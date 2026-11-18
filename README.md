# Grand Haven Hotel — Hotel Reservation Management System
### Full-Stack Python & Advanced Database Management Systems (ADBMS) Academic Implementation

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/Flask-3.0.3-black.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Bootstrap 5.3](https://img.shields.io/badge/Bootstrap-5.3.3-purple.svg)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Tests-53%20Passed-success.svg)]()
[![ADBMS](https://img.shields.io/badge/ADBMS-Phase%20I--IV%20Complete-gold.svg)]()

A complete hotel reservation management system built from scratch for an **Advanced Database Management Systems (ADBMS)** academic evaluation. The project couples a luxury hotel booking website with a robust back-of-house management portal and demonstrable relational database operations across all four academic phases.

---

## Key Features

1. **Public Luxury Hotel Portal (`/`)**
   - High-end hospitality design system (Warm Ivory `#FAF8F5`, Champagne Gold `#C5A880`, Charcoal Navy `#1A2238`).
   - Live date-based availability search querying real database records.
   - Featured suite showcases with bed configurations, capacity, and nightly rates.
   - Direct online guest booking with instant confirmation voucher generation (`/confirmation/<number>`).
   - Resort amenities, guest testimonials (demo content), interactive location, and concierge contact form.

2. **Executive Management Dashboard (`/dashboard`)**
   - 8 live operational KPIs (Available Rooms, Occupied Rooms, Monthly Revenue, Active Bookings, Today's Arrivals & Departures, Total Guests, Occupancy Rate %).
   - Real-time **Chart.js** data visualizations: Monthly Revenue 6-Month Rolling Trend and Reservation Status Distribution.
   - Today's Arrivals and Today's Departures action tables with quick check-in / check-out buttons.
   - Recent reservations log with links to full folios.

3. **Room Inventory Management (`/rooms`)**
   - Physical room inventory table with filtering by room type, operational status, and floor.
   - Separation of operational status (`operational`, `maintenance`, `out_of_order`) from reservation-based availability.
   - "Add Room" modal dialog with validation and amenity assignment.
   - "Edit Room" modal dialog and quick operational status toggles.

4. **Guest Relations & CRM (`/guests`)**
   - Comprehensive guest directory with live search by name, email, or telephone.
   - Unique constraints preventing duplicate guest email profiles.
   - Detailed guest folio (`/guests/<id>`) displaying personal details, identification records, and complete reservation history.

5. **Core Reservation Engine (`/reservations`)**
   - Multi-step booking wizard (`/reservations/create`) with live AJAX room querying (`/api/available-rooms`) and server-side price quotes (`/api/pricing-quote`).
   - **Double Booking Prevention**: Enforces strict date-overlap checks: `NOT (check_out <= req_in OR check_in >= req_out)`.
   - Server-side financial calculations: Lodging charges, configurable tax rates, and optional discounts.
   - Lifecycle status transitions: `pending` &rarr; `confirmed` &rarr; `checked_in` &rarr; `checked_out` (or `cancelled`).
   - Detailed Folio view (`/reservations/<id>`) with room allocations, payment history, and status audit trail.
   - Print-ready luxury booking confirmation voucher (`/reservations/<id>/voucher`) with barcode mockup.

6. **Payments Ledger & Financial Receipts (`/payments`)**
   - Complete transaction ledger with method, currency, status, and transaction reference.
   - Settle folio balances via simulated payment gateway.
   - Overpayment protection and refund processing.
   - Print-friendly official payment receipt (`/payments/<id>/receipt`).

7. **Analytics, Business Intelligence & Reports (`/reports`)**
   - Aggregated room classification performance (bookings count, average stay length, total revenue).
   - Unsettled folios alert table for front desk debt recovery.
   - Instant streaming CSV exports: `grand_haven_reservations.csv` and `grand_haven_payments.csv`.

8. **Administration & Security (`/admin/users` & `/admin/settings`)**
   - Role-Based Access Control (RBAC): `Guest`, `Receptionist`, and `Admin` roles enforced by backend route checks.
   - Staff user directory with account creation and one-click activation/deactivation.
   - Dynamic property settings (hotel name, contact email, phone, currency, lodging tax rate, check-in/out hours, cancellation terms).
   - System-wide security and mutation audit trail (`/admin/audit-logs`).

9. **Guest Self-Service (`/register` & `/account`)**
   - Guest registration, sign-in, profile updates, password changes, own reservation and payment history, and self-service cancellation.
   - Existing guest profiles are not linked to new accounts based only on matching email or phone. Reception must verify those records.
   - Cancellation fees follow the configured 48-hour check-in rule; refund eligibility is reviewed separately, and staff refund actions record ledger changes without confirming external payouts.
   - Admin and receptionist dashboards poll a safe operational event feed; no guest or payment details are broadcast.

---

## Test and setup information

Setup commands, account roles, cancellation workflows, MySQL migration notes, and known limits are documented in `docs/guest_roles_cancellation_and_india.md`. The SQL seed contains synthetic staff account records; do not deploy academic seed credentials as production credentials.

---

## Quick Start (MySQL)

Normal application operation requires MySQL 8.0+; the app does not create or seed a database during startup. Tests use a separate in-memory SQLite database.

### 1. Create and activate an isolated virtual environment
**Windows (PowerShell):**
```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
If `.venv` already exists, activate it and skip the creation and installation commands.
### 2. Configure MySQL
For a new empty schema, run `database/mysql/01_Create_Database_Tables.sql` and `02_Insert_Sample_Data.sql` in order. Do not run them against the existing database until the backup, restore, legacy-data review, and approval steps in `docs/mysql_reset_plan.md` are complete. Copy `.env.example` to `.env` and set a MySQL `DATABASE_URL` plus a private `SECRET_KEY`.

### 3. Seed the database (only when appropriate)
An optional Python seed command is available as an alternative for a new empty database; do not run it after SQL seed script 02 or against a database containing valuable records:
```powershell
# Seed the configured database:
python -m flask --app run.py seed-db
```

### 4. Launch the Application
```powershell
python run.py
```
Open your browser and navigate to:
- **Public Homepage & Guest Booking**: [http://localhost:5000/](http://localhost:5000/)
- **Staff Management Portal Login**: [http://localhost:5000/login](http://localhost:5000/login)

---

## Running the Automated Test Suite

The project includes automated tests covering security, authentication, room CRUD, guest directory, date-overlap prevention, reservation lifecycles, payment ledgers, CSV exports, and transaction rollbacks.

Execute the test suite using `pytest`:
```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

**Latest observed test result:** `53 passed, zero warnings` (Python 3.13.5, pytest 8.2.2; verified 2026-11-02). See `docs/final_audit.md` for historical audit scope and checks not performed.

---

## ADBMS Academic Phase Implementations & MySQL Integration

All four academic phases are documented and accompanied by standalone, executable MySQL scripts under `database/mysql/`:

| Academic Phase | Topic | Script File / Documentation |
| :--- | :--- | :--- |
| **Phase I** | Conceptual & Logical Data Modelling | [`docs/er_diagram.md`](docs/er_diagram.md) &bull; [`docs/relational_schema.md`](docs/relational_schema.md) &bull; [`docs/actual_3nf_model.md`](docs/actual_3nf_model.md) |
| **Phase II** | Database Creation & DDL | [`database/mysql/01_Create_Database_Tables.sql`](database/mysql/01_Create_Database_Tables.sql) |
| **Phase II** | Synthetic Dataset Population | [`database/mysql/02_Insert_Sample_Data.sql`](database/mysql/02_Insert_Sample_Data.sql) |
| **Phase II** | Data Cleaning & Basic Queries | [`database/mysql/03_data_cleaning_and_basic_queries.sql`](database/mysql/03_data_cleaning_and_basic_queries.sql) |
| **Phase III**| Advanced Joins & Subqueries | [`database/mysql/04_advanced_joins_and_subqueries.sql`](database/mysql/04_advanced_joins_and_subqueries.sql) |
| **Phase III**| Database Views | [`database/mysql/05_views.sql`](database/mysql/05_views.sql) |
| **Phase III**| Stored Procedures (5 Procedures) | [`database/mysql/06_stored_procedures.sql`](database/mysql/06_stored_procedures.sql) |
| **Phase III**| Stored Functions (3 Functions) | [`database/mysql/07_stored_functions.sql`](database/mysql/07_stored_functions.sql) |
| **Phase III**| Database Triggers (2 Triggers) | [`database/mysql/08_triggers.sql`](database/mysql/08_triggers.sql) |
| **Phase III**| Query Execution & EXPLAIN Analysis | [`database/mysql/09_query_execution_and_explain.sql`](database/mysql/09_query_execution_and_explain.sql) |
| **Phase IV** | Transactions, ACID & SAVEPOINT | [`database/mysql/10_transactions_and_acid.sql`](database/mysql/10_transactions_and_acid.sql) |
| **Phase IV** | Database Integrity Validator | [`database/mysql/11_integrity_validator.sql`](database/mysql/11_integrity_validator.sql) |

For complete instructions on connecting Flask to MySQL Server and running the scripts in MySQL Workbench, consult the **[MySQL Setup & Migration Guide](docs/mysql_setup_guide.md)**.

---

## Project Structure

```text
hotel-reservation-management-system/
├── app/
│   ├── __init__.py                 # Application factory & Jinja filters
│   ├── config.py                   # Config (Dev, Test, Prod) & DB URLs
│   ├── extensions.py               # SQLAlchemy, Migrate, LoginManager, CSRF
│   ├── models/                     # 3NF Relational ORM Models
│   │   ├── __init__.py
│   │   ├── user.py                 # User & Role entities
│   │   ├── guest.py                # Guest CRM entity
│   │   ├── room.py                 # Room, RoomType, Amenity entities
│   │   ├── reservation.py          # Reservation, ReservationRoom, History
│   │   ├── payment.py              # Payment entity
│   │   ├── service.py              # Service & ReservationService entities
│   │   ├── audit.py                # System-wide AuditLog entity
│   │   └── setting.py              # Dynamic HotelSetting entity
│   ├── routes/                     # Modular Blueprints
│   │   ├── __init__.py
│   │   ├── public.py               # Landing page, search, guest booking
│   │   ├── auth.py                 # Login, logout, profile
│   │   ├── auth_helpers.py         # Role-based decorators (@admin_required)
│   │   ├── dashboard.py            # Management dashboard
│   │   ├── rooms.py                # Rooms inventory & status toggles
│   │   ├── guests.py               # Guest directory & stay folios
│   │   ├── reservations.py         # Booking wizard, folios, check-in/out
│   │   ├── payments.py             # Payment ledger & receipts
│   │   ├── reports.py              # Analytics & CSV exports
│   │   ├── admin.py                # Staff, settings, audit logs
│   │   └── api.py                  # Asynchronous REST JSON endpoints
│   ├── services/                   # Transactional Business Logic
│   │   ├── __init__.py
│   │   ├── availability_service.py # Date overlap queries & capacity checks
│   │   ├── reservation_service.py  # Atomic booking, pricing, status lifecycles
│   │   ├── payment_service.py      # Payment ledger & refund processor
│   │   └── report_service.py       # Aggregations, revenue trends, KPIs
│   ├── static/
│   │   ├── css/style.css           # Luxury design system & print styles
│   │   └── js/                     # Client scripts, booking wizard, Chart.js
│   └── templates/                  # Jinja2 Luxury HTML Templates
├── database/
│   ├── mysql/                      # 15 MySQL scripts: core implementation, migrations and rollbacks
│   └── seed_data.py                # Python synthetic data seeder
├── docs/                           # Academic Documentation
│   ├── project_report.md           # Comprehensive Academic Report
│   ├── er_diagram.md               # Mermaid ER Diagram & Cardinalities
│   ├── relational_schema.md        # Relational Schema & Constraints
│   ├── actual_3nf_model.md         # Current 3NF Database Model
│   ├── api_documentation.md        # REST API Reference
│   ├── adbms_phase_mapping.md      # Academic Traceability Matrix
│   ├── mysql_setup_guide.md        # MySQL Server & Workbench Guide
│   ├── screenshot_checklist.md
│   ├── guest_roles_cancellation_and_india.md
│   └── mysql_reset_plan.md
├── instance/                       # Local ignored artifacts (not used by app startup)
├── tests/                          # Automated Pytest Suite
├── .env.example                    # Template environment configuration
├── .gitignore                      # Git ignore patterns
├── pytest.ini                      # Pytest runner configuration
├── requirements.txt                # Python package dependencies
├── run.py                          # Application entry point & CLI commands
└── README.md                       # Master Documentation
```

---

## License & Academic Disclaimer
Developed for educational and academic evaluation in Advanced Database Management Systems (ADBMS). All sample guest names, payment card simulations, and customer testimonials are synthetic and provided exclusively for demonstration purposes.
