-- Rollback for 12_guest_accounts_and_cancellation_audit.sql.
-- This drops only the additive linkage/audit columns. It does not delete guest,
-- user, reservation, or payment rows. Back up and test in a disposable schema.
USE hotelreservationdb;

ALTER TABLE reservation_status_history
  DROP FOREIGN KEY fk_rsh_request_guest,
  DROP INDEX idx_rsh_request_guest,
  DROP COLUMN refund_status,
  DROP COLUMN cancellation_fee,
  DROP COLUMN requested_by_guest_id,
  DROP COLUMN request_source;

ALTER TABLE users
  DROP FOREIGN KEY fk_users_guest_profile,
  DROP INDEX uq_users_guest_profile,
  DROP COLUMN guest_profile_id;

ALTER TABLE guests
  DROP COLUMN postal_code,
  DROP COLUMN state,
  MODIFY COLUMN country VARCHAR(100) NULL DEFAULT NULL;
