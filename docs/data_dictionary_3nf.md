# Grand Haven Hotel — Verified 3NF Data Dictionary

Source: fresh disposable MySQL 8.0.46 schema created from the revised canonical DDL. This is the implemented schema shape; the live database remains at its pre-migration version pending approval. `?` means nullable.

## `roles`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `name` | `VARCHAR(50)` | NOT NULL | — | UK |
| `description` | `VARCHAR(255)` | NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `users`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `username` | `VARCHAR(64)` | NOT NULL | — | UK |
| `email` | `VARCHAR(120)` | NOT NULL | — | UK |
| `password_hash` | `VARCHAR(255)` | NOT NULL | — | — |
| `full_name` | `VARCHAR(100)` | NOT NULL | — | — |
| `phone` | `VARCHAR(30)` | NULL | — | — |
| `is_active` | `TINYINT` | NOT NULL | '1' | — |
| `role_id` | `INTEGER` | NOT NULL | — | FK → `roles.id` (RESTRICT) |
| `guest_profile_id` | `INTEGER` | NULL | — | UK; FK → `guests.id` (SET NULL) |
| `last_login` | `DATETIME` | NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |
| `updated_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — |

## `guests`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `first_name` | `VARCHAR(60)` | NOT NULL | — | — |
| `last_name` | `VARCHAR(60)` | NOT NULL | — | — |
| `email` | `VARCHAR(120)` | NOT NULL | — | UK |
| `phone` | `VARCHAR(30)` | NOT NULL | — | — |
| `address` | `VARCHAR(255)` | NULL | — | — |
| `city` | `VARCHAR(100)` | NULL | — | — |
| `state` | `VARCHAR(100)` | NULL | — | — |
| `postal_code` | `VARCHAR(20)` | NULL | — | — |
| `country` | `VARCHAR(100)` | NULL | 'India' | — |
| `identification_type` | `VARCHAR(50)` | NULL | — | — |
| `identification_number` | `VARCHAR(100)` | NULL | — | — |
| `notes` | `TEXT` | NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |
| `updated_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — |

## `room_types`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `code` | `VARCHAR(20)` | NOT NULL | — | UK |
| `name` | `VARCHAR(100)` | NOT NULL | — | — |
| `description` | `TEXT` | NULL | — | — |
| `base_price` | `DECIMAL(10, 2)` | NOT NULL | — | — |
| `default_capacity` | `INTEGER` | NOT NULL | '2' | — |
| `max_capacity` | `INTEGER` | NOT NULL | '4' | — |
| `bed_type` | `VARCHAR(80)` | NOT NULL | '1 King Bed' | — |
| `image_url` | `VARCHAR(255)` | NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `rooms`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `room_number` | `VARCHAR(20)` | NOT NULL | — | UK |
| `room_type_id` | `INTEGER` | NOT NULL | — | FK → `room_types.id` (RESTRICT) |
| `floor` | `INTEGER` | NOT NULL | '1' | — |
| `capacity` | `INTEGER` | NOT NULL | '2' | — |
| `operational_status` | `ENUM` | NOT NULL | 'operational' | — |
| `is_active` | `TINYINT` | NOT NULL | '1' | — |
| `notes` | `TEXT` | NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |
| `updated_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — |

## `amenities`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `name` | `VARCHAR(80)` | NOT NULL | — | UK |
| `icon` | `VARCHAR(50)` | NULL | 'bi-check-circle' | — |
| `category` | `VARCHAR(50)` | NULL | 'General' | — |

## `room_amenities`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `room_id` | `INTEGER` | NOT NULL | — | PK; FK → `rooms.id` (CASCADE) |
| `amenity_id` | `INTEGER` | NOT NULL | — | PK; FK → `amenities.id` (CASCADE) |

## `reservations`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `confirmation_number` | `VARCHAR(32)` | NOT NULL | — | UK |
| `guest_id` | `INTEGER` | NOT NULL | — | FK → `guests.id` (RESTRICT) |
| `check_in_date` | `DATE` | NOT NULL | — | — |
| `check_out_date` | `DATE` | NOT NULL | — | — |
| `adults_count` | `INTEGER` | NOT NULL | '1' | — |
| `children_count` | `INTEGER` | NOT NULL | '0' | — |
| `tax_amount` | `DECIMAL(10, 2)` | NOT NULL | '0.00' | — |
| `discount_amount` | `DECIMAL(10, 2)` | NOT NULL | '0.00' | — |
| `status` | `ENUM` | NOT NULL | 'confirmed' | — |
| `special_requests` | `TEXT` | NULL | — | — |
| `created_by_id` | `INTEGER` | NULL | — | FK → `users.id` (SET NULL) |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |
| `updated_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — |

