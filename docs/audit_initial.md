# Initial Audit — Grand Haven Hotel

Date: 2026-10-25
Workspace: `GrandHavenHotel_fixed`

## Baseline state

- Project source, docs, tests, SQL scripts, and local artifacts inventoried.
- Git has no commits on `master`; project files are staged as additions, with additional unstaged edits in `app/__init__.py`, `app/config.py`, `app/routes/auth.py`, `app/templates/base.html`, `run.py`, and `tests/conftest.py`.
- Untracked items: `app/__init.py.phase4-backup`, `tests/_.code-search`, `tests/import uuid.py`, and `tests/test_api_csrf.py`.
- Local `.env` exists and is ignored. It was not printed or copied. It configures MySQL dialect with database name `hotelreservationdb`.
- Existing `.venv`, `venv`, `instance/grand_haven_hotel.db`, and `instance/grand_haven_hotel.db.backup` are retained as potentially useful local state.
- MySQL Shell is installed; the classic `mysql` executable was not found.

## Baseline verification

Command: `.\\.venv\\Scripts\\python.exe -m pytest -q`

Observed: **22 passed**, no failures, in 7.84 seconds. Warnings include Python `datetime.utcnow()` deprecations, SQLAlchemy legacy `Query.get()`, and inability to write pytest cache files. Tests use the testing configuration and in-memory SQLite, not the configured MySQL database.

## Verified findings

- Application models use plural table names (`guests`, `rooms`, `room_types`, `reservations`, `payments`, etc.).
- SQL script 01 and 02 select `hotelreservationdb`; scripts 03–11 select `grand_haven_hotel`.
- Runtime config defaults to a local SQLite file when `DATABASE_URL` is absent; `TestingConfig` uses in-memory SQLite.
- Currency defaults conflict: app config/payment model/seed use USD in some places while UI, MySQL DDL, and SQL seed use INR.
- `run.py` initializes and seeds on normal startup; its `reset-db` command drops all mapped tables.
- No college rubric/synopsis was located in the supplied project files; docs describe an ADBMS academic deliverable.

## Initial high-priority work list

1. Read-only compare live MySQL table metadata against ORM model expectations.
2. Reconcile SQL schema target database and SQLAlchemy model DDL.
3. Eliminate implicit normal-operation SQLite fallback and startup schema mutation/seeding; preserve isolated tests and explicit setup commands.
4. Resolve currency defaults consistently based on documented project choice, with INR currently evidenced by UI/SQL setup.
5. Inspect authentication, authorization, CSRF, reservation concurrency, payment/refund logic, and all SQL mutations.
6. Correct the integrity validator summary so it reports aggregate rule outcomes rather than unconditional success.
7. Update setup docs and safe environment example; prepare (but do not execute) live reset plan.
8. Create two-pass cleanup record; retain uncertain local files, environments, database files, backup, and Git metadata.

## Safety boundary

No active MySQL schema/data was changed. No local database, environment file, backup, virtual environment, or Git metadata was deleted. No commit or push was performed.
