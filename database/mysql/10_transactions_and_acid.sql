-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase IV: Transactions, ACID Integrity, Concurrency, and SAVEPOINT
-- Target: MySQL Server 8.0+ (InnoDB Engine)
-- ============================================================================

USE hotelreservationdb;

-- ============================================================================
-- 1. TRANSACTION EXAMPLE: COMPLETE COMMIT WORKFLOW
-- Atomic booking creation: All steps succeed and are committed permanently
-- ============================================================================

START TRANSACTION;

-- Step 1: Create master reservation record
INSERT INTO reservations (
    confirmation_number, guest_id, check_in_date, check_out_date,
    adults_count, children_count, tax_amount, discount_amount,
    status, special_requests, created_by_id
) VALUES (
    'GH-TXN-DEMO-001', 1, '2026-11-01', '2026-11-04',
    2, 0, 64.80, 0.00,
    'confirmed', 'Transaction ACID demonstration booking', 1
);

SET @demo_res_id = LAST_INSERT_ID();

-- Step 2: Allocate physical room unit (Room 102)
INSERT INTO reservation_rooms (
    reservation_id, room_id, nightly_rate, nights
) VALUES (
    @demo_res_id, 2, 180.00, 3
);

-- Step 3: Record advance payment
INSERT INTO payments (
    reservation_id, payment_reference, amount, currency,
    payment_method, payment_status, transaction_reference, notes, processed_by_id
) VALUES (
    @demo_res_id, 'PAY-DEMO-001', 604.80, 'INR',
    'credit_card', 'paid', 'SIM-TXN-ACID-COMMIT', 'Advance deposit committed', 1
);

-- Step 4: Record status history
INSERT INTO reservation_status_history (
    reservation_id, previous_status, new_status, changed_by_id, reason
) VALUES (
    @demo_res_id, NULL, 'confirmed', 1, 'Atomic COMMIT demo'
);

-- Commit all changes atomically
COMMIT;

-- Verify changes are committed
SELECT r.confirmation_number,
       GREATEST(0.00,COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00)+r.tax_amount-r.discount_amount) AS total_amount,
       COALESCE((SELECT SUM(p.amount-p.refunded_amount) FROM payments p WHERE p.reservation_id=r.id AND p.payment_status IN ('paid','partially_refunded')),0.00) AS paid_amount,
       r.status
FROM reservations r WHERE r.confirmation_number = 'GH-TXN-DEMO-001';


-- ============================================================================
-- 2. TRANSACTION EXAMPLE: COMPLETE ROLLBACK WORKFLOW
-- Demonstrates atomic failure: If an invalid operation occurs, ALL changes are undone
-- ============================================================================

START TRANSACTION;

-- Insert a test reservation
INSERT INTO reservations (
    confirmation_number, guest_id, check_in_date, check_out_date,
    adults_count, children_count, tax_amount, discount_amount,
    status, created_by_id
) VALUES (
    'GH-TXN-ROLLBACK-002', 1, '2026-11-10', '2026-11-12',
    2, 0, 43.20, 0.00,
    'confirmed', 1
);

-- Simulate a business validation or constraint failure (e.g. invalid payment amount)
-- Intentionally trigger ROLLBACK
ROLLBACK;

-- Verify that the test record does NOT exist in the database
SELECT COUNT(*) AS should_be_zero
FROM reservations
WHERE confirmation_number = 'GH-TXN-ROLLBACK-002';


-- ============================================================================
-- 3. TRANSACTION EXAMPLE: SAVEPOINT AND PARTIAL ROLLBACK
-- Scenario: The room booking succeeds. An optional add-on service fails.
-- We rollback ONLY to the savepoint, preserving the room reservation!
-- ============================================================================

START TRANSACTION;

-- Step 1: Create reservation
INSERT INTO reservations (
    confirmation_number, guest_id, check_in_date, check_out_date,
    adults_count, children_count, tax_amount, discount_amount,
    status, created_by_id
) VALUES (
    'GH-TXN-SAVEPOINT-003', 2, '2026-11-15', '2026-11-18',
    2, 0, 93.60, 0.00,
    'confirmed', 1
);

SET @sp_res_id = LAST_INSERT_ID();

INSERT INTO reservation_rooms (
    reservation_id, room_id, nightly_rate, nights
) VALUES (
    @sp_res_id, 4, 260.00, 3
);

-- ESTABLISH SAVEPOINT after core room allocation succeeds
SAVEPOINT room_booking_confirmed;

-- Step 2: Attempt to attach an add-on service
-- Suppose an application issue occurs here (e.g., requested yacht charter is unavailable)
-- We roll back to the savepoint:
ROLLBACK TO SAVEPOINT room_booking_confirmed;

-- Step 3: Complete and commit the core reservation without the failed add-on
COMMIT;

-- Verify that the core reservation was preserved despite the partial failure:
SELECT r.confirmation_number, r.status,
       GREATEST(0.00,COALESCE((SELECT SUM(rr.nightly_rate*rr.nights) FROM reservation_rooms rr WHERE rr.reservation_id=r.id),0.00)+r.tax_amount-r.discount_amount) AS total_amount
FROM reservations r WHERE r.confirmation_number = 'GH-TXN-SAVEPOINT-003';


-- ============================================================================
-- 4. ACID PROPERTIES & INNODB CONCURRENCY ISOLATION LEVELS
-- ============================================================================

/*
ACID PROPERTIES BREAKDOWN:
-------------------------------------------------------------------------------
1. ATOMICITY:
   All operations in a reservation sequence (room allocation, payment ledger,
   status history) succeed as a single unit or completely abort (ROLLBACK).

2. CONSISTENCY:
   All constraints (chk_dates, foreign keys, unique confirmation numbers)
   are validated before and after every transaction. Invalid states are impossible.

3. ISOLATION:
   Transactions execute concurrently without interfering with one another.
   InnoDB uses Multi-Version Concurrency Control (MVCC) and row locks.

4. DURABILITY:
   Once COMMIT is returned, all mutations are written to the Write-Ahead Log
   (InnoDB redo log) and survive any subsequent power outage or server crash.

TRANSACTION ISOLATION PHENOMENA:
-------------------------------------------------------------------------------
- Dirty Read: Transaction reads uncommitted changes from another transaction.
- Non-Repeatable Read: Re-reading a row returns different data because another TX committed an UPDATE.
- Phantom Read: Re-running a range query returns new rows inserted by another committed TX.
- Lost Update: Two transactions read the same balance and overwrite each other's changes.

INNODB ISOLATION LEVELS:
-------------------------------------------------------------------------------
1. READ UNCOMMITTED: Allows dirty reads. (Not suitable for financial operations).
2. READ COMMITTED: Prevents dirty reads. Consistent reads use fresh snapshots.
3. REPEATABLE READ: Default in MySQL InnoDB. Prevents dirty & non-repeatable reads.
   Uses Next-Key Locking (record lock + gap lock) to prevent phantom reads.
4. SERIALIZABLE: Converts all plain SELECTs to SELECT ... FOR SHARE locks.
*/

-- Check current session and global transaction isolation level in MySQL:
SELECT @@GLOBAL.transaction_isolation, @@SESSION.transaction_isolation;
