# Live MySQL 3NF Migration Plan — For Review Only

**Status: not applied.** The scripts were tested against disposable MySQL schemas. `hotelreservationdb` remains on the original schema. This plan requires explicit approval before any live migration.

## Scope

Only these three active tables are affected:

| Table | Exact columns to remove | Related constraint changes |
|---|---|---|
| `reservations` | `total_nights`, `room_charges`, `total_amount`, `paid_amount` | Drop `chk_res_nights`, `chk_res_charges`, `chk_res_total` because they reference removed values. Keep `chk_res_dates`. |
| `reservation_rooms` | `subtotal` | None. Keep both FKs, the unique `(reservation_id, room_id)` key and rate/night checks. |
| `reservation_services` | `total_price` | None. Keep both FKs, quantity check and indexes. |

No table is dropped or recreated. No row is inserted, updated, deleted, settled, refunded or recreated. No new tables, columns, foreign keys, unique keys or indexes are added. All legacy/backup tables and their rows remain outside the migration scope.

The removed values remain available through ORM calculations from retained source facts: dates; room-allocation rate and nights; reservation tax and discount snapshots; payment amount/refund/status ledger; and service-line unit price/quantity. The historical rate, tax, discount and payment/refund facts remain intact.

## Preflight and expected counts

Before running DDL, run the three preflight queries at the top of `database/mysql/13_normalize_derived_reservation_values.sql`. All three must return zero. They compare the values being removed with their exact derivations. **Stop if any value is nonzero; do not run the ALTER statements.** Reconcile the unexpected difference separately before proposing a revised plan.

Fresh source counts from the audit:

| Scope/table | Before | Expected after |
|---|---:|---:|
| All 15 active tables | 291 rows | 291 rows |
| All 23 base tables, including legacy | 344 rows | 344 rows |
| `reservations` | 16 | 16 |
| `reservation_rooms` | 16 | 16 |
| `reservation_services` | 0 | 0 |
| `payments` | 12 | 12 |
| `reservation_status_history` | 16 | 16 |

No data transformation is expected. The seven reservations without status-history entries and the zero-row service-line table remain as observed.

## Backup and rollout sequence

1. Schedule a short maintenance window and stop application writers so the preflight and DDL see a stable ledger. Preserve the existing dated backup.
2. Create a new full `mysqldump` backup of `hotelreservationdb` and a source-code snapshot. Record hashes and verify the dump/archive before continuing. The audit-stage backup is at `../.audit_3nf/pre_implementation_backup_20261103_01/`; take a fresh backup immediately before any future live migration.
3. Record live counts and protected-record presence; run the three derivation preflights and require zero results.
4. Deploy the reviewed application version and migration SQL during maintenance. Run `database/mysql/13_normalize_derived_reservation_values.sql` against `hotelreservationdb`. The script applies only the listed `ALTER TABLE` statements after the preflight result is accepted.
5. Verify the six columns are absent; the three named checks are absent; all other PK/FK/unique/index/check constraints remain; table counts match the table above; protected IDs remain present; and ORM-derived totals match the pre-migration values.
6. Run the approved MySQL smoke checks and application regression checks. Reopen traffic only after they pass.

MySQL DDL is not one transaction across these ALTER statements. Use maintenance mode and the verified backup; do not treat a transaction `ROLLBACK` as a recovery strategy.

## Rollback and recovery

The tested reverse script is `database/mysql/13_rollback_derived_reservation_values.sql`. It recreates the removed columns, repopulates them from the retained facts and ledgers, restores nullability/defaults and the three checks, and preserves rows. On the disposable copy, rollback restored the original row counts and zero mismatches for all reconstructed values.

If a live post-migration check fails: keep the app in maintenance mode; run the rollback script; verify counts and reconstructed-value checks; restore the prior application version if needed; and compare against the fresh pre-migration dump. If rollback itself fails, restore the verified full backup to a separate recovery schema first and follow the database administrator’s recovery procedure. Do not overwrite the existing backup.

## Risks and compatibility

- Any external report, integration, ad-hoc SQL, or deployed app version that reads one of the six removed columns will fail until updated. The project’s active ORM, routes, services, templates, seed code and SQL examples were updated; inventory external consumers before approval.
- The preflight must remain zero. A mismatch means a stored value cannot be reconstructed exactly under the reviewed formulas; the migration must stop.
- Computed hybrid properties issue correlated SQL expressions for some filters and aggregates. Functional correctness was verified on the disposable MySQL copy; production-sized performance was not benchmarked.
- A final ORM-to-MySQL metadata comparison after explicit ORM enum declarations was blocked before execution by the environment’s automatic approval usage limit. Re-run that comparison in an approved environment before live migration.
- No live application outage duration has been measured. Use a maintenance window and verify response times before reopening traffic.

## Evidence already collected

- The source database is MySQL 8.0.46, schema `hotelreservationdb`; fresh active-table sum 291 and all-table sum 344.
- Migration preflight values were all zero on the isolated copy.
- Forward migration removed only the listed columns/checks; counts remained unchanged.
- Rollback restored the old columns and exact derived values; the forward migration was then reapplied to the copy.
- The full automated suite passed 72 tests; MySQL DDL/seed, read-only queries/views/validator/explain, routines, triggers and ACID examples succeeded on disposable schemas.
- No live migration has been performed.
