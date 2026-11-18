# Requirements and Verification Matrix

Status reflects work performed through 2026-10-25. “Passed” applies only to the checks named in the evidence; it is not a production certification.

| Requirement | Evidence and files | Status | Remaining verification |
|---|---|---|---|
| Flask application uses MySQL for normal operation | `app/config.py`, `app/__init__.py`; configured MySQL URL verified as MySQL 8.0.46 and `hotelreservationdb` | Passed | A startup attempt with no URL is covered by regression test; production deployment configuration still needs operator values |
| Test database is isolated | `TestingConfig` uses in-memory SQLite; `tests/test_config.py` | Passed | MySQL-specific locking is not exercised by SQLite tests |
| Login, logout, open redirect, CSRF | `app/routes/auth.py`, templates, `tests/test_auth.py`, `tests/test_api_csrf.py` | Passed in automated suite | Manual browser interaction was not run |
| Guest, rooms, reservations, lifecycle, payment/refunds | Routes, services, templates, and corresponding `tests/test_*.py` | Passed for test database workflows | Full live write path intentionally not exercised against active data |
| Payment permissions and row locking | Payment routes restrict to Admin/Receptionist; payment service locks payment/reservation rows; authorization regression | Passed in unit suite | Real simultaneous transactions not load-tested |
| Room booking overlap prevention | Reservation service locks room rows; `08_triggers.sql` includes overlap guard; reservation tests | Partially verified | Concurrency behavior under simultaneous MySQL sessions remains unverified |
| Currency is consistently INR | App config, payment model/service, seeder, SQL seed and DDL, settings UI, schema docs | Passed by source inspection and INR regression assertion | Live data remains unchanged; existing payment rows already use INR |
| ORM tables, columns, nullability, and foreign keys | Read-only MySQL metadata comparison; 15 expected tables present; no ORM foreign keys absent; type aliases and MySQL enums documented | Passed with dialect differences | Full index/check-constraint equivalence has not been exhaustively compared |
| Legacy duplicate schema objects are understood | Read-only structure and row counts for eight extra legacy tables; app source references use plural model tables | Partial | Data lineage and business need for those rows cannot be inferred from counts alone |
| MySQL scripts 01–11 | Executed in order on disposable `ghh_validation_*` schema; 15 tables, 5 views, 3 triggers, 8 routines; integrity summary passed, zero violations; disposable schema dropped | Passed on disposable MySQL schema | Not installed in active schema; active objects remain unchanged |
| Live application views | Read-only test-client GETs for public/login and 11 staff/API endpoints; all returned 200 | Passed for GET paths | State-changing flows intentionally not run against active database |
| Audit aggregation | Six read-only live-data checks returned zero violations; script 11 summary uses aggregate counts | Passed for current snapshot | Data can change after this audit |
| Documentation and environment template | README, MySQL guide, phase docs, relational schema, `.env.example` | Partial | College rubric/synopsis was not supplied; deliverable-specific grading cannot be confirmed |
| Security and reliability audit | CSRF, login redirect, session settings, payment roles, secret exclusion, transactions reviewed | Partial | Dependency vulnerability scan, manual browser audit, and production threat model not performed |
| Cleanup and final archive | Two-pass cleanup record; 98-entry archive inspected for secrets/local data | Passed with one local cache permission exception | `.pytest_cache` remains in workspace because Windows denied deletion; it is excluded from the archive |
| Active database reset | Exact plan prepared separately; no live objects changed | Blocked pending explicit approval | Requires reviewed backup/restore test and approval to replace all rows and schema objects |
| Git delivery | Git working tree changes preserved; no commit/push | Passed | No commit/push was made |

## Follow-up verification — 2026-10-25

| Requirement | Current follow-up evidence | Status | Remaining verification |
|---|---|---|---|
| Deprecation cleanup and date default | Active code uses shared UTC helpers; callable date default; legacy query lookups modernized; focused tests 15 passed | Complete and verified | Naive UTC is intentionally retained for existing MySQL `DATETIME` columns |
| Full regression suite | `.venv` Python 3.13.5, pytest command in `docs/final_audit.md`; 29 passed, zero warnings | Complete and verified | MySQL-specific concurrency remains separate/unverified |
| Clean archive runs without local `.env` | Final ZIP extraction and test run: 29 passed, zero warnings; test-only fixed key is isolated to `TestingConfig` | Complete and verified | Installing dependencies in a brand-new environment was not repeated; current installed `.venv` used |
| Dependency consistency | `.venv` `pip check` reported no broken requirements | Complete and verified | Vulnerability scanning not run; scanner not available locally and no network install attempted |
| Submission packaging | Final archive verified for CRC, required files, and absence of local config, Git metadata, environments, databases, caches, and recovery files | Complete and verified | See final report for final file size |
| Full active-MySQL backup and scratch restore | No protected destination was available in the authorized workspace; no dump or restore made | Blocked | User must provide/authorize a protected backup destination/tool before a reset can be considered |
| Active database reset | No live write performed | Blocked pending explicit separate approval and verified backup/restore | Reset remains prohibited |
| Browser, live writes/concurrency, deployment, dependency scan | Not run during this follow-up | Pending / unverified | Requires suitable browser, disposable MySQL test schema, deployment target, or scanner |

## Current task addendum — 2026-10-27

The current extracted-submission implementation status supersedes older feature claims above; the detailed evidence and limitations are in `docs/feature_implementation_audit_20261027.md`.

| Requirement | Current evidence | Status | Remaining work |
|---|---|---|---|
| Guest accounts/profile/ownership | Registration, linked profile, current-password-verified password change, reservation/payment detail and cross-guest denial tests | Partially verified (SQLite) | Active MySQL migration and contact verification/email updates |
| Guest and receptionist cancellation | Shared locked cancellation service; ownership/identity checks; requester/processor, source, history and pending refund status tests | Partially verified (SQLite) | MySQL concurrency, separate repeat-cancellation regression, operator-configured fee behavior |
| Admin/receptionist permissions and activity | Role guards on management/API endpoints; generic PII-minimized event polling; guest and receptionist/admin route tests | Partially verified | Browser polling observation and full route-by-route authorization matrix |
| India localization and policy UI | INR requirement, mobile normalization, IST conversions/day-first templates and CSV, configurable policy text, generic boilerplate removed | Partially verified | Lakh grouping consistency and browser review |
| MySQL schema | Read-only comparison: 15 ORM tables, 23 active tables; current ORM needs columns absent in active schema. Migration/rollback/reapply succeeded on disposable MySQL schema | Partially verified | Separate approval before live migration; backup/restore evidence outstanding |
| Legacy database structures | 8 singular legacy tables with 53 combined rows and own FK references inventoried read-only | Retain / unresolved lineage | No migration or deletion recommendation until records are reviewed by owner |
| Regression tests | Final full suite: 46 passed on Python 3.13.5, isolated in-memory SQLite; extracted archive suite also 46 passed | Complete and verified for this test configuration | MySQL writes/locks, browser, deployment, vulnerability scan unverified |
| Final cleanup and ZIP | Two-pass cache review recorded; final 117-entry ZIP CRC/exclusion check passed; extracted copy passed all 46 tests | Complete and verified for package integrity and test suite | Local caches may remain; excluded from ZIP |
| Browser and real-time visual check | Temporary app used in-memory SQLite on port 5055; in-app browser returned `ERR_CONNECTION_REFUSED`, then `ERR_CONNECTION_TIMED_OUT` | Blocked | Browser visual interaction and polling observation remain unverified |
