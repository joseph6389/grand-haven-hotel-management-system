# Grand Haven Hotel — Verified 3NF Model

## Scope and evidence

This document describes the revised active SQLAlchemy/MySQL design. The MySQL 8.0.46 source schema was inspected read-only; a full database dump and source snapshot were verified before code changes. The migration was applied, rolled back, and reapplied only to a separate disposable MySQL copy. A second empty MySQL schema validated the revised canonical DDL, seed data, views, stored routines, triggers, query examples, and ACID examples. The live `hotelreservationdb` was not migrated.

The active model has 15 tables. A fresh source read counted **291 rows** across those tables and **344 rows** across all 23 live base tables, including legacy/backup tables. `reservation_status_history` has 16 rows; seven reservations have no history row. `reservation_services` has zero rows. No rows were added to address either observation. Seed files and project comments label the demonstration records synthetic; no external dataset citation is present.

## 1NF, 2NF and 3NF

**1NF** requires a row identifier and scalar values without repeating groups. The active schema stores individual rooms, payments, status events, amenities and service lines as rows. Room/amenity, reservation/room and reservation/service associations are represented as separate relations. Free-form text can contain arbitrary prose, so atomicity inside notes is not verifiable from the column type alone.

**2NF** requires 1NF and no non-key attribute dependent on only part of a composite candidate key. All active relations have a single-column primary key except `room_amenities`; that junction has only its two-column primary key and no non-key attributes. `reservation_rooms` also has a unique `(reservation_id, room_id)` alternate key; its rate and nights describe that full allocation pair. No partial dependency is identified under these keys.

**3NF** requires 2NF and no non-key attribute transitively dependent on a candidate key. The verified migration removes persisted values that were deterministically derivable. The application exposes those values as calculated ORM properties instead:

- `Reservation.total_nights` = date difference between `check_in_date` and `check_out_date`.
- `ReservationRoom.subtotal` = historical `nightly_rate × nights`.
- `ReservationService.total_price` = historical `unit_price × quantity`.
- `Reservation.room_charges` = sum of its reservation-room snapshot lines.
- `Reservation.total_amount` = `max(0, room_charges + tax_amount − discount_amount)`.
- `Reservation.paid_amount` = sum of net payments with `paid` or `partially_refunded` status.

The historical inputs remain stored: allocated nightly rates and nights, service unit prices and quantities, tax and discount amounts, and payment/refund amounts and statuses. These are transaction facts/snapshots, not current catalogue prices. Tax and discount are retained because the rate/policy that produced them is not otherwise stored on a reservation. The app’s hybrid properties also provide SQL expressions for supported filtering and aggregation; there is no persisted duplicate total.

### Active-table dependency assessment

`PK` is the primary key; `AK` is an alternate/candidate key evidenced by a unique constraint. A listed FD is asserted only where the schema or business rule supports it. Foreign keys alone do not establish that the referenced value determines unrelated data.

