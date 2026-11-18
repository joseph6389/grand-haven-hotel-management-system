-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: Query Execution Analysis, Index Optimization, and EXPLAIN
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

-- ============================================================================
-- 1. INDEX LOOKUP VS FULL TABLE SCAN COMPARISON
-- ============================================================================

-- Query 1A: Look up reservation using Unique B-Tree Index on 'confirmation_number'
-- Expected Type: 'const' (Optimal O(1) single-row index lookup)
EXPLAIN
SELECT *
FROM reservations
WHERE confirmation_number = 'GH-20261014-9B2D';

-- Explanation:
-- type = 'const': MySQL reads the row once using the unique index.
-- key = 'confirmation_number': The engine utilized the unique constraint index.
-- rows = 1: Exactly 1 row examined.


-- Query 1B: Search reservations using non-indexed text column 'special_requests'
-- Expected Type: 'ALL' (Full Table Scan O(N))
EXPLAIN
SELECT *
FROM reservations
WHERE special_requests LIKE '%feather%';

-- Explanation:
-- type = 'ALL': MySQL must examine every single record in the table.
-- possible_keys = NULL: No index exists to satisfy this wildcard text match.
-- rows = Total rows in reservations table. Demonstrates why primary search paths require indexes.


-- ============================================================================
-- 2. COMPOSITE DATE-RANGE INDEX ANALYSIS
-- ============================================================================

-- Query 2: Range scan on (check_in_date, check_out_date) for hotel arrivals
-- Expected Type: 'range' (B-Tree index range traversal)
EXPLAIN
SELECT
    r.confirmation_number,
    r.check_in_date,
    r.check_out_date,
    r.status
FROM reservations r
WHERE r.check_in_date BETWEEN '2026-10-01' AND '2026-10-31';

-- Explanation:
-- type = 'range': The B-tree index on check_in_date allows direct traversal of matching date bounds.
-- key = 'idx_res_dates': The composite date index is utilized effectively.


-- ============================================================================
-- 3. MULTI-TABLE JOIN PLAN ANALYSIS
-- ============================================================================

-- Query 3: Multi-table join across Guests, Reservations, Rooms, and Room Types
EXPLAIN
SELECT
    res.confirmation_number,
    g.last_name,
    g.email,
    rm.room_number,
    rt.name AS suite_type,
    GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=res.id),0.00)+res.tax_amount-res.discount_amount) AS total_amount
FROM reservations res
JOIN guests g ON res.guest_id = g.id
JOIN reservation_rooms rr ON res.id = rr.reservation_id
JOIN rooms rm ON rr.room_id = rm.id
JOIN room_types rt ON rm.room_type_id = rt.id
WHERE res.status = 'confirmed';

-- Execution Plan Analysis:
-- 1. Driving table selection: MySQL chooses the most restrictive table first (reservations filtered by status).
-- 2. Foreign Key index lookups: Links to guests, reservation_rooms, rooms, and room_types all evaluate as 'eq_ref'.
-- 3. 'eq_ref': One row is read from this table for each combination of rows from the previous tables. This is the best possible join type.


-- ============================================================================
-- 4. EXPLAIN ANALYZE (Actual Execution Engine Timings)
-- ============================================================================

-- Query 4: Detailed iterator execution profile in MySQL 8.0+
EXPLAIN ANALYZE
SELECT
    rt.name AS room_type,
    COUNT(rr.id) AS total_bookings,
    AVG(rr.nightly_rate * rr.nights) AS avg_revenue
FROM room_types rt
LEFT JOIN rooms r ON rt.id = r.room_type_id
LEFT JOIN reservation_rooms rr ON r.id = rr.room_id
GROUP BY rt.name;

-- Output Breakdown:
-- - Nested loop inner/outer joins
-- - Index scan on PK
-- - Actual time spent in milliseconds
-- - Actual rows produced vs estimated rows
