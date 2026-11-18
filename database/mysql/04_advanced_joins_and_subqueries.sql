-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: Advanced Joins, Complex Subqueries, and Set Predicates
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

-- ============================================================================
-- PART 1: ADVANCED JOINS
-- ============================================================================

-- 1.1 INNER JOIN: Guests and their confirmed reservations
SELECT
    g.id AS guest_id,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_full_name,
    g.email,
    r.confirmation_number,
    r.check_in_date,
    r.check_out_date,
    GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate * x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount - r.discount_amount) AS total_amount,
    r.status
FROM guests g
INNER JOIN reservations r ON g.id = r.guest_id
WHERE r.status = 'confirmed'
ORDER BY r.check_in_date ASC;

-- 1.2 LEFT JOIN: All rooms and their reservation allocations (including unbooked rooms)
SELECT
    r.room_number,
    rt.name AS room_type_name,
    r.operational_status,
    res.confirmation_number,
    res.status AS reservation_status
FROM rooms r
INNER JOIN room_types rt ON r.room_type_id = rt.id
LEFT JOIN reservation_rooms rr ON r.id = rr.room_id
LEFT JOIN reservations res ON rr.reservation_id = res.id
ORDER BY r.room_number ASC;

-- 1.3 MULTI-TABLE JOIN: Comprehensive guest folio with allocated rooms and payment status
SELECT
    res.confirmation_number,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_name,
    rm.room_number,
    rt.name AS suite_type,
    res.check_in_date,
    res.check_out_date,
    DATEDIFF(res.check_out_date,res.check_in_date) AS total_nights,
    GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=res.id),0.00) + res.tax_amount - res.discount_amount) AS total_amount,
    COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=res.id AND x.payment_status IN ('paid','partially_refunded')),0.00) AS paid_amount,
    GREATEST(0.00, GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=res.id),0.00) + res.tax_amount - res.discount_amount) - COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=res.id AND x.payment_status IN ('paid','partially_refunded')),0.00)) AS outstanding_balance,
    p.payment_reference,
    p.amount AS payment_amount,
    p.payment_method
FROM reservations res
INNER JOIN guests g ON res.guest_id = g.id
INNER JOIN reservation_rooms rr ON res.id = rr.reservation_id
INNER JOIN rooms rm ON rr.room_id = rm.id
INNER JOIN room_types rt ON rm.room_type_id = rt.id
LEFT JOIN payments p ON res.id = p.reservation_id
ORDER BY res.check_in_date DESC;


-- ============================================================================
-- PART 2: ADVANCED SUBQUERIES
-- ============================================================================

-- 2.1 SCALAR SUBQUERY:
-- Retrieve reservations whose total billing exceeds the hotel-wide average reservation value
WITH reservation_totals AS (
    SELECT r.*, GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) AS total_amount
    FROM reservations r
)
SELECT confirmation_number, total_amount,
       (SELECT AVG(total_amount) FROM reservation_totals WHERE status != 'cancelled') AS overall_average_booking,
       ROUND(total_amount - (SELECT AVG(total_amount) FROM reservation_totals WHERE status != 'cancelled'), 2) AS variance_above_average
FROM reservation_totals
WHERE total_amount > (SELECT AVG(total_amount) FROM reservation_totals WHERE status != 'cancelled')
  AND status != 'cancelled'
ORDER BY total_amount DESC;

-- 2.2 NESTED SUBQUERY WITH 'IN':
-- Find all guests who have stayed in either 'Executive Suite' or 'Penthouse' room types
SELECT
    id,
    CONCAT(first_name, ' ', last_name) AS guest_name,
    email,
    phone
FROM guests
WHERE id IN (
    SELECT DISTINCT res.guest_id
    FROM reservations res
    JOIN reservation_rooms rr ON res.id = rr.reservation_id
    JOIN rooms r ON rr.room_id = r.id
    JOIN room_types rt ON r.room_type_id = rt.id
    WHERE rt.code IN ('STE', 'PRE')
);

-- 2.3 CORRELATED SUBQUERY:
-- For each room, calculate the total count of active bookings allocated to it
SELECT
    r.room_number,
    rt.name AS room_type,
    r.capacity,
    (
        SELECT COUNT(*)
        FROM reservation_rooms rr
        JOIN reservations res ON rr.reservation_id = res.id
        WHERE rr.room_id = r.id
          AND res.status IN ('confirmed', 'checked_in')
    ) AS active_booking_count
FROM rooms r
JOIN room_types rt ON r.room_type_id = rt.id
ORDER BY active_booking_count DESC, r.room_number ASC;

-- 2.4 'EXISTS' PREDICATE:
-- Identify guests who have at least one successfully completed (checked_out) historical stay
SELECT
    g.id,
    CONCAT(g.first_name, ' ', g.last_name) AS repeat_guest_name,
    g.email
FROM guests g
WHERE EXISTS (
    SELECT 1
    FROM reservations r
    WHERE r.guest_id = g.id
      AND r.status = 'checked_out'
);

-- 2.5 'NOT EXISTS' PREDICATE:
-- Strict availability query: Find operational rooms that have NO overlapping bookings
-- between target dates '2026-10-25' and '2026-10-28'
SELECT
    r.id AS room_id,
    r.room_number,
    rt.name AS suite_type,
    rt.base_price,
    r.capacity
FROM rooms r
JOIN room_types rt ON r.room_type_id = rt.id
WHERE r.operational_status = 'operational'
  AND r.is_active = TRUE
  AND NOT EXISTS (
      SELECT 1
      FROM reservation_rooms rr
      JOIN reservations res ON rr.reservation_id = res.id
      WHERE rr.room_id = r.id
        AND res.status IN ('confirmed', 'checked_in')
        AND res.check_in_date < '2026-10-28'
        AND res.check_out_date > '2026-10-25'
  )
ORDER BY r.room_number ASC;
