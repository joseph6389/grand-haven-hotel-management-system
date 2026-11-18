# SUPERSEDED — See [Verified Actual 3NF Model](actual_3nf_model.md)

This earlier diagram includes persisted aggregate fields removed by the verified normalization implementation. Use the ER model and relational schema in `actual_3nf_model.md` for the revised application schema.

# Grand Haven Hotel — Entity Relationship (ER) Diagram & Data Model (archived draft)
## ADBMS Phase I — Advanced Conceptual & Logical Data Modelling

This document details the conceptual and logical database design for the **Grand Haven Hotel — Hotel Reservation Management System**.

---

## 1. Renderable Mermaid ER Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "assigned to"
    USERS ||--o{ RESERVATIONS : "creates"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    USERS ||--o{ PAYMENTS : "processes"

    GUESTS ||--o{ RESERVATIONS : "books"

    ROOM_TYPES ||--o{ ROOMS : "classifies"
    ROOMS ||--o{ ROOM_AMENITIES : "features"
    AMENITIES ||--o{ ROOM_AMENITIES : "included in"

    RESERVATIONS ||--|{ RESERVATION_ROOMS : "allocates"
    ROOMS ||--o{ RESERVATION_ROOMS : "allocated in"

    RESERVATIONS ||--o{ PAYMENTS : "billed through"
    RESERVATIONS ||--o{ RESERVATION_SERVICES : "consumes"
    SERVICES ||--o{ RESERVATION_SERVICES : "provided in"

    RESERVATIONS ||--o{ RESERVATION_STATUS_HISTORY : "tracks"

    ROLES {
        int id PK
        string name UK "Admin | Receptionist"
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
        string country
        string identification_type
        string identification_number
        text notes
        datetime created_at
        datetime updated_at
    }

    ROOM_TYPES {
        int id PK
        string code UK "STD | DLX | STE | PRE"
        string name
        text description
        decimal base_price
        int default_capacity
        int max_capacity
        string bed_type
        string image_url
        datetime created_at
    }

    ROOMS {
        int id PK
        string room_number UK "e.g. 101, 204"
        int room_type_id FK
        int floor
        int capacity
        string operational_status "operational | maintenance | out_of_order"
        boolean is_active
        text notes
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
        int room_id PK,FK
        int amenity_id PK,FK
    }

    RESERVATIONS {
        int id PK
        string confirmation_number UK "GH-YYYYMMDD-XXXX"
        int guest_id FK
        date check_in_date
        date check_out_date
        int adults_count
        int children_count
        int total_nights
        decimal room_charges
        decimal tax_amount
        decimal discount_amount
        decimal total_amount
        decimal paid_amount
        string status "pending | confirmed | checked_in | checked_out | cancelled"
        text special_requests
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
        decimal subtotal
        datetime created_at
    }

    RESERVATION_STATUS_HISTORY {
        int id PK
        int reservation_id FK
        string previous_status
        string new_status
        int changed_by_id FK
        string reason
        datetime changed_at
    }

    PAYMENTS {
        int id PK
        int reservation_id FK
        string payment_reference UK "PAY-..."
        decimal amount
        string currency
        string payment_method "credit_card | simulation | cash | bank_transfer"
        string payment_status "paid | refunded | failed"
        string transaction_reference
        string notes
        int processed_by_id FK
        datetime created_at
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
        decimal total_price
        date service_date
        datetime created_at
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string entity_type
        string entity_id
        text details
        string ip_address
        datetime timestamp
    }

    HOTEL_SETTINGS {
        int id PK
        string setting_key UK
        text setting_value
        string setting_type
        string description
        datetime updated_at
    }
```

---

## 2. Cardinality Analysis & Relationship Semantics

| Parent Entity | Child Entity | Cardinality | Business Meaning / Integrity Constraint |
| :--- | :--- | :--- | :--- |
| **ROLES** | **USERS** | `1 : N` (One-to-Many) | Each staff member has exactly one role clearance. A role can be assigned to zero, one, or many staff. `ON DELETE RESTRICT`. |
| **GUESTS** | **RESERVATIONS** | `1 : N` (One-to-Many) | A registered guest may place multiple reservations across time. A reservation belongs to exactly one primary guest. `ON DELETE RESTRICT`. |
| **ROOM_TYPES** | **ROOMS** | `1 : N` (One-to-Many) | A suite classification (e.g., Deluxe Oceanfront) governs multiple physical room units. Deleting a type with active rooms is disallowed. `ON DELETE RESTRICT`. |
| **ROOMS** | **AMENITIES** | `M : N` (Many-to-Many) | Resolved via junction entity `ROOM_AMENITIES`. A room features multiple amenities; an amenity is featured across multiple rooms. |
| **RESERVATIONS** | **ROOMS** | `M : N` (Many-to-Many) | Resolved via junction entity `RESERVATION_ROOMS`. Preserves historical rate snapshots (`nightly_rate`, `subtotal`). Unique constraint `(reservation_id, room_id)`. |
| **RESERVATIONS** | **PAYMENTS** | `1 : N` (One-to-Many) | Multiple transaction records (deposit, final balance, refunds) associate to one reservation. `ON DELETE RESTRICT`. |
| **RESERVATIONS** | **SERVICES** | `M : N` (Many-to-Many) | Resolved via junction entity `RESERVATION_SERVICES` with quantity and unit price. |
| **RESERVATIONS** | **STATUS_HISTORY** | `1 : N` (One-to-Many) | Chronological state transition audit log (`pending` -> `confirmed` -> `checked_in` -> `checked_out`). Cascade deleted if reservation is purged. |
| **USERS** | **AUDIT_LOGS** | `1 : N` (One-to-Many) | Security and operations audit trail. `ON DELETE SET NULL` ensures logs are preserved even if staff account is deleted. |

---

## 3. Entity Integrity & Domain Constraints

1. **Monetary Precision**: All monetary values (`base_price`, `nightly_rate`, `room_charges`, `tax_amount`, `discount_amount`, `total_amount`, `paid_amount`, `amount`, `unit_price`, `total_price`) utilize fixed-point `DECIMAL(10, 2)` representations to eliminate floating-point rounding errors.
2. **Temporal Bounds**: Check constraint `chk_res_dates` strictly requires `check_out_date > check_in_date`.
3. **Double Booking Guard**: Checked via composite unique indexing and database triggers (`trg_prevent_double_booking`) preventing overlapping date ranges for active allocations.
