-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase IV: Comprehensive Database Integrity Validator
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

-- ============================================================================
-- AUDIT 1: CONFLICTING / OVERLAPPING ROOM ALLOCATIONS (DOUBLE BOOKINGS)
-- Checks whether any room has two active reservations overlapping in stay dates
-- ============================================================================
SELECT
    'CONFLICTING_ROOM_ALLOCATIONS' AS audit_rule,
    rr1.room_id,
    rm.room_number,
    r1.confirmation_number AS reservation_1,
    r1.check_in_date AS r1_checkin,
    r1.check_out_date AS r1_checkout,
    r1.status AS r1_status,
    r2.confirmation_number AS reservation_2,
    r2.check_in_date AS r2_checkin,
    r2.check_out_date AS r2_checkout,
    r2.status AS r2_status
FROM reservation_rooms rr1
JOIN reservation_rooms rr2 ON rr1.room_id = rr2.room_id AND rr1.reservation_id < rr2.reservation_id
JOIN reservations r1 ON rr1.reservation_id = r1.id
JOIN reservations r2 ON rr2.reservation_id = r2.id
JOIN rooms rm ON rr1.room_id = rm.id
WHERE r1.status IN ('confirmed', 'checked_in')
  AND r2.status IN ('confirmed', 'checked_in')
  AND r1.check_in_date < r2.check_out_date
  AND r1.check_out_date > r2.check_in_date;


-- ============================================================================
-- AUDIT 2: INVALID DATE RANGES
-- Check if check_out_date is not strictly after check_in_date
-- ============================================================================
SELECT
    'INVALID_DATE_RANGES' AS audit_rule,
    id,
    confirmation_number,
    check_in_date,
    check_out_date
FROM reservations
WHERE check_out_date <= check_in_date;


-- ============================================================================
-- AUDIT 3: INVALID ROOM ALLOCATION INPUTS
-- Line subtotals and reservation totals are computed from retained snapshots.
-- ============================================================================
SELECT
    'INVALID_ROOM_ALLOCATION_INPUT' AS audit_rule,
    id, reservation_id, room_id, nightly_rate, nights
FROM reservation_rooms
WHERE nightly_rate < 0 OR nights <= 0;


-- ============================================================================
-- AUDIT 4: PAYMENT LEDGER INPUTS
-- Reservation paid amounts are computed from this ledger; there is no copied total.
-- ============================================================================
SELECT
    'INVALID_PAYMENT_REFUND' AS audit_rule,
    id, reservation_id, amount, refunded_amount, payment_status
FROM payments
WHERE amount <= 0 OR refunded_amount < 0 OR refunded_amount > amount;


-- ============================================================================
-- AUDIT 5: RESERVATIONS WITH UNKNOWN OR ORPHANED GUESTS
-- ============================================================================
SELECT
    'ORPHANED_RESERVATIONS' AS audit_rule,
    r.id,
    r.confirmation_number,
    r.guest_id
FROM reservations r
LEFT JOIN guests g ON r.guest_id = g.id
WHERE g.id IS NULL;


-- ============================================================================
-- AUDIT 6: OVERBOOKED ROOM CAPACITIES
-- Detects if guests allocated exceed room maximum capacity
-- ============================================================================
SELECT
    'OVER_CAPACITY_ALLOCATIONS' AS audit_rule,
    res.confirmation_number,
    (res.adults_count + res.children_count) AS requested_guests,
    SUM(rm.capacity) AS total_allocated_capacity
FROM reservations res
JOIN reservation_rooms rr ON res.id = rr.reservation_id
JOIN rooms rm ON rr.room_id = rm.id
WHERE res.status != 'cancelled'
GROUP BY res.id, res.confirmation_number, res.adults_count, res.children_count
HAVING (res.adults_count + res.children_count) > SUM(rm.capacity);


-- ============================================================================
-- SUMMARY AUDIT HEALTH CHECK
-- Computes each rule's actual violation count before reporting health.
-- ============================================================================
SELECT
    'DATABASE_INTEGRITY_SUMMARY' AS report,
    CURRENT_TIMESTAMP() AS audited_at,
    CASE WHEN SUM(violations) = 0 THEN 'PASSED' ELSE 'FAILED' END AS status,
    SUM(violations) AS total_violations
FROM (
    SELECT COUNT(*) AS violations
    FROM reservation_rooms rr1
    JOIN reservation_rooms rr2 ON rr1.room_id = rr2.room_id AND rr1.reservation_id < rr2.reservation_id
    JOIN reservations r1 ON rr1.reservation_id = r1.id
    JOIN reservations r2 ON rr2.reservation_id = r2.id
    WHERE r1.status IN ('confirmed', 'checked_in') AND r2.status IN ('confirmed', 'checked_in')
      AND r1.check_in_date < r2.check_out_date AND r1.check_out_date > r2.check_in_date
    UNION ALL
    SELECT COUNT(*) FROM reservations WHERE check_out_date <= check_in_date
    UNION ALL
    SELECT COUNT(*) FROM reservation_rooms WHERE nightly_rate < 0 OR nights <= 0
    UNION ALL
    SELECT COUNT(*) FROM payments WHERE amount <= 0 OR refunded_amount < 0 OR refunded_amount > amount
    UNION ALL
    SELECT COUNT(*) FROM reservations r LEFT JOIN guests g ON g.id = r.guest_id WHERE g.id IS NULL
    UNION ALL
    SELECT COUNT(*) FROM (
        SELECT res.id
        FROM reservations res JOIN reservation_rooms rr ON rr.reservation_id = res.id
        JOIN rooms rm ON rm.id = rr.room_id
        WHERE res.status != 'cancelled'
        GROUP BY res.id, res.adults_count, res.children_count
        HAVING res.adults_count + res.children_count > SUM(rm.capacity)
    ) over_capacity
) audit_rule_counts;
