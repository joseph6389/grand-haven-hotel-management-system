# Feature Inventory and Starting Checkpoint — 2026-10-26

## Workspace and baseline

- Target: `C:\Users\josep\Downloads\GrandHavenHotel_submission_20261025_final` (user-designated extracted submission).
- Original: `C:\Users\josep\Downloads\GrandHavenHotel_fixed` (not modified).
- The target has no `.git` directory; the original remains on an unborn `master` with pre-existing staged/unstaged work.
- The extracted files matched all 102 non-local members in the prior `GrandHavenHotel_submission_20261025_final.zip` byte-for-byte. That ZIP is the rollback checkpoint. `.env` was excluded from comparison and never read or disclosed.
- Environment: Python 3.13.5; `python -m pip check`: no broken requirements.
- Baseline: `python -m pytest -q -p no:cacheprovider` — 29 passed in 8.38s. This test configuration uses isolated in-memory SQLite, not MySQL.
- No application, schema, seed, or active-database changes have been made in this audit.

## Feature matrix

| Feature | Existing evidence | Status | Main files | Schema needed? |
|---|---|---|---|---|
| Staff login/logout/password hashing | `User`, Werkzeug hash methods, `/login`, POST `/logout`, CSRF | Present for staff | `app/models/user.py`, `app/routes/auth.py` | No |
| Admin/receptionist distinction | `roles`, `admin_required`; shared `is_receptionist` treats Admin as receptionist | Partial; permission review required | `app/routes/auth_helpers.py`, routes | No |
| Guest registration/login/logout | No guest auth routes; login queries `users` only | Missing | `app/routes/auth.py`, `app/models/user.py` | Yes, safe `users`↔`guests` link or account table design |
| Guest profile and reservation history | Staff guest directory/detail only; no authenticated ownership scope | Missing | `app/routes/guests.py`, templates | Likely account-to-profile link |
| Guest self-service cancellation | Generic authenticated staff cancellation route has no ownership check | Missing; current authorization is too broad | `app/routes/reservations.py`, `app/services/reservation_service.py` | Audit metadata likely needed |
| Receptionist phone cancellation | Generic staff cancellation accepts free-text reason; no request source or verified requester/processor distinction | Partial and insufficiently attributed | reservation routes/service, `ReservationStatusHistory`, `AuditLog` | Likely additive audit fields or structured audit metadata |
| Shared cancellation rules/refund state | Status transition and status history exist; cancellation does not model fee/refund policy transactionally | Partial | reservation service, payment service/models | Maybe additive cancellation audit fields; preserve payments |
| Admin operations | Staff management, settings, audit logs, reports, rooms, guests and reservations | Substantially present; scope/authorization needs audit | `app/routes/admin.py`, dashboard/reports | No for current functions |
| Receptionist operations | Shared dashboard, guest/room/reservation/payment flows; several routes use only `login_required` | Present but authorization too broad in places | route modules and templates | No for access tightening |
| Real-time operations | Dashboard stats JSON and browser chart code; no Socket.IO/WebSocket dependency or authenticated event feed found | Missing push; polling is a low-complexity option | `app/routes/api.py`, `dashboard.js`, `AuditLog` | No if audit log is source |
| INR display | INR defaults and several ₹ displays; USD remnants in API docs and `$` in guest detail | Partial | config, templates, docs, seed | No |
| India contact defaults | `.env.example` uses +91, but runtime config, seed, forms and fixtures include +1/US data | Partial | config, seed, templates, tests | No |
| Indian timezone/date display | Timestamps are naive UTC; `date.today()` and English/US date formatting remain | Partial; conversion policy needed | datetime utils, routes, templates | No if stored timestamps remain UTC |
| Terms/policy content | Cancellation policy is configurable and operationally relevant; generic wording scan pending | Partial | settings and booking templates | No |
| Existing regression suite | 29 tests pass | Verified baseline | `tests/` | SQLite only |

## Prioritized implementation plan

1. Finish targeted UI/currency/date/policy scan and map all relevant routes, forms, APIs, model constraints, and audit events.
2. Design guest account linkage and cancellation audit representation; add an additive MySQL migration with a rollback, and test it only in disposable SQLite/MySQL schemas where available.
3. Implement guest registration/login/profile/history with server-side ownership and safe linking rules; prevent access by another guest.
4. Refactor both cancellation pathways through one transaction-safe service. Capture source, requester, processor, reason, prior/resulting status and refund status. Keep refunds pending until processed.
5. Tighten route role permissions; add receptionist phone-cancellation confirmation and identity-verification fields without treating a confirmation number alone as identity proof.
6. Add an Admin-only operational event feed backed by committed audit records and a modest polling interval, unless an installed realtime dependency is found; do not broadcast private guest details.
7. Apply INR/Asia-Kolkata presentation and India contact defaults without inventing hotel identity or tax compliance. Remove only generic boilerplate; retain concise cancellation/payment/privacy notices.
8. Add regression/security tests, run all tests and startup/route checks, then prepare and extract-test a new uniquely named ZIP. Never change `.env`, active MySQL, original project, or existing ZIP.

## Change log

- 2026-10-26: Read-only inventory and baseline completed. No project source or database changed.
