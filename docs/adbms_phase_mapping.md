# Grand Haven Hotel — ADBMS Academic Phase Mapping Matrix
## Complete Phase I through Phase IV Traceability Guide

This document maps all theoretical and practical deliverables required for the **Advanced Database Management Systems (ADBMS)** academic evaluation to the implementation files in this repository.

---

## Academic Phase Overview & Deliverable Matrix

| ADBMS Phase | Academic Requirement | Implemented Artifact / Script / Source File | Validation Method |
| :--- | :--- | :--- | :--- |
| **PHASE I** | **Problem Statement, Scope & Objectives** | `docs/project_report.md` | Theoretical & Academic Review |
| **PHASE I** | **Entity-Relationship (ER) Diagram** | `docs/er_diag
ram.md` | Renderable Mermaid syntax with cardinalities |
| **PHASE I** | **Relational Schema & Constraints** | `docs/relational_schema.md` | Formal relational notations and data dictionary |
| **PHASE I** | **Functional Dependencies & Normalization** | `docs/normalization.md` | Mathematical breakdown: UNF &rarr; 1NF &rarr; 2NF &rarr; 3NF |
| **PHASE I** | **ORM Models & Relationships** | `app/models/*.py` | SQLAlchemy ORM Models with Decimal-safe typing |
| **PHASE II**| **MySQL Database Creation (DDL)** | `database/mysql/01_Create_Database_Tables.sql` | Executable in MySQL Server & Workbench |
| **PHASE II**| **Synthetic Dataset (DML)** | `database/mysql/02_Insert_Sample_Data.sql`<br>`database/seed_data.py` | Python seeder + pure MySQL script |
| **PHASE II**| **Data Cleaning & Standardization** | `database/mysql/03_data_cleaning_and_basic_queries.sql` | Duplicate email detection, TRIM, COALESCE |
| **PHASE II**| **Basic DML, Aggregates & Grouping** | `database/mysql/03_data_cleaning_and_basic_queries.sql` | SELECT, WHERE, ORDER BY, COUNT, SUM, AVG, GROUP BY, HAVING |
| **PHASE III**| **Advanced SQL Joins (INNER, LEFT, Multi)** | `database/mysql/04_advanced_joins_and_subqueries.sql` | Executable join queries across 5 entities |
| **PHASE III**| **Complex Subqueries (Scalar, Correlated)** | `database/mysql/04_advanced_joins_and_subqueries.sql` | IN, EXISTS, NOT EXISTS set predicates |
| **PHASE III**| **Database Views** | `database/mysql/05_views.sql` | 5 operational views (Reservations, Revenue, Occupancy) |
| **PHASE III**| **Stored Procedures** | `database/mysql/06_stored_procedures.sql` | `sp_create_reservation`, `sp_cancel_reservation`, `sp_check_in_guest`, `sp_check_out_guest`, `sp_get_available_rooms` |
| **PHASE III**| **Stored Functions** | `database/mysql/07_stored_functions.sql` | `fn_calculate_nights`, `fn_calculate_outstanding_balance`, `fn_calculate_tax` |
| **PHASE III**| **Database Triggers** | `database/mysql/08_triggers.sql` | `trg_validate_reservation_transition`, `trg_payment_update_reservation`, `trg_prevent_double_booking` |
| **PHASE III**| **Query Execution Plans (EXPLAIN)** | `database/mysql/09_query_execution_and_explain.sql` | EXPLAIN and EXPLAIN ANALYZE index usage comparison |
| **PHASE IV**| **Transactions (COMMIT & ROLLBACK)** | `database/mysql/10_transactions_and_acid.sql`<br>`app/services/reservation_service.py` | Atomic booking transactions with automatic rollback |
| **PHASE IV**| **SAVEPOINT Demonstration** | `database/mysql/10_transactions_and_acid.sql` | Partial rollback restoring state to savepoint |
| **PHASE IV**| **ACID Analysis & Concurrency Levels** | `database/mysql/10_transactions_and_acid.sql`<br>`docs/project_report.md` | Analysis of Dirty, Non-repeatable, Phantom reads and InnoDB isolation levels |
| **PHASE IV**| **Database Integrity Validator** | `database/mysql/11_integrity_validator.sql` | Comprehensive audit script checking 6 integrity rules |
| **TESTS**   | **Automated Python Test Suite** | `tests/test_*.py` (22 currently collected tests) | `pytest` test runner (latest verified result recorded in audit report) |

---

## Dialect & Concurrency Architecture Notes

### SQLite (Test Environment):
- **Concurrency Model**: SQLite utilizes file-level database locking. Concurrency is limited to serialized writes; row-level locks like `FOR UPDATE` are ignored.
- **Transactions**: SQLAlchemy ORM manages transactional session boundaries (`session.commit()` and `session.rollback()`) identically in SQLite and MySQL.
- **Triggers & Procedures**: SQLite does not support MySQL stored procedures, complex user functions, or `EXPLAIN ANALYZE`. Hence, core application logic resides in Python services (`app/services/`), while dedicated MySQL scripts provide the native stored procedures for MySQL Server execution.

### MySQL (Final Academic Evaluation Environment):
- **Engine**: InnoDB (Default in MySQL 8.0+).
- **Concurrency Model**: Multi-Version Concurrency Control (MVCC) with row-level locks, gap locks, and next-key locking.
- **Locking Statements**: `SELECT ... FOR UPDATE` row locks prevent race conditions during high-concurrency booking attempts.
- **Financial Precision**: `DECIMAL(10, 2)` columns prevent binary floating-point drift.
