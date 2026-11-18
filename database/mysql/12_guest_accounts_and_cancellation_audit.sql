-- Additive, reversible schema migration for guest accounts and cancellation audit.
-- Target: hotelreservationdb only. This migration preserves existing rows.
-- Test only in a disposable schema first; do not run automatically on application startup.
USE hotelreservationdb;

ALTER TABLE guests
  ADD COLUMN state VARCHAR(100) NULL AFTER city,
  ADD COLUMN postal_code VARCHAR(20) NULL AFTER state,
  MODIFY COLUMN country VARCHAR(100) NULL DEFAULT 'India';

ALTER TABLE users
  ADD COLUMN guest_profile_id INT NULL,
  ADD UNIQUE KEY uq_users_guest_profile (guest_profile_id),
  ADD CONSTRAINT fk_users_guest_profile
    FOREIGN KEY (guest_profile_id) REFERENCES guests (id) ON DELETE SET NULL;

ALTER TABLE reservation_status_history
  ADD COLUMN request_source VARCHAR(20) NULL,
  ADD COLUMN requested_by_guest_id INT NULL,
  ADD COLUMN cancellation_fee DECIMAL(10, 2) NULL,
  ADD COLUMN refund_status VARCHAR(30) NULL,
  ADD INDEX idx_rsh_request_guest (requested_by_guest_id),
  ADD CONSTRAINT fk_rsh_request_guest
    FOREIGN KEY (requested_by_guest_id) REFERENCES guests (id) ON DELETE SET NULL;
