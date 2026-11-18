# Guest accounts, hotel roles, cancellation, and India settings

## Roles

- **Guest:** registers and signs in through `/register` and `/login`; manages their own guest profile, reservation history, booking details, and account password. Reservation and payment queries are scoped to the linked guest profile. Existing unlinked stay records are not claimed based only on matching an email or phone number; the guest is directed to reception because the project has no contact-verification provider.
- **Receptionist:** signs in through `/login`; uses the existing front-desk dashboard, guest/room/reservation/payment screens, arrivals/departures, check-in/out, and permitted payment/refund functions. Staff routes check the role on the server.
- **Admin:** signs in through `/login`; retains staff management, hotel settings, audit trail, reports, inventory and reservation management, and the Admin dashboard. Guest roles are excluded from staff account management.

Passwords are stored using Werkzeug password hashes. Guest password changes require the current password and a 10-character minimum. Logout is POST-only and CSRF-protected. Normal operations require a configured MySQL URL; tests explicitly use the isolated in-memory SQLite configuration.

## Reservation cancellation

### Guest self-service

The guest opens their own reservation detail page and confirms a POST cancellation. The server checks the linked guest ownership and valid reservation state, then calls the shared `cancel_reservation` service. A row lock protects the transition on MySQL. Duplicate or invalid status transitions are rejected. The same page shows the current cancellation/refund status.

### Reception phone request

The receptionist opens the correct reservation and records the guest's reason. The server requires the confirmation number, guest's exact stored full name, email, and normalized Indian mobile to match. The audit history records `request_source=phone`, the verified guest requester, the acting staff account, reason, prior/resulting status, and refund state. Knowing the confirmation number alone is insufficient.

Both methods use the same locked service. Cancellation is permitted before the configured local check-in boundary. At exactly 48 hours before check-in or less, the service records a ₹500 fee capped at the reservation amount recorded as paid; more than 48 hours before check-in adds no fee. The check-in boundary uses the configured hotel check-in time (15:00 by default) in `Asia/Kolkata`. The service records the fee and the amount potentially available for review in the audit log, without reducing the paid ledger or initiating a payout. Reservations with a remaining potential refund stay `pending_review`; if the fee consumes the full recorded paid balance, refund status is `not_applicable`. Outside the fee window, eligibility follows the configured hotel policy and remains subject to staff review. Staff refund actions update the hotel ledger and mark the cancellation review `recorded`; this system has no payment-provider integration and cannot verify an external payout.

Guest-facing confirmation is shown in the browser/account. Email/SMS delivery and OTP identity checks are not implemented because no messaging provider is configured.

## Operational activity updates

The staff dashboard polls a server endpoint every ten seconds for new committed audit records. Admins receive the admin-only feed; Admins and Receptionists receive the operational staff feed. The response contains a numeric event ID, generic action label, and India-local timestamp, not guest names, email addresses, payment amounts, or audit details. Browser rendering uses text nodes. This is authenticated polling, not WebSocket push; the database remains authoritative.

## India-localized behavior

- Billing currency is fixed to INR (`₹`) in configuration and settings. Tax remains configurable and defaults to the existing project value; this is not a statement of GST/legal compliance.
- Hotel business dates use `Asia/Kolkata`. Naive values in existing MySQL `DATETIME` columns continue to represent UTC, and display/CSV timestamps convert to IST. Date-only UI and exported stay dates use day-first `DD/MM/YYYY` format.
- Guest mobile fields normalize ten-digit Indian mobile numbers to `+91` and reject non-Indian formats. The hotel phone and address defaults remain blank until the operator supplies verified details. `HOTEL_ADDRESS` and `HOTEL_TIMEZONE` are documented placeholders/configuration, not claims of an actual hotel address.
- Check-in/out hours and cancellation wording remain operator-configurable. The UI keeps specific cancellation/refund status, payment, check-in/out, and arrival ID notices while omitting generic terms-and-conditions boilerplate.

## Setup and schema notes

1. Use Python 3.13 and the pinned `requirements.txt` in a project virtual environment. Do not install the packages globally.
2. Create a new, empty MySQL 8.0 database for a fresh install. Run `database/mysql/01_Create_Database_Tables.sql` followed by `database/mysql/02_Insert_Sample_Data.sql` only in that new database. Scripts 03–11 are coursework demonstrations/queries; script 03 performs UPDATE, INSERT, and DELETE and must never be run against the active hotel database.
3. Put local settings in an untracked `.env`, using `.env.example` as a template. Use a dedicated least-privilege application DB account for ordinary runtime DML; use a separate controlled migration account for schema setup. Do not run Flask as MySQL `root`.
4. The fresh canonical DDL in script 01 already includes the guest/cancellation fields. Existing installations created before these features require review of their own schema and a verified backup before applying `12_guest_accounts_and_cancellation_audit.sql`; its rollback counterpart is `12_guest_accounts_and_cancellation_audit_rollback.sql`. The migration was exercised only in a disposable schema. The current `hotelreservationdb` schema was observed missing these columns and was not changed. Do not run script 12 there until separately approved.
5. Start with `python run.py`. Run the test suite with `python -m pytest -q -p no:cacheprovider`; tests use isolated in-memory SQLite and do not test MySQL row-lock concurrency.

## Known limits and operator decisions

- Current active MySQL metadata (read-only, 27 October 2026): `hotelreservationdb`, MySQL 8.0.46, 23 tables, no visible views/triggers/procedures/functions. Eight legacy tables contain existing rows and have foreign-key links to their own singular table family; they are retained and are not presumed duplicates.
- The connection account observed through read-only `SHOW GRANTS` is `root@localhost` with broad global privileges. This is inappropriate for routine application use. Create/configure a dedicated low-privilege runtime account outside the app and protect its password; no account or credential was changed in this audit.
- The active schema needs the additive migration for the current ORM/account features. That live migration is pending explicit review/approval. No active data or schema changes have been made.
- No verified backup-and-restore, browser manual test, live write workflow, concurrent MySQL test, email delivery, deployment test, or dependency vulnerability scan has been completed in this audit.
- No college synopsis/rubric was available; these documents do not claim rubric compliance or legal/tax compliance.
