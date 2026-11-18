# Final Audit — Grand Haven Hotel

Audit date: 2026-10-25
Workspace: `C:\Users\josep\Downloads\GrandHavenHotel_fixed`

## Verified results

- Current regression suite: **26 passed**, 627 warnings, 10.32 seconds (final post-cleanup run).
- Command: PowerShell: `$env:PYTHONDONTWRITEBYTECODE="1"; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
- The suite uses the isolated in-memory SQLite testing configuration. New regression cases cover no-MySQL configuration rejection, isolated test URI, payment role restriction, INR payment currency, and datetime-to-date normalization.
- Python AST syntax parse: **41 files passed**.
- Flask CLI route map loaded successfully with 44 application endpoints; `python -m flask --app run.py routes`.
- Live connection was inspected read-only: MySQL **8.0.46**, selected schema `hotelreservationdb`.
- ORM schema: all 15 expected tables and columns were present; all 15 ORM foreign keys matched. Six additional foreign keys belong to legacy tables. MySQL uses numeric/decimal and bool/tinyint aliases, and enum columns where model declarations use strings.
- The live schema contains eight extra legacy/backup tables with rows. Core ORM row counts: amenities 10, audit_logs 24, guests 10, hotel_settings 8, payments 8, reservation_rooms 12, reservation_services 0, reservation_status_history 7, reservations 12, roles 2, room_amenities 58, room_types 4, rooms 16, services 5, users 3. Exact legacy counts and reset scope are recorded in `docs/mysql_reset_plan.md`.
- Six read-only live integrity checks returned zero overlaps, invalid date ranges, folio mismatches, ledger mismatches, orphaned reservations, or over-capacity allocations.
- All SQL scripts 01–11 executed in order in a newly created disposable MySQL schema. Result: 15 tables, five views, three triggers, eight procedures/functions, and integrity summary `PASSED` with zero violations. The test schema was dropped after validation.
- Live MySQL Flask test-client GETs were run with a read-only database session: `/`, `/login`, `/api/available-rooms`, `/dashboard`, `/rooms/`, `/guests/`, `/reservations/`, `/payments/`, `/reports/`, `/admin/users`, `/admin/settings`, `/admin/audit-logs`, `/api/dashboard/stats`, and `/api/reservations`. All returned HTTP 200.
- No live database writes, schema changes, commits, or pushes occurred.
- Cleanup removed generated Python caches, `tests/_.code-search`, and an untracked duplicate copy of `reservation_service.py`. `.pytest_cache` could not be removed because Windows returned “Access is denied”; it remains excluded from the final ZIP.
- Final archive: `GrandHavenHotel_submission.zip`, 98 entries, 179,009 bytes; verified required files and confirmed exclusion of local credentials, Git metadata, virtual environments, database files/backups, caches, and scratch/recovery files.

## Warnings and limitations

- The suite reports 627 warnings, mainly repeated SQLAlchemy/Python deprecations for `datetime.utcnow()` defaults/calls, plus one legacy `Query.get()` warning. They do not fail tests, but should be modernized in a separate focused pass.
- SQLite does not enforce MySQL row locks; real simultaneous reservation/payment requests were not stress-tested.
- SQL integration scripts were tested in a disposable MySQL schema, but no destructive live reset or restore was run.
- Browser interaction, dependency vulnerability scanning, exact index/check-constraint parity, and a production deployment were not verified.
- The supplied project did not contain the original college synopsis or grading rubric; academic scope is inferred from supplied phase documents.
- The current live MySQL schema has no installed views, triggers, or routines. The application does not require them for its normal ORM paths.

## Audit disposition

The application and all provided SQL scripts are materially more consistent and have passed isolated regression and MySQL schema-script verification. The deliverable is **not declared fully complete** because a verified backup/restore and approved active database reset remain pending, potential legacy records require the user's decision, and live write/concurrency flows were deliberately not attempted. No commit or push was made.

See `docs/requirements_matrix.md`, `docs/mysql_reset_plan.md`, and `docs/cleanup_record.md` for requirement-level status, exact reset boundaries, and cleanup evidence.

## Follow-up verification — 2026-10-25

The earlier figures above describe the prior checkpoint and are superseded for current source-test results by this follow-up:

- Isolated environment: `.venv\Scripts\python.exe`, Python 3.13.5. `.venv\Scripts\python.exe -m pip check` reported no broken requirements.
- Focused deprecation/date tests: 15 passed with no warnings.
- Current full suite: **29 passed, zero warnings**, 18.85 seconds. Command: `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`.
- AST syntax parse: **44 project Python files passed** (`app`, `tests`, `database`, and `run.py`). Flask application import passed; route map loaded with 48 rules. Active app code has no `datetime.utcnow` or legacy `.query.get(` occurrences.
- Dependency consistency: `pip check` passed. A vulnerability scan was not run because no scanner is installed; no package/network changes were made.
- This follow-up did not connect to or mutate MySQL. Earlier MySQL inspection, disposable SQL-script validation, and read-only live route results above are historical evidence, not rerun results.
- No complete database backup or scratch restore has been verified. A protected destination outside the writable project roots was not available through the current safe workflow. Existing local SQLite files and the separate project backup remain untouched. Therefore the reset plan remains blocked and no active reset is authorized.
- Manual browser interaction, live write/concurrency testing, backup restoration, and production deployment remain unverified.
- The follow-up cleanup and uniquely named ZIP details will be recorded below after execution.

### Clean-package finding and resolution

- The first extracted archive test uncovered that `TestingConfig` inherited its session secret from the ignored local `.env`. An archive that correctly excluded `.env` therefore failed session/CSRF-dependent tests. This was a test reproducibility defect, not a production-secret leak.
- `TestingConfig` now declares an isolated test-only secret, and `tests/test_config.py` asserts the setting. The full source suite then passed **29 tests** with zero warnings, and the extracted final archive also passed **29 tests** with zero warnings.
- Final archive: `GrandHavenHotel_submission_20261025_final.zip`; **102 entries**. ZIP CRC passed; required app/SQL/docs/tests/environment-template files were present. Local `.env`, Git metadata, `.venv`, `venv`, instance data, `.codex`, database files, bytecode, and recovery files were absent.
- The original `GrandHavenHotel_submission.zip` was preserved. No active MySQL reads or writes were made in this follow-up. No complete backup/restore was performed, so active reset remains prohibited pending the required evidence and separate explicit approval.
