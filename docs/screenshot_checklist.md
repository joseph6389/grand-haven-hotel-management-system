# Grand Haven Hotel — Academic Report Screenshot Checklist
## ADBMS Project Evaluation & Demonstration Verification Guide

Capture the following screenshots to compile your final academic report and presentation slides.

---

## 1. Web Application Interfaces

- [ ] **Screenshot 1: Public Homepage (`/`)**
  - Hero section with luxury hotel branding and navigation.
  - Live availability search widget (Check-in, Check-out, Guests).
- [ ] **Screenshot 2: Accommodations Showcase (`/#roomTypes`)**
  - Featured suite cards with pricing, bed configuration, and amenity badges.
- [ ] **Screenshot 3: Live Availability Search Results (`/search-availability`)**
  - Search results matching queried dates.
  - Price breakdown card and "Book Room" modal.
- [ ] **Screenshot 4: Guest Booking Confirmation (`/confirmation/<conf_number>`)**
  - Official booking confirmation slip with unique confirmation number.
- [ ] **Screenshot 5: Staff Login Portal (`/login`)**
  - Login card with show/hide password toggle and demo credentials helper card.
- [ ] **Screenshot 6: Executive Management Dashboard (`/dashboard`)**
  - Top 8 KPI metric cards (Available Rooms, Occupied Rooms, Monthly Revenue, etc.).
  - Chart.js Monthly Revenue line chart and Status Distribution doughnut chart.
  - Today's Arrivals and Departures tables.
- [ ] **Screenshot 7: Room Inventory Management (`/rooms`)**
  - Status pill filter badges (Total, Operational, Maintenance, Out of Order).
  - Room directory table with "Manage" dropdown actions.
  - "Add Room Unit" modal dialog.
- [ ] **Screenshot 8: Guest Directory & Profiles (`/guests` and `/guests/<id>`)**
  - Guest directory with search bar.
  - Guest detail folio showing personal details and reservation history table.
- [ ] **Screenshot 9: Reservation Wizard (`/reservations/create`)**
  - Multi-step booking form.
  - Live available rooms fetched asynchronously from `/api/available-rooms`.
  - Dynamic price quotation box.
- [ ] **Screenshot 10: Reservation Folio Details (`/reservations/<id>`)**
  - Full folio overview with guest details, stay schedule, and room allocation table.
  - Status transition action buttons (Check-In, Check-Out, Cancel).
  - Audit trail of status history.
- [ ] **Screenshot 11: Luxury Printable Booking Voucher (`/reservations/<id>/voucher`)**
  - Print-ready voucher with hotel crest, booking details, and barcode mockup.
- [ ] **Screenshot 12: Payments Ledger & Printable Receipt (`/payments` and `/payments/<id>/receipt`)**
  - Financial ledger table with summary cards.
  - Official payment receipt.
- [ ] **Screenshot 13: Financial & Occupancy Analytics (`/reports`)**
  - Performance analytics by suite type.
  - Open folios alert table and CSV export buttons.
- [ ] **Screenshot 14: Staff & Role Management (`/admin/users`)**
  - Staff user table with clearance roles and activation toggle.
- [ ] **Screenshot 15: Hotel Settings & Audit Trail (`/admin/settings` and `/admin/audit-logs`)**
  - Dynamic property configuration form.
  - System audit logs table tracking mutations.

---

## 2. MySQL Workbench & Database Execution

- [ ] **Screenshot 16: DDL Execution & Table Verification**
  - Output of `SHOW TABLES;` in MySQL Workbench displaying all 15 tables.
- [ ] **Screenshot 17: Relational Schema Inspection**
  - MySQL Workbench EER Diagram generated via *Database &rarr; Reverse Engineer*.
- [ ] **Screenshot 18: Advanced Joins Execution**
  - Query results of `04_advanced_joins_and_subqueries.sql`.
- [ ] **Screenshot 19: Database Views Inspection**
  - Output of `SELECT * FROM vw_reservation_details;` and `SELECT * FROM vw_occupancy_summary;`.
- [ ] **Screenshot 20: Stored Procedure & Function Execution**
  - Execution of `CALL sp_create_reservation(...)` or `SELECT fn_calculate_nights(...);`.
- [ ] **Screenshot 21: Trigger Audit Verification**
  - Execution showing automatic row insertion into `reservation_status_history` after a reservation status update.
- [ ] **Screenshot 22: Query Execution Plan (EXPLAIN)**
  - Graphical query plan and tabular EXPLAIN output showing index utilization (`type: const` vs `type: ALL`).
- [ ] **Screenshot 23: Transaction & SAVEPOINT Demonstration**
  - Output of `10_transactions_and_acid.sql` demonstrating `SAVEPOINT` and `ROLLBACK TO SAVEPOINT`.
- [ ] **Screenshot 24: Database Integrity Validator**
  - Execution of `11_integrity_validator.sql` showing zero integrity violations.
- [ ] **Screenshot 25: Automated Test Suite**
  - Terminal output showing all 26 automated tests passing with `pytest`.