| Table | PK and candidate/alternate keys | Functional dependencies and assessment |
|---|---|---|
| `roles` | `id`; AK `name` | `id → name, description, created_at`; `name → id, description, created_at`. No non-key determinant; 1NF/2NF/3NF. |
| `users` | `id`; AKs `username`, `email`; nullable unique `guest_profile_id` is an alternate key only when populated | Each non-null candidate key identifies the account row. `role_id` does not determine role description within `users`; role facts live in `roles`. No partial/transitive dependency; 1NF/2NF/3NF. |
| `guests` | `id`; AK `email` | `id →` all guest columns; `email → id` and therefore all guest columns. Names, phone and address are not assumed unique. 1NF/2NF/3NF. |
| `room_types` | `id`; AK `code` | `id →` all room-type columns; `code → id` and all room-type columns. 1NF/2NF/3NF. |
| `rooms` | `id`; AK `room_number` | `id →` room attributes; `room_number → id` and room attributes. Room-type descriptions are not duplicated in `rooms`; they are reached through `room_type_id`. 1NF/2NF/3NF. |
| `amenities` | `id`; AK `name` | `id →` all amenity columns; `name → id` and all amenity columns. 1NF/2NF/3NF. |
| `room_amenities` | Composite PK/AK `(room_id, amenity_id)` | The pair identifies one association. There are no non-key attributes and therefore no partial/transitive dependency; 1NF/2NF/3NF. |
| `reservations` | `id`; AK `confirmation_number` | Either candidate key determines guest, dates, occupancy, tax/discount snapshots, status and audit fields. Nights, room charges, total, and paid amounts are no longer stored; they derive from dates, room allocations and payments. 1NF/2NF/3NF. |
| `reservation_rooms` | `id`; AK `(reservation_id, room_id)` | The row key determines the reservation/room pair and historical `nightly_rate`, `nights`, `created_at`. `subtotal` has been removed because the business rule makes it `nightly_rate × nights`. No partial/transitive dependency; 1NF/2NF/3NF. |
| `payments` | `id`; AK `payment_reference` | Each key determines its payment amount, currency, method/status, refund amount, references, processor and timestamp. `payment_status` remains an independent lifecycle fact: a failed payment is not inferable from amount/refund values alone. 1NF/2NF/3NF. |
| `reservation_status_history` | `id` | `id →` reservation, transition values, actor/request context and timestamp. No alternate event key is asserted; multiple events may share timestamps. 1NF/2NF/3NF. |
| `services` | `id`; AK `name` | `id →` service catalogue attributes; `name → id` and attributes. 1NF/2NF/3NF. |
| `reservation_services` | `id` | The line key determines reservation, service, historical `unit_price`, `quantity`, service date and creation time. `total_price` has been removed because `unit_price × quantity` determines it. No partial/transitive dependency; 1NF/2NF/3NF. The table currently has no rows. |
| `audit_logs` | `id` | `id →` event attributes. `entity_type/entity_id` is a polymorphic reference, not a declared FK; no target-entity FD is asserted. 1NF/2NF/3NF, with weaker referential integrity for the generic target. |
| `hotel_settings` | `id`; AK `setting_key` | `id →` setting fields; `setting_key → id, value, type, description, updated_at`. Value parsing/validity is enforced by application logic, not a relational FK. 1NF/2NF/3NF. |

### Before and after

Before the migration, the reservation row stored `total_nights`, `room_charges`, `total_amount`, and `paid_amount`; allocation rows stored `subtotal`; service lines stored `total_price`. The former fields had exact derivations or aggregate sources in other rows. The revised base relations are:

```text
RESERVATIONS(id PK, confirmation_number AK, guest_id FK, check_in_date,
             check_out_date, adults_count, children_count, tax_amount,
             discount_amount, status, special_requests, created_by_id FK?,
             created_at, updated_at)

RESERVATION_ROOMS(id PK, reservation_id FK, room_id FK, nightly_rate,
                  nights, created_at, UNIQUE(reservation_id, room_id))

RESERVATION_SERVICES(id PK, reservation_id FK, service_id FK, quantity,
                     unit_price, service_date, created_at)

PAYMENTS(id PK, reservation_id FK, payment_reference AK, amount, refunded_amount,
         currency, payment_method, payment_status, transaction_reference?,
         notes?, processed_by_id FK?, created_at)
```

The ORM properties retain the application’s read interface and compute amounts from these base relations. They do not persist the derived values.

## Entity relationships and ER model

