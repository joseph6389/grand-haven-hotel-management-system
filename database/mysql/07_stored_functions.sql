-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: MySQL Stored Functions for Mathematical and Business Computations
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

DELIMITER $$

-- ----------------------------------------------------------------------------
-- FUNCTION 1: fn_calculate_nights
-- Deterministic calculation of nights between two dates with validation
-- ----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calculate_nights$$

CREATE FUNCTION fn_calculate_nights(
    p_check_in DATE,
    p_check_out DATE
)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_nights INT;

    IF p_check_out <= p_check_in THEN
        RETURN 0;
    END IF;

    SET v_nights = DATEDIFF(p_check_out, p_check_in);
    RETURN v_nights;
END$$


-- ----------------------------------------------------------------------------
-- FUNCTION 2: fn_calculate_outstanding_balance
-- Retrieves current remaining debt on any given reservation record
-- ----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calculate_outstanding_balance$$

CREATE FUNCTION fn_calculate_outstanding_balance(
    p_reservation_id INT
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_paid DECIMAL(10, 2) DEFAULT 0.00;
    DECLARE v_balance DECIMAL(10, 2) DEFAULT 0.00;

    SELECT GREATEST(0.00, COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount),
           COALESCE((SELECT SUM(p.amount-p.refunded_amount) FROM payments p WHERE p.reservation_id=r.id AND p.payment_status IN ('paid','partially_refunded')),0.00)
    INTO v_total, v_paid
    FROM reservations r
    WHERE r.id = p_reservation_id;

    IF v_total IS NULL THEN
        RETURN 0.00;
    END IF;

    SET v_balance = v_total - v_paid;
    IF v_balance < 0.00 THEN
        SET v_balance = 0.00;
    END IF;

    RETURN v_balance;
END$$


-- ----------------------------------------------------------------------------
-- FUNCTION 3: fn_calculate_tax
-- Standardized lodging tax calculation with banker's rounding
-- ----------------------------------------------------------------------------
DROP FUNCTION IF EXISTS fn_calculate_tax$$

CREATE FUNCTION fn_calculate_tax(
    p_amount DECIMAL(10, 2),
    p_rate DECIMAL(5, 4)
)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
NO SQL
BEGIN
    DECLARE v_tax DECIMAL(10, 2);
    IF p_amount <= 0.00 OR p_rate <= 0.0000 THEN
        RETURN 0.00;
    END IF;
    SET v_tax = ROUND(p_amount * p_rate, 2);
    RETURN v_tax;
END$$

DELIMITER ;

-- Verification of Functions:
SELECT
    id,
    confirmation_number,
    check_in_date,
    check_out_date,
    fn_calculate_nights(check_in_date, check_out_date) AS computed_nights,
    GREATEST(0.00, COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) AS total_amount,
    COALESCE((SELECT SUM(p.amount-p.refunded_amount) FROM payments p WHERE p.reservation_id=r.id AND p.payment_status IN ('paid','partially_refunded')),0.00) AS paid_amount,
    fn_calculate_outstanding_balance(id) AS computed_balance
FROM reservations r;