## `reservation_rooms`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `reservation_id` | `INTEGER` | NOT NULL | — | UK; FK → `reservations.id` (CASCADE) |
| `room_id` | `INTEGER` | NOT NULL | — | UK; FK → `rooms.id` (RESTRICT) |
| `nightly_rate` | `DECIMAL(10, 2)` | NOT NULL | — | — |
| `nights` | `INTEGER` | NOT NULL | '1' | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `payments`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `reservation_id` | `INTEGER` | NOT NULL | — | FK → `reservations.id` (RESTRICT) |
| `payment_reference` | `VARCHAR(40)` | NOT NULL | — | UK |
| `amount` | `DECIMAL(10, 2)` | NOT NULL | — | — |
| `refunded_amount` | `DECIMAL(10, 2)` | NOT NULL | '0.00' | — |
| `currency` | `VARCHAR(3)` | NOT NULL | 'INR' | — |
| `payment_method` | `VARCHAR(30)` | NOT NULL | 'credit_card' | — |
| `payment_status` | `ENUM` | NOT NULL | 'paid' | — |
| `transaction_reference` | `VARCHAR(100)` | NULL | — | — |
| `notes` | `VARCHAR(255)` | NULL | — | — |
| `processed_by_id` | `INTEGER` | NULL | — | FK → `users.id` (SET NULL) |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `reservation_status_history`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `reservation_id` | `INTEGER` | NOT NULL | — | FK → `reservations.id` (CASCADE) |
| `previous_status` | `VARCHAR(20)` | NULL | — | — |
| `new_status` | `VARCHAR(20)` | NOT NULL | — | — |
| `changed_by_id` | `INTEGER` | NULL | — | FK → `users.id` (SET NULL) |
| `reason` | `VARCHAR(255)` | NULL | — | — |
| `request_source` | `VARCHAR(20)` | NULL | — | — |
| `requested_by_guest_id` | `INTEGER` | NULL | — | FK → `guests.id` (SET NULL) |
| `cancellation_fee` | `DECIMAL(10, 2)` | NULL | — | — |
| `refund_status` | `VARCHAR(30)` | NULL | — | — |
| `changed_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `services`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `name` | `VARCHAR(100)` | NOT NULL | — | UK |
| `description` | `VARCHAR(255)` | NULL | — | — |
| `unit_price` | `DECIMAL(10, 2)` | NOT NULL | '0.00' | — |
| `is_active` | `TINYINT` | NOT NULL | '1' | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `reservation_services`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `reservation_id` | `INTEGER` | NOT NULL | — | FK → `reservations.id` (CASCADE) |
| `service_id` | `INTEGER` | NOT NULL | — | FK → `services.id` (RESTRICT) |
| `quantity` | `INTEGER` | NOT NULL | '1' | — |
| `unit_price` | `DECIMAL(10, 2)` | NOT NULL | — | — |
| `service_date` | `DATE` | NOT NULL | — | — |
| `created_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `audit_logs`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `user_id` | `INTEGER` | NULL | — | FK → `users.id` (SET NULL) |
| `action` | `VARCHAR(50)` | NOT NULL | — | — |
| `entity_type` | `VARCHAR(50)` | NOT NULL | — | — |
| `entity_id` | `VARCHAR(50)` | NULL | — | — |
| `details` | `TEXT` | NULL | — | — |
| `ip_address` | `VARCHAR(45)` | NULL | — | — |
| `timestamp` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP | — |

## `hotel_settings`

| Column | MySQL type | Null | Default | Key / rule |
|---|---|---|---|---|
| `id` | `INTEGER` | NOT NULL | — | PK |
| `setting_key` | `VARCHAR(50)` | NOT NULL | — | UK |
| `setting_value` | `TEXT` | NOT NULL | — | — |
| `setting_type` | `VARCHAR(20)` | NOT NULL | 'string' | — |
| `description` | `VARCHAR(255)` | NULL | — | — |
| `updated_at` | `DATETIME` | NOT NULL | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — |

Composite uniqueness: `reservation_rooms(reservation_id, room_id)`; composite primary key: `room_amenities(room_id, amenity_id)`. Other table-level checks and relationship actions are listed in `actual_3nf_model.md`.