```mermaid
erDiagram
    ROLES ||--o{ USERS : assigns
    GUESTS o|--o| USERS : profile_for
    GUESTS ||--o{ RESERVATIONS : books
    USERS o|--o{ RESERVATIONS : creates
    ROOM_TYPES ||--o{ ROOMS : classifies
    ROOMS ||--o{ ROOM_AMENITIES : has
    AMENITIES ||--o{ ROOM_AMENITIES : includes
    RESERVATIONS ||--o{ RESERVATION_ROOMS : allocates
    ROOMS ||--o{ RESERVATION_ROOMS : allocated_to
    RESERVATIONS ||--o{ PAYMENTS : paid_by
    USERS o|--o{ PAYMENTS : processes
    RESERVATIONS ||--o{ RESERVATION_STATUS_HISTORY : tracks
    USERS o|--o{ RESERVATION_STATUS_HISTORY : changes
    GUESTS o|--o{ RESERVATION_STATUS_HISTORY : requests
    RESERVATIONS ||--o{ RESERVATION_SERVICES : consumes
    SERVICES ||--o{ RESERVATION_SERVICES : provides
    USERS o|--o{ AUDIT_LOGS : performs

    ROLES {
        int id PK
        string name UK
        string description
        datetime created_at
    }
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string full_name
        string phone
        boolean is_active
        int role_id FK
        int guest_profile_id FK_UK
        datetime last_login
        datetime created_at
        datetime updated_at
    }
    GUESTS {
        int id PK
        string first_name
        string last_name
        string email UK
        string phone
        string address
        string city
        string state
        string postal_code
        string country
        string identification_type
        string identification_number
        string notes
        datetime created_at
        datetime updated_at
    }
    ROOM_TYPES {
        int id PK
        string code UK
        string name
        string description
        decimal base_price
        int default_capacity
        int max_capacity
        string bed_type
        string image_url
        datetime created_at
    }
    ROOMS {
        int id PK
        string room_number UK
        int room_type_id FK
        int floor
        int capacity
        string operational_status
        boolean is_active
        string notes
        datetime created_at
        datetime updated_at
    }
    AMENITIES {
        int id PK
        string name UK
        string icon
        string category
    }
    ROOM_AMENITIES {
        int room_id PK, FK
        int amenity_id PK, FK
    }
    RESERVATIONS {
        int id PK
        string confirmation_number UK
        int guest_id FK
        date check_in_date
        date check_out_date
        int adults_count
        int children_count
        decimal tax_amount
        decimal discount_amount
        string status
        string special_requests
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }
    RESERVATION_ROOMS {
        int id PK
        int reservation_id FK
        int room_id FK
        decimal nightly_rate
        int nights
        datetime created_at
    }
    PAYMENTS {
        int id PK
        int reservation_id FK
        string payment_reference UK
        decimal amount
        decimal refunded_amount
        string currency
        string payment_method
        string payment_status
        string transaction_reference
        string notes
        int processed_by_id FK
        datetime created_at
    }
    RESERVATION_STATUS_HISTORY {
        int id PK
        int reservation_id FK
        string previous_status
        string new_status
        int changed_by_id FK
        string reason
        string request_source
        int requested_by_guest_id FK
        decimal cancellation_fee
        string refund_status
        datetime changed_at
    }
    SERVICES {
        int id PK
        string name UK
        string description
        decimal unit_price
        boolean is_active
        datetime created_at
    }
    RESERVATION_SERVICES {
        int id PK
        int reservation_id FK
        int service_id FK
        int quantity
        decimal unit_price
        date service_date
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string entity_type
        string entity_id
        string details
        string ip_address
        datetime timestamp
    }
    HOTEL_SETTINGS {
        int id PK
        string setting_key UK
        string setting_value
        string setting_type
        string description
        datetime updated_at
    }
```

All child references marked mandatory are `NOT NULL`; references marked optional are nullable. A reservation is not constrained by a database rule to have at least one allocation. `room_amenities`, `reservation_rooms`, and `reservation_services` are associative entities. `hotel_settings` has no relationship. `audit_logs.entity_type/entity_id` has no FK.

## Relational schema and constraints

