-- Grand Haven Hotel — 3NF normalization migration
-- PREVIEW/TEST ONLY until an exact live migration plan is approved.
-- Run preflight first and proceed only when every returned count is zero.
USE hotelreservationdb;

SELECT COUNT(*) AS reservation_derived_value_mismatches
FROM reservations r
WHERE r.total_nights <> DATEDIFF(r.check_out_date, r.check_in_date)
   OR r.room_charges <> COALESCE((
       SELECT SUM(rr.nightly_rate * rr.nights)
       FROM reservation_rooms rr WHERE rr.reservation_id = r.id
   ), 0.00)
   OR r.total_amount <> GREATEST(0.00, r.room_charges + r.tax_amount - r.discount_amount)
   OR r.paid_amount <> COALESCE((
       SELECT SUM(p.amount - p.refunded_amount)
       FROM payments p
       WHERE p.reservation_id = r.id
         AND p.payment_status IN ('paid', 'partially_refunded')
   ), 0.00);

SELECT COUNT(*) AS reservation_room_subtotal_mismatches
FROM reservation_rooms WHERE subtotal <> nightly_rate * nights;

SELECT COUNT(*) AS reservation_service_total_mismatches
FROM reservation_services WHERE total_price <> quantity * unit_price;

-- Preserve transaction inputs and historical snapshots. Derived values remain
-- available through SQLAlchemy hybrid properties and are calculated on demand.
ALTER TABLE reservations
  DROP CHECK chk_res_nights,
  DROP CHECK chk_res_charges,
  DROP CHECK chk_res_total,
  DROP COLUMN total_nights,
  DROP COLUMN room_charges,
  DROP COLUMN total_amount,
  DROP COLUMN paid_amount;

ALTER TABLE reservation_rooms DROP COLUMN subtotal;
ALTER TABLE reservation_services DROP COLUMN total_price;
