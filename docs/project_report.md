# Grand Haven Hotel — Hotel Reservation Management System
## Advanced Database Management Systems (ADBMS) Academic Evaluation Report

**Institution:** Department of Computer Science & Engineering
**Course:** Advanced Database Management Systems (ADBMS)
**Project Title:** Grand Haven Hotel — Full-Stack Hotel Reservation Management System
**Author:** Pair-Programmed with Antigravity AI
**Academic Year:** 2026

---

## 1. Executive Summary

The **Grand Haven Hotel Reservation Management System** is an full-stack web application and advanced relational database implementation. Developed to satisfy the rigorous academic standards of Advanced Database Management Systems (ADBMS), this project demonstrates mastery across data modelling, normalization up to 3NF, advanced relational algebra, multi-table joins, subqueries, database views, stored procedures, stored functions, database triggers, transaction control with partial rollback (`SAVEPOINT`), concurrency control, and index optimization.

The system features an aesthetic front-of-house public booking portal and a robust back-of-house management portal built on **Python 3**, **Flask**, **SQLAlchemy ORM & Core**, **Bootstrap 5**, **JavaScript ES6+**, and **Chart.js**, backed by an environment-driven database architecture using **MySQL Server 8.0+** for normal operation and isolated in-memory SQLite for automated tests.

---

## 2. Problem Statement & Project Objectives

### 2.1 Problem Statement
Hospitality properties often struggle with fragmented reservation systems that suffer from:
1. **Concurrency Failures**: Simultaneous reservation requests resulting in duplicate room allocations (double bookings).
2. **Data Anomalies & Financial Drift**: Improper normalization causing insertion, update, and deletion anomalies, compounded by binary floating-point rounding errors in billing calculations.
3. **Disjointed Operational Visibility**: Inability to synthesize real-time occupancy metrics, front-desk arrivals/departures, and multi-month revenue trends into actionable operational insights.
4. **Weak Integrity Enforcement**: Relying solely on client-side browsers for validation, leaving databases vulnerable to invalid date ranges, orphaned records, and untracked status transitions.

### 2.2 Project Objectives
1. **Architect a 3NF Relational Database**: Eliminate data redundancy and partial/transitive functional dependencies across 15 normalized tables.
2. **Enforce Transactional ACID Guarantees**: Implement atomic reservation workflows where room allocation, status progression, and financial transactions succeed as a single unit or cleanly roll back.
3. **Implement Advanced SQL Constructs**: Engineer native MySQL views, stored procedures with row-level locking (`SELECT ... FOR UPDATE`), deterministic stored functions, and automated database audit triggers.
4. **Deliver a Luxury Full-Stack Experience**: Provide a luxury hospitality website with real-time room availability searching, interactive multi-step booking, executive KPI dashboards, and printable receipts and vouchers.
5. **Verify through Automated Testing**: Formulate comprehensive test suites covering security, room inventory, double-booking prevention, payment ledger synchronization, and transaction rollbacks.

---

## 3. Technology Stack & System Architecture

```text
+-----------------------------------------------------------------------------------+
|                            PRESENTATION LAYER (UI/UX)                             |
|  HTML5 & CSS3 (Custom Luxury Palette: Warm Ivory #FAF8F5, Champagne Gold #C5A880) |
|  Bootstrap 5.3 & Bootstrap Icons 1.11 & Modern Typography (Outfit, Playfair Serif)|
|  Vanilla JavaScript ES6+ & Fetch API & Chart.js 4.4 Data Visualizations           |
+-----------------------------------------------------------------------------------+
                                         │
                                   HTTP / REST JSON
                                         │
+-----------------------------------------------------------------------------------+
|                        APPLICATION LAYER (FLASK BACKEND)                          |
|  Python 3.13 & Flask Application Factory Architecture                             |
|  Flask Blueprints: Public, Auth, Dashboard, Rooms, Guests, Reservations,          |
|                    Payments, Reports, Admin, API                                  |
|  Security & Auth: Flask-Login, Werkzeug Password Hashing (scrypt), Flask-WTF CSRF |
|  Service Layer: AvailabilityService, ReservationService, PaymentService, Reports  |
+-----------------------------------------------------------------------------------+
                                         │
                              SQLAlchemy 2.0 ORM & Core
                                         │
+-----------------------------------------------------------------------------------+
|                             DATABASE STORAGE LAYER                                |
|  Automated Test Database: Isolated SQLite 3 (not used for normal application operation)          |
|  Academic / Production: MySQL Server 8.0+ (InnoDB Engine, Row Locks, MVCC)        |
|  Native Database Scripts: 11 MySQL DDL, DML, View, Procedure, Function, Trigger,  |
|                           Transaction, EXPLAIN, and Validator Scripts             |
+-----------------------------------------------------------------------------------+
```

