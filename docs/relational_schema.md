# SUPERSEDED — See [Verified Actual 3NF Model](actual_3nf_model.md)

This earlier schema predates removal of persisted derived totals. The current relational schema and migration evidence are documented in `actual_3nf_model.md`.

# Grand Haven Hotel — Relational Schema Specification (archived draft)
## ADBMS Phase I & II — Relational Schema & Integrity Architecture

This document presents the formal relational schema, column data dictionaries, foreign key actions, and index mappings for the Grand Haven Hotel reservation management system.

---

## 1. Relational Schema Notation

- **ROLES** (<ins>id</ins>, name, description, created_at)
- **USERS** (<ins>id</ins>, username, email, password_hash, full_name, phone, is_active, <span style="text-decoration: underline dashed;">role_id</span>, last_login, created_at, updated_at)
- **GUESTS** (<ins>id</ins>, first_name, last_name, email, phone, address, city, country, identification_type, identification_number, notes, created_at, updated_at)
- **ROOM_TYPES** (<ins>id</ins>, code, name, description, base_price, default_capacity, max_capacity, bed_type, image_url, created_at)
- **AMENITIES** (<ins>id</ins>, name, icon, category)
- **ROOMS** (<ins>id</ins>, room_number, <span style="text-decoration: underline dashed;">room_type_id</span>, floor, capacity, operational_status, is_active, notes, created_at, updated_at)
- **ROOM_AMENITIES** (<ins><span style="text-decoration: underline dashed;">room_id</span></ins>, <ins><span style="text-decoration: underline dashed;">amenity_id</span></ins>)
- **RESERVATIONS** (<ins>id</ins>, confirmation_number, <span style="text-decoration: underline dashed;">guest_id</span>, check_in_date, check_out_date, adults_count, children_count, total_nights, room_charges, tax_amount, discount_amount, total_amount, paid_amount, status, special_requests, <span style="text-decoration: underline dashed;">created_by_id</span>, created_at, updated_at)
- **RESERVATION_ROOMS** (<ins>id</ins>, <span style="text-decoration: underline dashed;">reservation_id</span>, <span style="text-decoration: underline dashed;">room_id</span>, nightly_rate, nights, subtotal, created_at)
- **RESERVATION_STATUS_HISTORY** (<ins>id</ins>, <span style="text-decoration: underline dashed;">reservation_id</span>, previous_status, new_status, <span style="text-decoration: underline dashed;">changed_by_id</span>, reason, changed_at)
- **PAYMENTS** (<ins>id</ins>, <span style="text-decoration: underline dashed;">reservation_id</span>, payment_reference, amount, currency, payment_method, payment_status, refunded_amount, transaction_reference, notes, <span style="text-decoration: underline dashed;">processed_by_id</span>, created_at)
- **SERVICES** (<ins>id</ins>, name, description, unit_price, is_active, created_at)
- **RESERVATION_SERVICES** (<ins>id</ins>, <span style="text-decoration: underline dashed;">reservation_id</span>, <span style="text-decoration: underline dashed;">service_id</span>, quantity, unit_price, total_price, service_date, created_at)
- **AUDIT_LOGS** (<ins>id</ins>, <span style="text-decoration: underline dashed;">user_id</span>, action, entity_type, entity_id, details, ip_address, timestamp)
- **HOTEL_SETTINGS** (<ins>id</ins>, setting_key, setting_value, setting_type, description, updated_at)

*(Key: <ins>Underlined</ins> = Primary Key; <span style="text-decoration: underline dashed;">Dashed Underline</span> = Foreign Key)*

---

## 2. Table Data Dictionary & Constraint Matrix

### Table: `reservations`
| Attribute | Type | Nullable | Key / Constraint | Default | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | NO | PK, Auto Increment | &mdash; | Surrogate identifier |
| `confirmation_number` | `VARCHAR(32)` | NO | UK, Index | &mdash; | Unique guest booking code (`GH-YYYYMMDD-XXXX`) |
| `guest_id` | `INT` | NO | FK &rarr; `guests.id` (`RESTRICT`) | &mdash; | Associated primary guest |
| `check_in_date` | `DATE` | NO | Composite Index | &mdash; | Arrival calendar date |
| `check_out_date` | `DATE` | NO | Composite Index | &mdash; | Departure calendar date (`CHECK (check_out_date > check_in_date)`) |
| `adults_count` | `INT` | NO | `CHECK (adults_count >= 1)` | 1 | Number of adult occupants |
| `children_count` | `INT` | NO | `CHECK (children_count >= 0)` | 0 | Number of child occupants |
| `total_nights` | `INT` | NO | `CHECK (total_nights >= 1)` | 1 | Number of calculated nights |
| `room_charges` | `DECIMAL(10,2)`| NO | `CHECK (room_charges >= 0.00)` | 0.00 | Total lodging subtotal |
| `tax_amount` | `DECIMAL(10,2)`| NO | `CHECK (tax_amount >= 0.00)` | 0.00 | Calculated lodging tax (e.g. 12%) |
| `discount_amount` | `DECIMAL(10,2)`| NO | `CHECK (discount_amount >= 0.00)`| 0.00 | Applied promo or loyalty discount |
| `total_amount` | `DECIMAL(10,2)`| NO | `CHECK (total_amount >= 0.00)` | 0.00 | Server-calculated total (`room_charges + tax - discount`) |
| `paid_amount` | `DECIMAL(10,2)`| NO | `CHECK (paid_amount >= 0.00)` | 0.00 | Total cleared payments received |
| `status` | `ENUM(...)` | NO | Index | `'confirmed'` | Lifecycle state (`pending`, `confirmed`, `checked_in`, `checked_out`, `cancelled`) |
| `special_requests` | `TEXT` | YES | &mdash; | NULL | Guest dietary/concierge notes |
| `created_by_id` | `INT` | YES | FK &rarr; `users.id` (`SET NULL`) | NULL | Staff member who initiated (NULL for web self-booking) |
| `created_at` | `DATETIME` | NO | &mdash; | `CURRENT_TIMESTAMP` | Audit creation timestamp |
| `updated_at` | `DATETIME` | NO | &mdash; | `CURRENT_TIMESTAMP` | Last mutation timestamp |

