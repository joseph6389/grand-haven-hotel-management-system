-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase II: Data Cleaning and Core DML Operations
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

-- ============================================================================
-- PART 1: DATA CLEANING & INTEGRITY PREPARATION
-- ============================================================================

-- 1.1 Duplicate Detection: Identify duplicate guest email addresses
SELECT
    LOWER(email) AS normalized_email,
    COUNT(*) AS occurrence_count
FROM guests
GROUP BY LOWER(email)
HAVING COUNT(*) > 1;

-- 1.2 NULL Handling & Data Normalization:
-- Replace NULL identification fields with standardized fallback text
SELECT
    id,
    first_name,
    last_name,
    email,
    COALESCE(identification_type, 'Not Provided') AS clean_id_type,
    IFNULL(identification_number, 'UNSPECIFIED') AS clean_id_number,
    COALESCE(address, 'Address on file unavailable') AS display_address
FROM guests;

-- 1.3 String Standardization: Trim accidental leading/trailing whitespace
UPDATE guests
SET
    first_name = TRIM(first_name),
    last_name = TRIM(last_name),
    email = LOWER(TRIM(email)),
    phone = TRIM(phone);

-- 1.4 Safe Status Correction: Ensure room statuses conform to allowed values
UPDATE rooms
SET operational_status = 'operational'
WHERE operational_status NOT IN ('operational', 'maintenance', 'out_of_order');

-- 1.5 Safe Test Data Insertion and Deletion:
-- Insert a temporary dummy record to demonstrate safe deletion
INSERT INTO guests (first_name, last_name, email, phone, address)
VALUES ('Test', 'Dummy', 'test.dummy@temporary.com', '+91 9876500099', 'Temporary test address');

-- Safely delete only the test record matching the specific test email
DELETE FROM guests
WHERE email = 'test.dummy@temporary.com'
  AND first_name = 'Test';

-- Verify test record is purged
SELECT COUNT(*) AS test_records_remaining
FROM guests
WHERE email = 'test.dummy@temporary.com';


-- ============================================================================
-- PART 2: BASIC DML & AGGREGATE SQL OPERATIONS
-- ============================================================================

-- 2.1 SELECT with WHERE and ORDER BY
-- Retrieve all operational rooms on Floor 2 or higher, sorted by price descending
SELECT
    r.room_number,
    rt.name AS suite_type,
    r.floor,
    r.capacity,
    rt.base_price
FROM rooms r
JOIN room_types rt ON r.room_type_id = rt.id
WHERE r.operational_status = 'operational'
  AND r.floor >= 2
ORDER BY rt.base_price DESC, r.room_number ASC;

-- 2.2 DISTINCT
-- List all distinct room capacity sizes available across the hotel
SELECT DISTINCT capacity
FROM rooms
ORDER BY capacity ASC;

-- 2.3 LIMIT
-- Retrieve the top 3 highest value reservations ever booked
SELECT
    r.confirmation_number,
    r.check_in_date,
    r.check_out_date,
    DATEDIFF(r.check_out_date, r.check_in_date) AS total_nights,
    GREATEST(0.00, COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) AS total_amount,
    r.status
FROM reservations r
ORDER BY total_amount DESC
LIMIT 3;

-- 2.4 AGGREGATE FUNCTIONS: COUNT, SUM, AVG, MIN, MAX
-- Calculate comprehensive lodging portfolio financial metrics
SELECT
    COUNT(*) AS total_reservations_booked,
    SUM(total_amount) AS total_gross_booking_value,
    AVG(total_amount) AS average_reservation_value,
    MIN(room_charges) AS minimum_room_charge,
    MAX(total_amount) AS maximum_reservation_value,
    AVG(total_nights) AS average_stay_nights
FROM (
  SELECT r.id,r.status,DATEDIFF(r.check_out_date,r.check_in_date) AS total_nights,
    COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00) AS room_charges,
    GREATEST(0.00,COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00)+r.tax_amount-r.discount_amount) AS total_amount
  FROM reservations r
) totals
WHERE status != 'cancelled';

-- 2.5 GROUP BY
-- Group revenue and count by reservation status
SELECT status, COUNT(*) AS count_reservations,
    SUM(GREATEST(0.00,COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00)+r.tax_amount-r.discount_amount)) AS aggregate_revenue,
    SUM(COALESCE((SELECT SUM(p.amount-p.refunded_amount) FROM payments p WHERE p.reservation_id=r.id AND p.payment_status IN ('paid','partially_refunded')),0.00)) AS aggregate_paid
FROM reservations r
GROUP BY status
ORDER BY aggregate_revenue DESC;

-- 2.6 GROUP BY with HAVING
-- Identify suite types that have generated more than ₹1,500 in total revenue
SELECT
    rt.code,
    rt.name,
    COUNT(rr.id) AS total_room_bookings,
    SUM(rr.nightly_rate * rr.nights) AS total_category_revenue
FROM room_types rt
JOIN rooms r ON rt.id = r.room_type_id
JOIN reservation_rooms rr ON r.id = rr.room_id
JOIN reservations res ON rr.reservation_id = res.id
WHERE res.status != 'cancelled'
GROUP BY rt.code, rt.name
HAVING SUM(rr.nightly_rate * rr.nights) > 1500.00
ORDER BY total_category_revenue DESC;
