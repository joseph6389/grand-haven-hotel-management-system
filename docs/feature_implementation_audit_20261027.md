# Feature implementation audit — 2026-10-27

## Workspace and evidence

- Working target: `C:\Users\josep\Downloads\GrandHavenHotel_submission_20261025_final`, the extracted submission requested for implementation.
- Protected original: `C:\Users\josep\Downloads\GrandHavenHotel_fixed`; it was not edited. The target has no `.git` directory, so Git status/diff is not available there. The original's existing staged and unstaged work was not changed.
- The 25 October submission ZIP remains unchanged and served as a read-only source checkpoint. The extracted `.env` was not read, copied into deliverables, or included in output.
- Runtime used Python 3.13.5 and the already-installed project dependencies. No global package install or dependency update was run.
- Baseline before edits: `python -m pytest -q -p no:cacheprovider` — 29 passed in 8.38 s.
- Final working-tree regression suite: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -q -p no:cacheprovider` — **46 passed in 37.71 s**, zero failures. `python -m pip check` reported no broken requirements. Tests use the isolated in-memory SQLite configuration, not MySQL application writes.
- The final submission ZIP extracted to a separate temporary directory and its suite passed: **46 passed**. ZIP CRC validation passed; it contains 117 entries and no `.env`, cache/bytecode, local database, backup, or nested archive entries.
- A temporary app instance initialized only its in-memory SQLite database and started on `127.0.0.1:5055`. The desktop in-app browser returned `ERR_CONNECTION_REFUSED`, then `ERR_CONNECTION_TIMED_OUT`; browser visual/workflow verification is therefore unverified. The server was stopped afterward.

## Feature status

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Guest registration, hashed password, login/logout | Partially verified | `/register`, existing `/login`, CSRF-protected POST guest logout; isolated tests cover registration/password hash. Active MySQL needs migration first. |
| Guest profile and password update | Partially verified | Owner-scoped profile; optional password update requires current password and 10+ character confirmation. Focused test covers accepted/rejected password update. Email change and email verification are not available. |
| Own reservation/payment history and privacy | Partially verified | Guest-scoped reservation/detail query; cross-guest ID request returns 404 in test. Payment/refund data is associated with own reservation. |
| Guest cancellation | Partially verified | Owner check and shared locked service; status/history and refund state updated transactionally. Paid amount is not changed and refund is pending review. SQLite test verifies status, history, and released availability; MySQL locking not stress-tested. |
| Reception phone cancellation | Partially verified | Staff route requires confirmation number, exact guest name, email, normalized phone and reason. Audit distinguishes verified guest requester from staff processor. Test covers wrong phone rejection and success. Phone/email accuracy is the verification source; no external OTP/email verification exists. |
| Duplicate cancellation prevention | Partially verified | Locked reservation row and allowed status transitions reject already-cancelled state. A dedicated repeat-request test remains desirable. |
| Admin/receptionist access | Partially verified | Staff/Admin role decorators applied across dashboard, management, report and API routes; Admin-only event feed and staff event feed authorization have tests. Not every route/write operation has an individual role test. |
| Admin/receptionist existing operational features | Partially verified | Existing room, guest, reservation, payment/refund, settings, audit, and reports modules retained. No comprehensive manual write workflow was run. |
| Real-time operational dashboard | Partially verified | Same-origin 10-second polling from committed audit rows; generic event labels omit guest PII and use `textContent`. Admin/receptionist event route role checks covered in tests; browser observation could not connect. This is polling, not WebSocket push. |
| INR and Indian contacts | Partially verified | Runtime requires INR; ₹ is used across user-visible financial views, charts, and docs. Hotel phone/address defaults are blank rather than fabricated; guest phones normalize to Indian mobile format. Some formatting uses ordinary comma grouping rather than Indian lakh grouping for large values. |
| India timezone/date display | Partially verified | `Asia/Kolkata` helper interprets legacy naive DB timestamps as UTC; templates use day-first dates and timestamps convert to IST. Fixed UTC+05:30 fallback handles Windows without tzdata. Unit test covers midnight conversion. ISO serializers remain machine-oriented. |
| Generic T&C removal | Partially verified | Generic acceptance checkbox and voucher boilerplate removed. Configured cancellation text, refund status/processing notice, check-in/out times, and photo-ID operational notice retained. Browser visual review could not be completed because the in-app browser could not reach the local test server. |
| SQL schema and ORM | Partially verified | Active MySQL metadata inspected read-only. ORM: 15 tables; active: 23 tables. Missing current model columns: `users.guest_profile_id`; `guests.state`, `guests.postal_code`; four cancellation audit fields on `reservation_status_history`. Migration tested in isolated disposable MySQL schema only. |
| Active legacy data | Verified read-only inventory | Eight legacy tables contain 53 rows combined: backup users 5, check_in 8, check_out 2, guest 9, payment 8, reservation 9, room 8, room_type 4. They have independent FK relationships; no deletion or migration was performed. Backup user table contains credential-bearing fields and must remain protected. |

## Implementation changes

- Added guest profile linkage and Indian postal/state fields in ORM plus additive MySQL migration and rollback.
- Added guest register, profile, optional password change, account history/detail, owner-checked cancellation and POST logout.
- Shared phone/self cancellation logic with status history and audit attribution; no automatic refund completion.
- Restricted management routes by role and added safe staff/admin operational audit polling.
- Added India date/time and phone helpers; removed invented property phone/address defaults; localized operational dates and financial displays.
- Removed generic booking acceptance boilerplate and made cancellation/check-in/out policy copy configurable in confirmation/voucher screens.
- Added guest account and localization regression tests. No SQL was applied to `hotelreservationdb`.

## MySQL evidence and safety

- Read-only active target: `hotelreservationdb`, MySQL 8.0.46, 23 visible tables.
- Active metadata exposed 0 views, 0 triggers, 0 procedures, and 0 functions. No active data values were queried; legacy checks used column names, row counts, and foreign-key metadata only.
- Canonical DDL and migration rollback/reapply test ran only in `ghh_schema_validation_20261026`; column checks passed and only that disposable schema was dropped. A first attempt stopped due SQL-comment splitting; its disposable schema was cleaned up, then the corrected retry passed.
- Active schema migration is required before ORM queries using the new fields work against the current live schema. The exact migration is `database/mysql/12_guest_accounts_and_cancellation_audit.sql`; rollback is `database/mysql/12_guest_accounts_and_cancellation_audit_rollback.sql`. It adds two nullable guest fields, a nullable unique user-to-guest FK, and cancellation attribution/refund columns/FK/index. It does not remove guest, reservation, payment, or audit rows. It changes the country default to India.
- Neither migration nor any active database writes were executed. The live migration still requires separate review/explicit approval. No backup/restore was performed or claimed verified.

## Security and unresolved checks

- Verified in tests: password hashes are not plaintext, guest reservation access is owner-scoped, staff pages/API deny guests, and unauthorized phone cancellation details are rejected.
- Current phone identity match uses known guest data; the project has no email/SMS provider or OTP verification. Guest notifications after cancellation are on-screen/account status only.
- The active MySQL schema cannot run the new account paths until its additive migration is approved and applied.
- Not performed: successful manual browser testing (local browser connection failed), browser-based real-time observation, concurrent MySQL booking/payment stress tests, live write workflows, production deployment, dependency vulnerability scan, or verified active DB backup restore.
- No college synopsis/rubric was available in the extracted submission evidence reviewed.
- No active database reset, permanent valuable-file deletion, commit, push, or modification of the original/backup was performed.

## Final packaging and cleanup status

- New archive: `GrandHavenHotel_submission_20261027_verified.zip` in the extracted submission folder. It is a 117-entry archive. CRC and exclusion checks passed; it excludes `.env`, `.git`, environments, local DB/backup files, caches, bytecode, and nested archives. Extraction and tests succeeded (46 passed).
- The older submission ZIP and protected original project were not changed. Python caches remain local if Windows prevents their removal; they are excluded from the archive.
- No active MySQL writes, migration, reset, or destructive operation was performed. The additive migration remains pending review/approval; backup restoration has not been verified.
