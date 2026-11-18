# Current Task Checklist — 2026-10-25

Workspace verified as `C:\Users\josep\Downloads\GrandHavenHotel_fixed`, the Git root and only visible worktree. No sibling project/backup directory or archive was found in `Downloads`; the user's separate backup location is not available to this session. The untracked `.codex/environments/environment.toml` was inspected and will be preserved. No files were edited before this checkpoint.

## Starting checkpoint

- Git: unborn `master` branch; 89 project files already staged as additions; previous audit changes are unstaged; no commits exist. Preserve all staged, unstaged, ignored, and untracked changes.
- Python: `.venv\Scripts\python.exe` is Python 3.13.5. It has Flask 3.0.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.5, pytest 8.2.2, PyMySQL 1.1.1. Global Python is `C:\Python313\python.exe` with SQLAlchemy 2.1.6; global packages will not be modified.
- Baseline command: `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`
- Baseline result: **26 passed, 627 warnings, 19.79s**. Warnings match the prior deprecation report.
- `.env` exists and selects MySQL `hotelreservationdb`; only scheme/database/secret presence were inspected, never values.
- Current ZIP is readable and passes `ZipFile.testzip()`, 98 entries. It may need regeneration after follow-up changes.
- `.pytest_cache` remains due prior Windows access-denied result; do not force permissions.

## Prioritized work

1. Replace deprecated UTC calls with a shared naive-UTC helper consistent with existing MySQL `DATETIME` columns; correct the import-time `service_date` default; replace direct legacy `Query.get()` use. Add focused regression coverage.
2. Rerun focused and full tests; confirm warning count falls without weakening assertions.
3. Recheck app workflow/security findings and SQL schema mappings; do not write to the active database.
4. Check for available dependency audit tools and run `pip check`; do not install globally or change dependency versions.
5. Assess whether a protected full database backup and scratch restore are possible without touching the user's separate backup or exposing real records. If file permissions/target remain uncertain, stop before the operation and document exact requirements.
6. Update checklist, change log, requirements matrix, final audit, cleanup record, and submission ZIP after verification. Preserve the active database; no reset, commit, or push.

## Follow-up completion checkpoint

- Replaced deprecated UTC timestamps with a shared naive-UTC helper compatible with existing MySQL `DATETIME` columns. Corrected the service-date default from an import-time value to a callable. Replaced active legacy `Query.get` calls with SQLAlchemy 2.x session/get helpers.
- Added `tests/test_datetime_utils.py`. Focused command: `python -m pytest tests/test_datetime_utils.py tests/test_auth.py tests/test_reservations.py -q -p no:cacheprovider` — **15 passed**, no warnings.
- Full command: `$env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider` — **29 passed in 18.85s**, zero warnings.
- `.venv\Scripts\python.exe -m pip check` — no broken requirements found.
- AST parse passed for the project `app`, `tests`, `database` Python files and `run.py` — **44 files**. Flask app import passed; route map loaded with **48 rules**. Active app search found no `datetime.utcnow` or `.query.get(` uses.
- No dependency vulnerability scanner is installed in the available environment; no network installation was attempted.
- Current local DB files were inventoried by name and size only; they are retained and excluded from submission. No MySQL backup or scratch restore was performed in this follow-up. Creating a protected backup outside the authorized writable project roots and proving a restore could not be completed safely with the currently available file permissions/tools. Active-database reset remains prohibited pending separate approval and backup evidence.
- Live MySQL route GETs, concurrent MySQL write workflows, manual browser interaction, and production deployment were not rerun in this follow-up. The prior report's results remain historical evidence only.
- The existing archive was preserved. A uniquely named follow-up submission archive and extraction check remain to be completed.
- No destructive cleanup, active database mutation, commit, or push was performed.
- Extracted package initially failed 14 tests because `TestingConfig` inherited its secret from the excluded local `.env`. Added an isolated test-only key and regression assertion. Rebuilt a distinct final ZIP; extraction/package checks passed and the extracted suite passed **29 tests** with zero warnings.
- Final archive candidate: `GrandHavenHotel_submission_20261025_final.zip`, 102 entries, ZIP CRC passed. Required setup/source/test files are present; `.env`, Git metadata, environments, local DBs, caches, and recovery files are absent. Exact final file size is reported in the delivery summary.

## Status

- Deprecation repair and regression verification: complete.
- Static/import/route and dependency consistency checks: complete.
- Documentation refresh, two-pass archive cleanup review, and new archive: in progress.
- Protected full database backup and restore: blocked by safe destination/permission limitations; no active reset will occur.
- Live MySQL write/concurrency, browser, deployment, and vulnerability scans: unverified.
