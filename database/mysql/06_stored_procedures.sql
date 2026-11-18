-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: MySQL Stored Procedures with Transactions & Concurrency Handling
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- PROCEDURE 1: sp_create_reservation
-- Atomic reservation creation with concurrency check, server pricing, and rollback
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_create_reservation$$

CREATE PROCEDURE sp_create_reservation(
    IN p_guest_id INT,
    IN p_room_id INT,
    IN p_check_in DATE,
    IN p_check_out DATE,
    IN p_adults INT,
    IN p_children INT,
    IN p_special_requests TEXT,
    IN p_user_id INT,
    OUT p_confirmation_no VARCHAR(32),
    OUT p_res_id INT,
    OUT p_status_code INT,
    OUT p_status_msg VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_nights INT;
    DECLARE v_nightly_rate DECIMAL(10, 2);
    DECLARE v_room_charges DECIMAL(10, 2);
    DECLARE v_tax_amount DECIMAL(10, 2);
    DECLARE v_total_amount DECIMAL(10, 2);
    DECLARE v_room_status VARCHAR(20);
    DECLARE v_room_capacity INT;
    DECLARE v_conflict_count INT;
    DECLARE v_locked_room_id INT;
    DECLARE v_tax_rate DECIMAL(5, 4) DEFAULT 0.1200; -- 12% Lodging Tax

    -- Declare SQLEXCEPTION handler for automatic transaction rollback
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status_code = 500;
        SET p_status_msg = 'Database transaction failed during reservation creation. Changes rolled back.';
    END;

    -- Step 1: Input Validation
    IF p_check_out <= p_check_in THEN
        SET p_status_code = 400;
        SET p_status_msg = 'Check-out date must be strictly after check-in date.';
        LEAVE proc_block;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM guests WHERE id = p_guest_id) THEN
        SET p_status_code = 404;
        SET p_status_msg = 'Guest profile not found.';
        LEAVE proc_block;
    END IF;

    -- Step 2: Room Inspection (Capacity, Operational Status, Base Price)
    SELECT r.operational_status, r.capacity, rt.base_price
    INTO v_room_status, v_room_capacity, v_nightly_rate
    FROM rooms r
    JOIN room_types rt ON r.room_type_id = rt.id
    WHERE r.id = p_room_id AND r.is_active = TRUE;

    IF v_room_status IS NULL THEN
        SET p_status_code = 404;
        SET p_status_msg = 'Room does not exist or is inactive.';
        LEAVE proc_block;
    END IF;

    IF v_room_status != 'operational' THEN
        SET p_status_code = 409;
        SET p_status_msg = CONCAT('Room is currently blocked for ', v_room_status);
        LEAVE proc_block;
    END IF;

    IF (p_adults + p_children) > v_room_capacity THEN
        SET p_status_code = 400;
        SET p_status_msg = CONCAT('Occupancy exceeds room capacity of ', v_room_capacity);
        LEAVE proc_block;
    END IF;

    -- Step 3: Atomic Transaction Block
    START TRANSACTION;

    -- Serialize competing bookings for the same physical room, including when
    -- the room has no reservation rows yet (the empty-range case).
    SELECT id INTO v_locked_room_id
    FROM rooms
    WHERE id = p_room_id AND is_active = TRUE AND operational_status = 'operational'
    FOR UPDATE;

    IF v_locked_room_id IS NULL THEN
        ROLLBACK;
        SET p_status_code = 409;
        SET p_status_msg = 'Room is no longer operational or active.';
        LEAVE proc_block;
    END IF;

    -- Concurrency re-check: Check if an overlapping active reservation exists
    SELECT COUNT(*)
    INTO v_conflict_count
    FROM reservation_rooms rr
    JOIN reservations res ON rr.reservation_id = res.id
    WHERE rr.room_id = p_room_id
      AND res.status IN ('confirmed', 'checked_in')
      AND res.check_in_date < p_check_out
      AND res.check_out_date > p_check_in
    FOR UPDATE; -- Row-level locking to prevent race conditions

    IF v_conflict_count > 0 THEN
        ROLLBACK;
        SET p_status_code = 409;
        SET p_status_msg = 'Room was just booked by another concurrent transaction for these dates.';
        LEAVE proc_block;
    END IF;

    -- Calculate Nights and Financials
    SET v_nights = DATEDIFF(p_check_out, p_check_in);
    SET v_room_charges = v_nightly_rate * v_nights;
    SET v_tax_amount = ROUND(v_room_charges * v_tax_rate, 2);
    SET v_total_amount = v_room_charges + v_tax_amount;

    -- Generate Confirmation Number (GH-YYYYMMDD-XXXX)
    SET p_confirmation_no = CONCAT('GH-', DATE_FORMAT(CURRENT_DATE(), '%Y%m%d'), '-', UPPER(SUBSTRING(MD5(RAND()), 1, 4)));

    -- Insert Master Reservation
    INSERT INTO reservations (
        confirmation_number, guest_id, check_in_date, check_out_date,
        adults_count, children_count, tax_amount, discount_amount,
        status, special_requests, created_by_id
    ) VALUES (
        p_confirmation_no, p_guest_id, p_check_in, p_check_out,
        p_adults, p_children, v_tax_amount, 0.00,
        'confirmed', p_special_requests, p_user_id
    );

    SET p_res_id = LAST_INSERT_ID();

    -- Insert Room Allocation
    INSERT INTO reservation_rooms (
        reservation_id, room_id, nightly_rate, nights
    ) VALUES (
        p_res_id, p_room_id, v_nightly_rate, v_nights
    );

    -- Insert Status Progression History
    INSERT INTO reservation_status_history (
        reservation_id, previous_status, new_status, changed_by_id, reason
    ) VALUES (
        p_res_id, NULL, 'confirmed', p_user_id, 'Stored procedure reservation creation'
    );

    COMMIT;

    SET p_status_code = 201;
    SET p_status_msg = 'Reservation created and confirmed successfully.';

