-- Grand Haven Hotel — rollback for 13_normalize_derived_reservation_values.sql
-- Restore the prior stored values from the retained source facts and ledgers.
-- PREVIEW/TEST ONLY until an exact live migration plan is approved.
USE hotelreservationdb;

ALTER TABLE reservations
  ADD COLUMN total_nights INT NULL,
  ADD COLUMN room_charges DECIMAL(10,2) NULL,
  ADD COLUMN total_amount DECIMAL(10,2) NULL,
  ADD COLUMN paid_amount DECIMAL(10,2) NULL;

UPDATE reservations r
SET r.total_nights = DATEDIFF(r.check_out_date, r.check_in_date),
    r.room_charges = COALESCE((
      SELECT SUM(rr.nightly_rate * rr.nights)
      FROM reservation_rooms rr WHERE rr.reservation_id = r.id
    ), 0.00),
    r.total_amount = GREATEST(0.00, r.room_charges + r.tax_amount - r.discount_amount),
    r.paid_amount = COALESCE((
      SELECT SUM(p.amount - p.refunded_amount)
      FROM payments p
      WHERE p.reservation_id = r.id
        AND p.payment_status IN ('paid', 'partially_refunded')
    ), 0.00);

ALTER TABLE reservation_rooms ADD COLUMN subtotal DECIMAL(10,2) NULL;
UPDATE reservation_rooms SET subtotal = nightly_rate * nights;
ALTER TABLE reservation_rooms MODIFY COLUMN subtotal DECIMAL(10,2) NOT NULL;

ALTER TABLE reservation_services ADD COLUMN total_price DECIMAL(10,2) NULL;
UPDATE reservation_services SET total_price = quantity * unit_price;
ALTER TABLE reservation_services MODIFY COLUMN total_price DECIMAL(10,2) NOT NULL;

ALTER TABLE reservations
  MODIFY COLUMN total_nights INT NOT NULL DEFAULT 1,
  MODIFY COLUMN room_charges DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  MODIFY COLUMN total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  MODIFY COLUMN paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  ADD CONSTRAINT chk_res_nights CHECK (total_nights > 0),
  ADD CONSTRAINT chk_res_charges CHECK (room_charges >= 0.00),
  ADD CONSTRAINT chk_res_total CHECK (total_amount >= 0.00);
