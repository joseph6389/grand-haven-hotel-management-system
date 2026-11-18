-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase III: Database Views for Operational Reporting
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

-- ----------------------------------------------------------------------------
-- VIEW 1: vw_reservation_details
-- Complete flattened perspective of reservations with guest, rooms, and balances
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_reservation_details AS
SELECT
    r.id AS reservation_id,
    r.confirmation_number,
    r.guest_id,
    CONCAT(g.first_name, ' ', g.last_name) AS guest_full_name,
    g.email AS guest_email,
    g.phone AS guest_phone,
    r.check_in_date,
    r.check_out_date,
    DATEDIFF(r.check_out_date, r.check_in_date) AS total_nights,
    r.adults_count,
    r.children_count,
    GROUP_CONCAT(rm.room_number ORDER BY rm.room_number SEPARATOR ', ') AS allocated_room_numbers,
    GROUP_CONCAT(DISTINCT rt.name ORDER BY rt.name SEPARATOR ', ') AS suite_types,
    COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) AS room_charges,
    r.tax_amount,
    r.discount_amount,
    GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) AS total_amount,
    COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=r.id AND x.payment_status IN ('paid','partially_refunded')),0.00) AS paid_amount,
    GREATEST(0.00, GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) - COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=r.id AND x.payment_status IN ('paid','partially_refunded')),0.00)) AS outstanding_balance,
    CASE
        WHEN COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=r.id AND x.payment_status IN ('paid','partially_refunded')),0.00) >= GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) AND GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) > 0 THEN 'Paid'
        WHEN COALESCE((SELECT SUM(x.amount-x.refunded_amount) FROM payments x WHERE x.reservation_id=r.id AND x.payment_status IN ('paid','partially_refunded')),0.00) > 0 THEN 'Partially Paid'
        ELSE 'Unpaid'
    END AS billing_status,
    r.status AS reservation_status,
    r.created_at AS booked_at
FROM reservations r
INNER JOIN guests g ON r.guest_id = g.id
LEFT JOIN reservation_rooms rr ON r.id = rr.reservation_id
LEFT JOIN rooms rm ON rr.room_id = rm.id
LEFT JOIN room_types rt ON rm.room_type_id = rt.id
GROUP BY
    r.id, r.confirmation_number, r.guest_id, g.first_name, g.last_name,
    g.email, g.phone, r.check_in_date, r.check_out_date,
    r.adults_count, r.children_count, r.tax_amount,
    r.discount_amount, r.status, r.created_at;

-- ----------------------------------------------------------------------------
-- VIEW 2: vw_room_availability
-- Real-time inventory status mapping physical rooms, operational status, and rates
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_room_availability AS
SELECT
    r.id AS room_id,
    r.room_number,
    r.floor,
    r.capacity,
    rt.code AS room_type_code,
    rt.name AS room_type_name,
    rt.base_price AS nightly_rate,
    rt.bed_type,
    r.operational_status,
    r.is_active,
    CASE
        WHEN r.is_active = FALSE THEN 'Deactivated'
        WHEN r.operational_status != 'operational' THEN CONCAT('Blocked: ', r.operational_status)
        ELSE 'Available'
    END AS general_availability_state
FROM rooms r
INNER JOIN room_types rt ON r.room_type_id = rt.id;

-- ----------------------------------------------------------------------------
-- VIEW 3: vw_monthly_revenue
-- Monthly historical breakdown of gross revenue collected via completed payments
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    YEAR(p.created_at) AS revenue_year,
    MONTH(p.created_at) AS revenue_month,
    DATE_FORMAT(p.created_at, '%b %Y') AS month_label,
    COUNT(p.id) AS total_transactions,
    SUM(CASE WHEN p.payment_status = 'paid' THEN p.amount ELSE 0.00 END) AS gross_revenue_collected,
    SUM(CASE WHEN p.payment_status = 'refunded' THEN p.amount ELSE 0.00 END) AS total_refunded_amount,
    SUM(CASE WHEN p.payment_status = 'paid' THEN p.amount ELSE -p.amount END) AS net_revenue_collected
FROM payments p
GROUP BY YEAR(p.created_at), MONTH(p.created_at), DATE_FORMAT(p.created_at, '%b %Y')
ORDER BY revenue_year DESC, revenue_month DESC;

-- ----------------------------------------------------------------------------
-- VIEW 4: vw_guest_booking_history
-- Aggregated CRM summary calculating lifetime loyalty value per guest
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_guest_booking_history AS
SELECT
    g.id AS guest_id,
    CONCAT(g.first_name, ' ', g.last_name) AS full_name,
    g.email,
    g.phone,
    g.country,
    COUNT(r.id) AS lifetime_reservations_count,
    SUM(CASE WHEN r.status != 'cancelled' THEN GREATEST(0.00, COALESCE((SELECT SUM(x.nightly_rate*x.nights) FROM reservation_rooms x WHERE x.reservation_id=r.id),0.00) + r.tax_amount-r.discount_amount) ELSE 0.00 END) AS lifetime_spend_value,
    MAX(r.check_in_date) AS most_recent_stay_date,
    SUM(CASE WHEN r.status = 'cancelled' THEN 1 ELSE 0 END) AS total_cancellations
FROM guests g
LEFT JOIN reservations r ON g.id = r.guest_id
GROUP BY g.id, g.first_name, g.last_name, g.email, g.phone, g.country;

-- ----------------------------------------------------------------------------
-- VIEW 5: vw_occupancy_summary
-- Executive KPI summary comparing total capacity against currently occupied rooms
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_occupancy_summary AS
SELECT
    CURRENT_DATE() AS report_date,
    (SELECT COUNT(*) FROM rooms WHERE is_active = TRUE) AS total_active_rooms,
    (SELECT COUNT(*) FROM rooms WHERE is_active = TRUE AND operational_status = 'operational') AS operational_rooms,
    (SELECT COUNT(*) FROM rooms WHERE operational_status IN ('maintenance', 'out_of_order')) AS maintenance_rooms,
    (
        SELECT COUNT(DISTINCT rr.room_id)
        FROM reservation_rooms rr
        JOIN reservations res ON rr.reservation_id = res.id
        WHERE res.status = 'checked_in'
          AND res.check_in_date <= CURRENT_DATE()
          AND res.check_out_date > CURRENT_DATE()
    ) AS currently_occupied_rooms,
    ROUND(
        (
            (
                SELECT COUNT(DISTINCT rr.room_id)
                FROM reservation_rooms rr
                JOIN reservations res ON rr.reservation_id = res.id
                WHERE res.status = 'checked_in'
                  AND res.check_in_date <= CURRENT_DATE()
                  AND res.check_out_date > CURRENT_DATE()
            ) /
            NULLIF((SELECT COUNT(*) FROM rooms WHERE is_active = TRUE AND operational_status = 'operational'), 0)
        ) * 100,
        1
    ) AS current_occupancy_rate_percentage;

-- Verification of views
SELECT * FROM vw_occupancy_summary;
SELECT * FROM vw_monthly_revenue LIMIT 5;