---

### Table: `rooms`
| Attribute | Type | Nullable | Key / Constraint | Default | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | NO | PK, Auto Increment | &mdash; | Surrogate identifier |
| `room_number` | `VARCHAR(20)` | NO | UK, Index | &mdash; | Physical room identifier (e.g., '101', '403') |
| `room_type_id` | `INT` | NO | FK &rarr; `room_types.id` (`RESTRICT`) | &mdash; | Room classification parent |
| `floor` | `INT` | NO | `CHECK (floor > 0)` | 1 | Property floor level |
| `capacity` | `INT` | NO | `CHECK (capacity > 0)` | 2 | Max allowed occupants |
| `operational_status` | `ENUM(...)` | NO | Index | `'operational'` | `'operational'`, `'maintenance'`, `'out_of_order'` |
| `is_active` | `BOOLEAN` | NO | &mdash; | `TRUE` | Soft deletion flag |
| `notes` | `TEXT` | YES | &mdash; | NULL | Housekeeping / maintenance notes |

---

### Table: `reservation_rooms` (Junction Entity)
| Attribute | Type | Nullable | Key / Constraint | Default | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | NO | PK, Auto Increment | &mdash; | Surrogate identifier |
| `reservation_id` | `INT` | NO | FK &rarr; `reservations.id` (`CASCADE`) | &mdash; | Parent reservation |
| `room_id` | `INT` | NO | FK &rarr; `rooms.id` (`RESTRICT`) | &mdash; | Allocated physical room |
| `nightly_rate` | `DECIMAL(10,2)`| NO | `CHECK (nightly_rate >= 0.00)` | &mdash; | Immutable rate snapshot at booking time |
| `nights` | `INT` | NO | `CHECK (nights >= 1)` | 1 | Stay nights for this allocation |
| `subtotal` | `DECIMAL(10,2)`| NO | `CHECK (subtotal >= 0.00)` | &mdash; | `nightly_rate * nights` |

**Table Unique Constraint**: `UNIQUE KEY uq_reservation_room (reservation_id, room_id)` ensures a room cannot be allocated multiple times to the same reservation.

---

### Table: `payments`
| Attribute | Type | Nullable | Key / Constraint | Default | Purpose / Business Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INT` | NO | PK, Auto Increment | &mdash; | Surrogate identifier |
| `reservation_id` | `INT` | NO | FK &rarr; `reservations.id` (`RESTRICT`) | &mdash; | Associated reservation |
| `payment_reference` | `VARCHAR(40)` | NO | UK, Index | &mdash; | Unique receipt identifier (`PAY-XXXXXXXX-N`) |
| `amount` | `DECIMAL(10,2)`| NO | `CHECK (amount > 0.00)` | &mdash; | Cleared payment amount |
| `currency` | `VARCHAR(3)` | NO | &mdash; | `'INR'` | ISO 4217 Currency Code |
| `payment_method` | `VARCHAR(30)` | NO | &mdash; | `'credit_card'`| `'credit_card'`, `'simulation'`, `'cash'`, `'bank_transfer'` |
| `payment_status` | `ENUM(...)` | NO | Index | `'paid'` | `'paid'`, `'refunded'`, `'failed'` |
| `transaction_reference`| `VARCHAR(100)`| YES| &mdash; | NULL | Gateway transaction or simulation auth code |
| `notes` | `VARCHAR(255)`| YES| &mdash; | NULL | Transaction remarks |
| `processed_by_id` | `INT` | YES | FK &rarr; `users.id` (`SET NULL`) | NULL | Staff clerk who processed payment |
| `created_at` | `DATETIME` | NO | Index | `CURRENT_TIMESTAMP` | Transaction timestamp |

---

## 3. Database Indexes

| Index Name | Table | Columns | Index Type | Optimization Objective |
| :--- | :--- | :--- | :--- | :--- |
| `PRIMARY` | All tables | `id` | Clustered B-Tree | O(1) row retrieval |
| `idx_res_confirmation`| `reservations` | `confirmation_number` | Unique B-Tree | Instant voucher and front desk lookup |
| `idx_res_dates` | `reservations` | `(check_in_date, check_out_date)` | Composite B-Tree | Fast date range overlap collision detection |
| `idx_res_status` | `reservations` | `status` | B-Tree | Fast filtering by Confirmed, Checked-in, Checked-out |
| `idx_guests_email` | `guests` | `email` | Unique B-Tree | Prevents duplicate guest accounts |
| `idx_rooms_number` | `rooms` | `room_number` | Unique B-Tree | Instant room lookup |
| `idx_rooms_status` | `rooms` | `operational_status` | B-Tree | Filtering available vs maintenance rooms |
| `idx_pay_reference` | `payments` | `payment_reference` | Unique B-Tree | Instant payment and receipt retrieval |