---

## 4. ADBMS Academic Phase Breakdown

### Phase I: Data Modelling & Dataset Design
- **Entities Formulated**: 15 distinct relational entities covering security (`roles`, `users`), inventory (`room_types`, `rooms`, `amenities`, `room_amenities`), CRM (`guests`), operations (`reservations`, `reservation_rooms`, `reservation_status_history`), finance (`payments`, `services`, `reservation_services`), system audit (`audit_logs`), and property parameters (`hotel_settings`).
- **Data Dictionary**: Fixed-point `DECIMAL(10, 2)` monetary representations; `DATE` and `DATETIME` temporal typing; foreign key actions with `RESTRICT`, `CASCADE`, and `SET NULL`.
- **Normalization**: Rigorous step-by-step reduction from Unnormalized Form (UNF) through First Normal Form (1NF), Second Normal Form (2NF), and Third Normal Form (3NF).

### Phase II: Database Creation & Data Preparation
- **DDL Execution**: Clean table creation scripts with explicit primary keys, composite unique constraints, check constraints (`chk_res_dates`), and secondary B-Tree indexes.
- **Synthetic Data**: Rich, multi-month operational dataset containing historical completed stays, currently checked-in guests, future confirmed reservations, cancelled bookings with reasons, and multi-method payments.
- **Data Cleaning**: SQL scripts showcasing duplicate detection queries, NULL handling via `COALESCE` and `IFNULL`, string normalization via `TRIM`, safe updates, and safe test data deletion.

### Phase III: Advanced SQL Operations
- **Joins**: Demonstrations of `INNER JOIN`, `LEFT JOIN`, and multi-table 5-way joins linking guests, reservations, rooms, suite types, and payments.
- **Subqueries**: Scalar subqueries comparing individual bookings against portfolio averages, correlated subqueries computing live occupancy counts per room, and set membership queries using `IN`, `EXISTS`, and `NOT EXISTS`.
- **Database Views**: 5 production views: `vw_reservation_details`, `vw_room_availability`, `vw_monthly_revenue`, `vw_guest_booking_history`, and `vw_occupancy_summary`.
- **Stored Procedures**: Procedural routines featuring exception handlers (`EXIT HANDLER FOR SQLEXCEPTION`), output parameters, and transactional commits: `sp_create_reservation`, `sp_cancel_reservation`, `sp_check_in_guest`, `sp_check_out_guest`, and `sp_get_available_rooms`.
- **Stored Functions**: Deterministic routines: `fn_calculate_nights`, `fn_calculate_outstanding_balance`, and `fn_calculate_tax`.
- **Triggers**: Lifecycle validation trigger `trg_validate_reservation_transition`, ledger synchronization trigger `trg_payment_update_reservation`, and physical double-booking barrier `trg_prevent_double_booking`.
- **Query Optimization**: Query plan analysis comparing unique index scans (`type: const`) against full table scans (`type: ALL`) using `EXPLAIN` and `EXPLAIN ANALYZE`.

### Phase IV: Data Integrity, Transactions & ACID Handling
- **Atomic Operations**: Step-by-step transaction handling ensuring master reservation insertion, physical room allocation, status logging, and payment receipt succeed atomically.
- **Partial Rollback via SAVEPOINT**: Demonstrated recovery where secondary add-on failures roll back to `SAVEPOINT room_booking_confirmed` without terminating the core room reservation.
- **Concurrency & Isolation**: Comprehensive academic analysis of Dirty Reads, Non-Repeatable Reads, Phantom Reads, and Lost Updates across MySQL InnoDB's four isolation levels (`READ UNCOMMITTED`, `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`).
- **Integrity Validation Script**: Execution of `11_integrity_validator.sql` testing 6 automated audit rules across the database.

---

## 5. Automated Testing & Verification Results

The latest audit run collected and passed 26 tests under Python 3.13.5 and pytest 8.2.2. See `docs/final_audit.md` for exact commands, warning details, MySQL verification, and limitations.

---

## 6. Conclusion

The Grand Haven Hotel Reservation Management System successfully bridges theoretical database design and practical full-stack software engineering. By combining rigorous 3NF schema modelling, decimal monetary precision, atomic transaction boundaries, and advanced MySQL operations with an elegant, responsive user experience, the system provides a substantial academic implementation. The supplied workspace did not include the original grading rubric, and the active database reset and live write-path checks remain approval-gated.
