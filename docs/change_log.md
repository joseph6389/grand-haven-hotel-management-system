# Change Log and Rollback Notes

## 2026-10-25 — Baseline

- Recorded initial inventory and test outcome in `docs/audit_initial.md`.
- No application or database changes made at baseline.

## 2026-10-25 — Application and database repair

- Removed implicit SQLite normal-operation fallback; development/production app startup now requires a configured MySQL URL. Testing remains on in-memory SQLite.
- Removed startup `create_all` and seeding, and removed the destructive `reset-db` CLI command. `init-db`/`seed-db` remain explicit commands.
- Standardized application currency defaults and demo seeding to INR.
- Added MySQL row locks for payment/refund workflows and Admin/Receptionist role checks for payment routes.
- Corrected a datetime parsing edge case.
- Updated DDL, SQL script database targets, payment refund fields/statuses, MySQL triggers, stored-procedure room serialization, and the six-rule integrity summary.
- Added `.env.example`, setup and reset guidance, requirements matrix, audit report, cleanup record, and regression tests.
- Verified 26 tests, 41 Python syntax parses, live read-only route rendering, live read-only integrity counts, and all 11 SQL scripts in a disposable MySQL schema.
- No active database rows/objects changed; no Git commit/push made.

## Rollback notes

- Source edits are uncommitted and remain reviewable with `git diff`; original staged Git additions were preserved.
- The live database was only queried read-only. The disposable validation schema was dropped after successful validation.
- To undo code edits selectively, use the pre-existing working-tree version/diff. Do not reset all Git changes because the repository began with staged additions and user modifications.
- The untracked prior app factory backup was retained locally.

## 2026-10-25 — Follow-up audit checkpoint

- Reconfirmed the workspace is the project Git root and sole visible worktree; no adjacent backup was discoverable. The separate backup location remains unknown and was not accessed.
- Preserved existing staged additions, unstaged modifications, `.codex/environments/environment.toml`, and existing archive.
- Rechecked `.venv` package versions and reran baseline tests before edits: 26 passed, 627 warnings, 19.79s.
- Created `docs/task_checklist.md` to track this follow-up. No application/database edits have yet been made in this follow-up.

## 2026-10-25 — Deprecation and date-default follow-up

- Added `app/utils/datetime_utils.py` and its package initializer. It returns naive UTC datetimes to preserve existing MySQL `DATETIME` semantics and provides a dynamic UTC-date helper.
- Updated active timestamp defaults/calls and replaced legacy ORM `Query.get` patterns with SQLAlchemy 2.x APIs. Corrected `ReservationService.service_date` so it is evaluated per instance rather than once at import time.
- Added `tests/test_datetime_utils.py` for UTC shape and dynamic defaults.
- Focused test command: `python -m pytest tests/test_datetime_utils.py tests/test_auth.py tests/test_reservations.py -q -p no:cacheprovider` — 15 passed, zero warnings.
- Full suite: `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` — 29 passed, zero warnings (18.85s).
- Additional checks: `.venv\Scripts\python.exe -m pip check` reported no broken requirements; AST parse passed for 44 project Python files; app import passed; route map loaded with 48 rules; no deprecated active UTC or `.query.get` patterns remain.
- Rollback: inspect/revert only the listed app and test paths using the current working-tree diff; preserve the pre-existing staged baseline and all other changes. No database operations were performed for this change.
- Clean-package testing exposed a missing test-only secret: the tests had depended on the ignored local `.env`. `TestingConfig` now defines a fixed, non-deployment test secret and `tests/test_config.py` asserts it, so CSRF/session tests run from an archive that contains no `.env`. Full source suite after this fix: 29 passed, zero warnings. Extracted final archive suite: 29 passed, zero warnings.

## 2026-10-26/27 — Guest, cancellation, localization, security and operations follow-up

- Target: extracted submission `GrandHavenHotel_submission_20261025_final`; the original `GrandHavenHotel_fixed`, separate backup, and prior ZIP were not edited.
- Added guest-profile linkage, guest registration/profile/password-change/history/detail/logout routes and owner checks; added Indian state/postal code model fields.
- Added common locked cancellation service for account and verified phone requests; stored source/requester/processor/reason/status/refund attribution and kept refund state pending review.
- Added role checks for staff dashboard, rooms, guests, reservations, reports and APIs; added admin-only and staff-safe PII-minimized audit polling.
- Added India timezone/date/phone utilities, localized date displays/CSV, INR documentation/UI, verified-property-contact blanks, configured cancellation text, and removed generic booking checkbox/voucher T&C boilerplate.
- Hardened booking result rendering against HTML injection and replaced database exception details shown in payment/reservation flows with safe messages and server-side logs.
- Added admin settings validation for contact, times, tax range, and policy. Admin currency remains INR.
- Added regression coverage in `tests/test_guest_accounts.py`, `tests/test_datetime_utils.py`, `tests/test_india_localization.py`, and `tests/test_admin_settings_validation.py`.
- Full suite command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -q -p no:cacheprovider` — **41 passed in 17.75s** (before the last settings/temporal security edits; rerun is required for final status).
- AST parse/import check at prior checkpoint: 47 Python files parsed; testing app imported; 55 route rules registered. Repeat final check after remaining edits.
- Read-only active MySQL introspection selected `hotelreservationdb`, MySQL 8.0.46: 23 tables, 15 ORM tables; three model tables lack new fields. Legacy tables total 53 rows. No active schema/data writes occurred. `SHOW GRANTS` exposed a root-level connection account; no credentials were printed or changed.
- Canonical DDL and migration rollback/reapply passed in disposable schema `ghh_schema_validation_20261026`; only that disposable schema was dropped. An initial runner failed parsing a leading SQL comment, then cleaned its disposable schema; corrected run passed.
- Rollback: use the original submission ZIP checkpoint and selectively revert only this follow-up's listed files; do not reset another working copy or database. No `.env`, active DB, original project, Git commit, or push was changed.

## 2026-10-27 — Final verification and package

- Final source suite on Python 3.13.5: `python -m pytest -q -p no:cacheprovider` with `PYTHONDONTWRITEBYTECODE=1` — 46 passed in 18.93 s. `python -m pip check` reported no broken requirements.
- Built `GrandHavenHotel_submission_20261027_verified.zip` without replacing the prior ZIP. It contains 117 files/entries (214,943 bytes at initial packaging); CRC and excluded-file checks passed, and a separately extracted copy passed 46 tests in 25.78 s. The package excludes `.env`, environments, Git data, local databases/backups, and caches.
- Started a temporary app with in-memory SQLite on port 5055. The in-app browser could not connect (connection refused, then timed out); browser visual verification is not claimed. Server was stopped.
- Completed two-pass cleanup review and removed only generated `.pytest_cache`, `__pycache__`, and `.pyc` artifacts inside the extracted project. `.env`, source files, database records, backups, prior ZIP, original project, and separate backup were retained.
- Database operation log: no active `hotelreservationdb` mutation. SQL scripts 01–11 and migration rollback/reapply were exercised only in disposable schemas in the prior recorded checks; no active database backup/restore was performed. No Git commit or push.
- Rollback: source changes remain separately reviewable; the original project and prior archive remain unchanged. The generated cache files are reproducible. Remove only the newly named ZIP if the user later decides it is not needed.

### Final evidence correction

- The final source-tree run was 46 passed; the final extracted-package run was 46 passed.
- The refreshed ZIP contains 117 entries. CRC and exclusion checks passed. Its exact final byte size is recorded in the delivery report; it is intentionally not embedded in this archive because doing so changes the archive size.
