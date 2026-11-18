# Active MySQL Reset Plan — Approval Required

> **Status as of 2026-10-27:** No reset is recommended or authorized. Preserve all current tables and records. The active database was inspected read-only; no backup/restore was performed and no live schema or row changes were made. The current need is an additive account/cancellation migration, documented separately, which also requires explicit review/approval before it is applied. Do not use the replacement procedure below for the current feature rollout.

## Current target and scope

Target: `hotelreservationdb`, the database selected by the local `.env` and the canonical target of the revised scripts.

Read-only metadata inspection found 23 base tables:

- 15 current application tables: `amenities`, `audit_logs`, `guests`, `hotel_settings`, `payments`, `reservation_rooms`, `reservation_services`, `reservation_status_history`, `reservations`, `roles`, `room_amenities`, `room_types`, `rooms`, `services`, `users`.
- 8 legacy/backup tables with existing rows: `app_user_backup_20261020` (5), `check_in` (8), `check_out` (2), `guest` (9), `payment` (8), `reservation` (9), `room` (8), `room_type` (4).

The 15 ORM tables also contain data. Their exact row counts are recorded in `docs/final_audit.md`. No view, trigger, or stored routine currently exists in the active schema. The eight legacy tables contain records, and no automatic migration/drop is safe based on names alone.

## Proposed replacement

After explicit approval, replace the entire `hotelreservationdb` schema with the canonical 15-table application schema and synthetic seed data. This would remove all 23 current tables and every row in them, including legacy records. It would also replace any future object created in that schema. MySQL system schemas and other databases are outside scope.

Canonical setup files are `database/mysql/01_Create_Database_Tables.sql` then `02_Insert_Sample_Data.sql`. Scripts 03 and 10 include data changes and committed demonstration bookings; they are not bootstrap scripts. Scripts 05–08 install/replace optional academic views, routines, functions, and triggers. Scripts 04, 09, and 11 are query/verification demonstrations. All 11 were tested only in an isolated disposable schema.

## Required safety sequence

1. Stop the Flask application and any other writers to `hotelreservationdb`.
2. Export the complete database with MySQL Workbench, including all tables and rows, triggers, routines, and events. Save the export outside the project archive in a protected location.
3. Check the export file exists, is non-empty, and reports all current tables and expected row totals. Do not proceed if any object or row set is missing.
4. Restore the export into a separately named scratch database. Verify restored table counts, selected row counts, constraints, and that the application can connect to the restored copy. This restore verification has not yet been performed.
5. Review whether any legacy rows must be migrated. No field mapping or migration has been prepared; approval to reset would mean discarding them.
6. Obtain explicit approval for the destructive reset after reviewing this plan and the backup/restore evidence.
7. Only then drop and recreate `hotelreservationdb`, execute scripts 01 and 02, and install the optional academic objects from scripts 05–08 if desired.
8. Verify all 15 tables, key foreign keys/check constraints, seed counts, the six-rule integrity validator, and read-only application routes.
9. If any check fails, stop the application and restore the verified backup into `hotelreservationdb`; rerun the same validation before reopening writes.

No step above has been run against the active schema. No backup or restore has been performed yet.
