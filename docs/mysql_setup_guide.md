# Grand Haven Hotel â€” MySQL Setup & Migration Guide
## Connecting Flask to MySQL Server & Executing Academic ADBMS Scripts

This guide configures the Grand Haven Hotel application to use **MySQL Server 8.0+** via **MySQL Workbench**. Normal startup requires a MySQL `DATABASE_URL` and does not create or seed tables. Tests use isolated in-memory SQLite.

---

## 1. Prerequisites & Verification

1. **MySQL Server 8.0+** installed and running on `localhost:3306`.
   - Verify service in Windows PowerShell:
     ```powershell
     Get-Service -Name MySQL*
     ```
   - Or test client connection:
     ```bash
     mysql -u root -p -e "SELECT VERSION();"
     ```
2. **MySQL Workbench** installed for graphical database inspection, query plan visualization, and script execution.

---

## 2. Executing MySQL Scripts in Ordered Sequence

The active `hotelreservationdb` already contains application and legacy records. Do not run setup or demonstration scripts against it until the backup, restore, migration review, and explicit approval steps in `docs/mysql_reset_plan.md` are complete. The all-script verification in this project was performed only on a disposable schema.

For a new empty schema, normal application bootstrap is limited to scripts `01_Create_Database_Tables.sql` and `
`. Scripts 03 and 10 modify data and script 10 commits demonstration bookings. Scripts 05–08 create or replace views, routines, functions, and triggers. Scripts 04, 09, and 11 are query/performance/integrity demonstrations. Review each script before running it on any database containing valuable data.

Open **MySQL Workbench**, connect to your local MySQL instance, and use the following order only on a disposable teaching database or an approved replacement schema:

| Step | Script File | Execution Purpose |
| :---: | :--- | :--- |
| **1** | `01_Create_Database_Tables.sql` | Creates database `hotelreservationdb` and all 15 tables with PKs, FKs, and constraints. |
| **2** | `02_Insert_Sample_Data.sql` | Seeds realistic demo records (roles, staff, room types, rooms, guests, bookings, payments). |
| **3** | `03_data_cleaning_and_basic_queries.sql` | Demonstrates duplicate detection, NULL handling, and aggregate grouping queries. |
| **4** | `04_advanced_joins_and_subqueries.sql` | Demonstrates multi-table joins, scalar subqueries, and `EXISTS`/`NOT EXISTS` set predicates. |
| **5** | `05_views.sql` | Compiles 5 production database views (`vw_reservation_details`, `vw_occupancy_summary`, etc.). |
| **6** | `06_stored_procedures.sql` | Compiles stored procedures (`sp_create_reservation`, `sp_cancel_reservation`, etc.). |
| **7** | `07_stored_functions.sql` | Compiles deterministic functions (`fn_calculate_nights`, `fn_calculate_outstanding_balance`). |
| **8** | `08_triggers.sql` | Installs automated audit triggers and double-booking prevention guards. |
| **9** | `09_query_execution_and_explain.sql` | Executes `EXPLAIN` and `EXPLAIN ANALYZE` index usage performance comparisons. |
| **10**| `10_transactions_and_acid.sql` | Demonstrates atomic transactions, `COMMIT`, `ROLLBACK`, and `SAVEPOINT` partial recovery. |
| **11**| `11_integrity_validator.sql` | Runs comprehensive database integrity health check auditing all 6 business invariants. |

---

## 3. Configuring Flask for MySQL Connectivity

1. Copy `.env.example` to `.env`.
2. Set `DATABASE_URL` to your local MySQL database credentials:

```ini
# MySQL Server Configuration:
DATABASE_URL=mysql+pymysql://<DB_USER>:<DB_PASSWORD>@localhost:3306/hotelreservationdb
```
*(Replace `root` and `YourPassword` with your local MySQL credentials).*

3. Verify PyMySQL driver:
   The virtual environment already includes `PyMySQL==1.1.1` and `cryptography==42.0.8` (required for MySQL 8's `caching_sha2_password` authentication).

4. Launch the application:
   ```powershell
   .\.venv\Scripts\python.exe run.py
   ```
   The Flask application will connect directly to the MySQL database. All web operations (searching rooms, booking, check-in, check-out, recording payments) will execute directly against MySQL Server.

---

## 4. Verification in MySQL Workbench

After performing actions in the web application (e.g. creating a booking at `http://localhost:5000/reservations/create`):
1. In MySQL Workbench, execute:
   ```sql
   USE hotelreservationdb;
   SELECT * FROM vw_reservation_details ORDER BY booked_at DESC LIMIT 5;
   ```
2. Verify that the new reservation appears in Workbench with matching confirmation number, room allocation, and financial balances.
3. Check the audit history:
   ```sql
   SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5;
   ```

---

## 5. Active database reset and recovery

Follow `docs/mysql_reset_plan.md`. In short: stop writers, export the entire schema including routines/triggers/events, verify the export, restore it into a scratch database, review legacy records, and obtain explicit approval before replacing `hotelreservationdb`. No reset has been run.

## 6. Architectural Differences: SQLite vs MySQL Server

| Feature | SQLite (Development) | MySQL Server 8.0 (Academic & Production) |
| :--- | :--- | :--- |
| **Architecture** | Serverless, single local file | Client-server architecture with dedicated daemon |
| **Concurrency & Locking** | Database-level lock (serialized writers) | Row-level locking (MVCC), Next-Key locking, `FOR UPDATE` |
| **Stored Procedures / Functions** | Not natively supported | Fully supported (`DELIMITER $$`, procedural language) |
| **Triggers** | Basic row triggers only | Full AFTER/BEFORE triggers with `SIGNAL SQLSTATE` |
| **Query Plans** | Basic `EXPLAIN QUERY PLAN` | Advanced `EXPLAIN`, JSON formats, `EXPLAIN ANALYZE` |
| **Data Types** | Dynamic manifest typing | Strict static types (`DECIMAL(10,2)`, `DATE`, `DATETIME`, `ENUM`) |
