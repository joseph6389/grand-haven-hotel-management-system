-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: MySQL Database Triggers for Automated Auditing and Integrity
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- TRIGGER 1: trg_validate_reservation_transition
-- Protects reservation lifecycle rules for writes that bypass Flask services.
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_reservation_status_audit$$
DROP TRIGGER IF EXISTS trg_validate_reservation_transition$$

CREATE TRIGGER trg_validate_reservation_transition
BEFORE UPDATE ON reservations
FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status AND NOT (
        (OLD.status = 'pending' AND NEW.status IN ('confirmed', 'cancelled')) OR
        (OLD.status = 'confirmed' AND NEW.status IN ('checked_in', 'cancelled')) OR
        (OLD.status = 'checked_in' AND NEW.status = 'checked_out')
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid reservation status transition.';
    END IF;
END$$


-- ----------------------------------------------------------------------------
-- TRIGGER 2: trg_prevent_double_booking
-- Database-level barrier preventing overlapping room allocations at the physical layer
-- ----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_double_booking$$

CREATE TRIGGER trg_prevent_double_booking
BEFORE INSERT ON reservation_rooms
FOR EACH ROW
BEGIN
    DECLARE v_new_check_in DATE;
    DECLARE v_new_check_out DATE;
    DECLARE v_conflicts INT;

    -- Retrieve check-in and check-out dates of the reservation being allocated
    SELECT check_in_date, check_out_date
    INTO v_new_check_in, v_new_check_out
    FROM reservations
    WHERE id = NEW.reservation_id;

    -- Query if any overlapping active reservation already claims this room
    SELECT COUNT(*)
    INTO v_conflicts
    FROM reservation_rooms rr
    JOIN reservations res ON rr.reservation_id = res.id
    WHERE rr.room_id = NEW.room_id
      AND res.status IN ('confirmed', 'checked_in')
      AND res.id != NEW.reservation_id
      AND res.check_in_date < v_new_check_out
      AND res.check_out_date > v_new_check_in;

    IF v_conflicts > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Integrity Violation: Room is already reserved for overlapping dates.';
    END IF;
END$$

DELIMITER ;