END proc_block$$


-- ----------------------------------------------------------------------------
-- PROCEDURE 2: sp_cancel_reservation
-- Releasing allocated inventory safely with audit tracking
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cancel_reservation$$

CREATE PROCEDURE sp_cancel_reservation(
    IN p_reservation_id INT,
    IN p_user_id INT,
    IN p_reason VARCHAR(255),
    OUT p_status_code INT,
    OUT p_status_msg VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_current_status VARCHAR(20);

    SELECT status INTO v_current_status
    FROM reservations
    WHERE id = p_reservation_id;

    IF v_current_status IS NULL THEN
        SET p_status_code = 404;
        SET p_status_msg = 'Reservation not found.';
        LEAVE proc_block;
    END IF;

    IF v_current_status NOT IN ('pending', 'confirmed') THEN
        SET p_status_code = 400;
        SET p_status_msg = CONCAT('Cannot cancel reservation in status: ', v_current_status);
        LEAVE proc_block;
    END IF;

    START TRANSACTION;

    UPDATE reservations
    SET status = 'cancelled', updated_at = NOW()
    WHERE id = p_reservation_id;

    INSERT INTO reservation_status_history (
        reservation_id, previous_status, new_status, changed_by_id, reason
    ) VALUES (
        p_reservation_id, v_current_status, 'cancelled', p_user_id, p_reason
    );

    COMMIT;

    SET p_status_code = 200;
    SET p_status_msg = 'Reservation successfully cancelled. Rooms released back to inventory.';
END proc_block$$


-- ----------------------------------------------------------------------------
-- PROCEDURE 3: sp_check_in_guest
-- Front desk guest check-in procedure
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_check_in_guest$$

CREATE PROCEDURE sp_check_in_guest(
    IN p_reservation_id INT,
    IN p_user_id INT,
    OUT p_status_code INT,
    OUT p_status_msg VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_current_status VARCHAR(20);

    SELECT status INTO v_current_status
    FROM reservations
    WHERE id = p_reservation_id;

    IF v_current_status IS NULL THEN
        SET p_status_code = 404;
        SET p_status_msg = 'Reservation not found.';
        LEAVE proc_block;
    END IF;

    IF v_current_status NOT IN ('confirmed', 'pending') THEN
        SET p_status_code = 400;
        SET p_status_msg = CONCAT('Cannot check in reservation in status: ', v_current_status);
        LEAVE proc_block;
    END IF;

    START TRANSACTION;

    UPDATE reservations
    SET status = 'checked_in', updated_at = NOW()
    WHERE id = p_reservation_id;

    INSERT INTO reservation_status_history (
        reservation_id, previous_status, new_status, changed_by_id, reason
    ) VALUES (
        p_reservation_id, v_current_status, 'checked_in', p_user_id, 'Front desk arrival check-in'
    );

    COMMIT;

    SET p_status_code = 200;
    SET p_status_msg = 'Guest checked in successfully.';
END proc_block$$


-- ----------------------------------------------------------------------------
-- PROCEDURE 4: sp_check_out_guest
-- Front desk departure and key return
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_check_out_guest$$

CREATE PROCEDURE sp_check_out_guest(
    IN p_reservation_id INT,
    IN p_user_id INT,
    OUT p_status_code INT,
    OUT p_status_msg VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_current_status VARCHAR(20);
    DECLARE v_balance DECIMAL(10, 2);

    SELECT r.status,
      GREATEST(0.00, GREATEST(0.00, COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount)
      - COALESCE((SELECT SUM(p.amount-p.refunded_amount) FROM payments p WHERE p.reservation_id=r.id AND p.payment_status IN ('paid','partially_refunded')),0.00))
    INTO v_current_status, v_balance
    FROM reservations r
    WHERE r.id = p_reservation_id;

    IF v_current_status IS NULL THEN
        SET p_status_code = 404;
        SET p_status_msg = 'Reservation not found.';
        LEAVE proc_block;
    END IF;

    IF v_current_status != 'checked_in' THEN
        SET p_status_code = 400;
        SET p_status_msg = 'Only currently checked-in reservations can be checked out.';
        LEAVE proc_block;
    END IF;

    START TRANSACTION;

    UPDATE reservations
    SET status = 'checked_out', updated_at = NOW()
    WHERE id = p_reservation_id;

    INSERT INTO reservation_status_history (
        reservation_id, previous_status, new_status, changed_by_id, reason
    ) VALUES (
        p_reservation_id, v_current_status, 'checked_out', p_user_id, 'Front desk departure check-out'
    );

    COMMIT;

    SET p_status_code = 200;
    IF v_balance > 0.00 THEN
        SET p_status_msg = CONCAT('Guest checked out. Notice: Unsettled folio balance of ₹', v_balance);
    ELSE
        SET p_status_msg = 'Guest checked out successfully with zero outstanding balance.';
    END IF;
END proc_block$$


-- ----------------------------------------------------------------------------
-- PROCEDURE 5: sp_get_available_rooms
-- Real-time date-overlap inventory search procedure
-- ----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_get_available_rooms$$

CREATE PROCEDURE sp_get_available_rooms(
    IN p_check_in DATE,
    IN p_check_out DATE,
    IN p_room_type_id INT,
    IN p_min_capacity INT
)
BEGIN
    SELECT
        r.id AS room_id,
        r.room_number,
        r.floor,
        r.capacity,
        rt.id AS room_type_id,
        rt.code AS room_type_code,
        rt.name AS room_type_name,
        rt.base_price AS nightly_rate,
        rt.bed_type,
        DATEDIFF(p_check_out, p_check_in) AS nights_requested,
        ROUND(rt.base_price * DATEDIFF(p_check_out, p_check_in), 2) AS estimated_room_charges
    FROM rooms r
    JOIN room_types rt ON r.room_type_id = rt.id
    WHERE r.is_active = TRUE
      AND r.operational_status = 'operational'
      AND (p_room_type_id IS NULL OR r.room_type_id = p_room_type_id)
      AND (p_min_capacity IS NULL OR r.capacity >= p_min_capacity)
      AND NOT EXISTS (
          SELECT 1
          FROM reservation_rooms rr
          JOIN reservations res ON rr.reservation_id = res.id
          WHERE rr.room_id = r.id
            AND res.status IN ('confirmed', 'checked_in')
            AND res.check_in_date < p_check_out
            AND res.check_out_date > p_check_in
      )
    ORDER BY r.floor ASC, r.room_number ASC;
END$$

DELIMITER ;