```text
ROLES(id PK, name UK, description?, created_at)
USERS(id PK, username UK, email UK, password_hash, full_name, phone?, is_active,
      role_id FK→ROLES.id, guest_profile_id FK→GUESTS.id UNIQUE?, last_login?,
      created_at, updated_at)
GUESTS(id PK, first_name, last_name, email UK, phone, address?, city?, state?,
       postal_code?, country?, identification_type?, identification_number?, notes?,
       created_at, updated_at)
ROOM_TYPES(id PK, code UK, name, description?, base_price, default_capacity,
           max_capacity, bed_type, image_url?, created_at)
ROOMS(id PK, room_number UK, room_type_id FK→ROOM_TYPES.id, floor, capacity,
      operational_status, is_active, notes?, created_at, updated_at)
AMENITIES(id PK, name UK, icon?, category?)
ROOM_AMENITIES(room_id PK/FK→ROOMS.id, amenity_id PK/FK→AMENITIES.id)
RESERVATIONS(id PK, confirmation_number UK, guest_id FK→GUESTS.id,
             check_in_date, check_out_date, adults_count, children_count,
             tax_amount, discount_amount, status, special_requests?,
             created_by_id FK→USERS.id?, created_at, updated_at)
RESERVATION_ROOMS(id PK, reservation_id FK→RESERVATIONS.id, room_id FK→ROOMS.id,
                  nightly_rate, nights, created_at, UNIQUE(reservation_id, room_id))
PAYMENTS(id PK, reservation_id FK→RESERVATIONS.id, payment_reference UK, amount,
         refunded_amount, currency, payment_method, payment_status,
         transaction_reference?, notes?, processed_by_id FK→USERS.id?, created_at)
RESERVATION_STATUS_HISTORY(id PK, reservation_id FK→RESERVATIONS.id,
                           previous_status?, new_status, changed_by_id FK→USERS.id?,
                           reason?, changed_at, request_source?,
                           requested_by_guest_id FK→GUESTS.id?, cancellation_fee?,
                           refund_status?)
SERVICES(id PK, name UK, description?, unit_price, is_active, created_at)
RESERVATION_SERVICES(id PK, reservation_id FK→RESERVATIONS.id,
                     service_id FK→SERVICES.id, quantity, unit_price,
                     service_date, created_at)
AUDIT_LOGS(id PK, user_id FK→USERS.id?, action, entity_type, entity_id?, details?,
           ip_address?, timestamp)
HOTEL_SETTINGS(id PK, setting_key UK, setting_value, setting_type,
               description?, updated_at)
```

Live MySQL FKs use `RESTRICT` for deleting referenced guest/room-type/room/service/role rows and `CASCADE` for deleting reservation child rows and junction associations. Nullable user/guest actor links use `SET NULL`. Unique keys include all marked `UK` attributes and `(reservation_id, room_id)`; `room_amenities` has the composite PK. Native enum domains are `reservations.status` = `pending|confirmed|checked_in|checked_out|cancelled`, `payments.payment_status` = `paid|partially_refunded|refunded|failed`, and `rooms.operational_status` = `operational|maintenance|out_of_order`. MySQL check constraints validate reservation date ordering, room type pricing/capacity, room floor/capacity, nonnegative allocation rates and positive nights, positive payments with valid refunds, nonnegative service prices, and positive service quantities. Check-constraint declarations are present in the MySQL DDL; they are not all represented in ORM metadata.

## Implementation and verification evidence

The column-by-column MySQL type, nullability, default, primary/unique key and foreign-key catalogue is in [`data_dictionary_3nf.md`](data_dictionary_3nf.md).

- Removed the six persisted derived columns described above; retained row identifiers, FKs, unique constraints, rate/payment snapshots and audit data.
- `Reservation`, `ReservationRoom`, and `ReservationService` expose calculated hybrid properties; reservation price/balance filtering remains SQL-capable.
- Payment and refund services now write only the payment ledger; they no longer update a duplicate reservation paid total.
- Updated canonical schema, synthetic seed, and dependent SQL examples/routines/views/triggers.
- Added regression tests for derived values and SQL filtering.
- Full automated suite: 72 passed.
- MySQL forward migration and rollback succeeded on a disposable copy; baseline 23-table/344-row counts survived migration and rollback. A fresh disposable schema successfully loaded revised DDL/seed and ran revised read-only query, view, procedure, function, trigger, validator, explain and ACID scripts.
- The migrated disposable copy retained 16 reservations, 12 payments, 16 allocations, 16 status history rows, and zero service lines before smoke records. The seven missing status-history associations remain; no artificial history was inserted.
- A final direct ORM-to-MySQL metadata comparison after changing the ORM status fields to explicit native enums was blocked before execution by the environment's automatic approval usage limit. The revised DDL declares the same enum values; the comparison should be rerun in an approved environment before live migration.

## Live migration approval boundary

`database/mysql/13_normalize_derived_reservation_values.sql` and its rollback counterpart are prepared and tested only on disposable schemas. They are not approved for `hotelreservationdb`. The live database still has the pre-migration columns. The review plan must include a fresh backup, zero-result preflight checks, exact dropped columns/checks, unchanged expected row counts, application deployment ordering, and a tested recovery path. No live schema or data changes are made until explicit approval of that exact plan.
