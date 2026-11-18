# SUPERSEDED — See [Verified Actual 3NF Model](actual_3nf_model.md)

This earlier draft describes a hypothetical unnormalized source relation and predates the verified schema migration work. Do not use it as evidence of the current implementation. The updated FD analysis, active-table assessment, relational schema, ER relationships, migration evidence and limitations are in `actual_3nf_model.md`.

# Grand Haven Hotel — Database Normalization Analysis (archived draft)
## ADBMS Phase I — Rigorous Normalization from UNF through 3NF

This document presents the complete formal normalization process for the hotel reservation system, fulfilling the academic requirements of **Advanced Database Management Systems (ADBMS)**.

---

## 1. Unnormalized Form (UNF)

In a legacy or spreadsheet-based hotel log, an unnormalized record typically captures booking, guest, room, amenity, and payment data in a single wide table containing multi-valued attributes and repeating groups.

### Example UNF Record:
```text
Reservation_Record {
    Confirmation_No: "GH-20261014-9B2D",
    Booking_Date: "2026-10-12",
    Guest_Name: "Marcus Sterling",
    Guest_Email: "marcus.sterling@example.com",
    Guest_Phone: "+44 20 7946 0912",
    Guest_Address: "14 Mayfair Gardens, London, United Kingdom",
    Check_In: "2026-10-14",
    Check_Out: "2026-10-18",
    Nights: 4,
    Allocated_Rooms: ["203", "204"],                  <-- REPEATING GROUP
    Room_Types: ["Deluxe Oceanfront", "Deluxe Oceanfront"],
    Room_Rates: [260.00, 260.00],
    Room_Amenities: ["Ocean Balcony, Wi-Fi, Jacuzzi", "Balcony, Wi-Fi"], <-- NON-ATOMIC VALUES
    Total_Charges: 2080.00,
    Tax: 249.60,
    Grand_Total: 2329.60,
    Payment_Refs: ["PAY-1001", "PAY-1002"],           <-- REPEATING GROUP
    Payment_Amounts: [1000.00, 1329.60],              <-- REPEATING GROUP
    Staff_Clerk: "Elena Rostova",
    Staff_Role: "Receptionist"
}
```

### Flaws of the UNF Design:
1. **Repeating Groups**: Multiple rooms and payments stored within array structures.
2. **Non-Atomic Attributes**: `Room_Amenities` stored as comma-separated text strings.
3. **Insertion Anomalies**: Cannot record an amenity or a room type without creating a dummy reservation.
4. **Update Anomalies**: Changing a room's base price or a guest's phone requires mutating multiple redundant rows.
5. **Deletion Anomalies**: Deleting a past reservation erases guest contact details and room configuration permanently.

---

## 2. First Normal Form (1NF)

### 1NF Definition:
> A relation is in **1NF** if and only if all domain values are atomic (indivisible) and there are no repeating groups or nested arrays. Every column must hold a single scalar value, and each tuple must be uniquely identifiable.

### Step 1: Flatten Repeating Groups & Atomize Attributes
1. Atomize `Room_Amenities` into separate rows rather than comma-separated lists.
2. Flatten `Allocated_Rooms` and `Payments` so that each row represents a single reservation-room-payment instance.

### 1NF Schema Representation:
```text
HOTEL_BOOKING_1NF (
    Confirmation_No,
    Room_Number,
    Payment_Ref,
    Amenity_Name,
    Booking_Date,
    Guest_Email,
    Guest_Name,
    Guest_Phone,
    Guest_Address,
    Check_In,
    Check_Out,
    Nights,
    Room_Type_Code,
    Room_Type_Name,
    Room_Base_Price,
    Room_Floor,
    Room_Capacity,
    Payment_Amount,
    Payment_Method,
    Staff_Username,
    Staff_Role
)
```
- **Composite Primary Key**: `{Confirmation_No, Room_Number, Payment_Ref, Amenity_Name}`

### Functional Dependencies in 1NF:
- `Confirmation_No -> Guest_Email, Guest_Name, Guest_Phone, Check_In, Check_Out, Nights, Staff_Username`
- `Room_Number -> Room_Type_Code, Room_Floor, Room_Capacity`
- `Room_Type_Code -> Room_Type_Name, Room_Base_Price`
- `Payment_Ref -> Payment_Amount, Payment_Method`
- `Guest_Email -> Guest_Name, Guest_Phone, Guest_Address`
- `Staff_Username -> Staff_Role`

### Diagnosis of 1NF:
The relation suffers from **Partial Functional Dependencies**: Non-prime attributes depend only on a proper subset of the composite primary key. For example, `Room_Floor` depends solely on `Room_Number`, not on `{Confirmation_No, Payment_Ref, Amenity_Name}`. This violates 2NF.

---

## 3. Second Normal Form (2NF)

### 2NF Definition:
> A relation is in **2NF** if and only if it is in 1NF and **no non-prime attribute is partially dependent on any candidate key**. All non-key attributes must be fully functionally dependent on the entire primary key.

### Step 2: Eliminate Partial Dependencies by Table Decomposition
We decompose `HOTEL_BOOKING_1NF` into distinct relations based on the determinant subsets of candidate keys:

1. **RESERVATIONS** (`Confirmation_No` as PK):
   - Attributes: `Confirmation_No`, `Booking_Date`, `Guest_Email`, `Check_In`, `Check_Out`, `Nights`, `Staff_Username`
   - *Dependency*: All attributes depend on the complete key `Confirmation_No`.

2. **RESERVATION_ROOMS** (`Confirmation_No, Room_Number` as PK):
   - Attributes: `Confirmation_No`, `Room_Number`, `Nightly_Rate_Snapshot`, `Subtotal`
   - *Dependency*: Fully dependent on the composite key of which room is in which reservation.

3. **ROOMS** (`Room_Number` as PK):
   - Attributes: `Room_Number`, `Room_Type_Code`, `Room_Floor`, `Room_Capacity`, `Operational_Status`
   - *Dependency*: Fully dependent on `Room_Number`.

4. **ROOM_AMENITIES** (`Room_Number, Amenity_Name` as PK):
   - Attributes: `Room_Number`, `Amenity_Name`
   - *Dependency*: Pure associative entity.

5. **PAYMENTS** (`Payment_Ref` as PK):
   - Attributes: `Payment_Ref`, `Confirmation_No`, `Payment_Amount`, `Payment_Method`, `Payment_Date`
   - *Dependency*: Fully dependent on `Payment_Ref`.

6. **GUESTS** (`Guest_Email` as PK):
   - Attributes: `Guest_Email`, `Guest_Name`, `Guest_Phone`, `Guest_Address`, `City`, `Country`
   - *Dependency*: Fully dependent on `Guest_Email`.

### Diagnosis of 2NF:
All partial dependencies on composite keys have been eliminated. However, relations still contain **Transitive Dependencies**: Non-key attributes depend on other non-key attributes. For example:
- In `ROOMS`: `Room_Number -> Room_Type_Code -> Room_Type_Name, Room_Base_Price`
  - `Room_Type_Name` depends on `Room_Type_Code`, which is NOT a candidate key of `ROOMS`.
- In `RESERVATIONS`: `Confirmation_No -> Staff_Username -> Staff_Role`
  - `Staff_Role` depends on `Staff_Username`.

This violates 3NF.

---

## 4. Third Normal Form (3NF)

### 3NF Definition:
> A relation is in **3NF** if and only if it is in 2NF and **no non-prime attribute is transitively dependent on any candidate key**. Formally: For every non-trivial functional dependency $X \rightarrow Y$, either:
> 1. $X$ is a superkey, OR
> 2. $Y$ is a prime attribute (part of a candidate key).

### Step 3: Eliminate Transitive Dependencies by Further Decomposition

#### Transitive Dependency 1: Room Classification
- In `ROOMS`, we have:
  - $\text{Room\_Number} \rightarrow \text{Room\_Type\_Code}$
  - $\text{Room\_Type\_Code} \rightarrow \{\text{Room\_Type\_Name}, \text{Room\_Base\_Price}, \text{Bed\_Type}\}$
- **Resolution**: Extract `ROOM_TYPES` relation:
  - `ROOM_TYPES` (<ins>id</ins>, code, name, description, base_price, default_capacity, max_capacity, bed_type)
  - `ROOMS` (<ins>id</ins>, room_number, <span style="text-decoration: underline dashed;">room_type_id</span>, floor, capacity, operational_status)

#### Transitive Dependency 2: Staff Security Clearance
- In `USERS`, we have:
  - $\text{Username} \rightarrow \text{Role\_ID}$
  - $\text{Role\_ID} \rightarrow \text{Role\_Name}, \text{Role\_Description}$
- **Resolution**: Extract `ROLES` relation:
  - `ROLES` (<ins>id</ins>, name, description)
  - `USERS` (<ins>id</ins>, username, email, password_hash, full_name, <span style="text-decoration: underline dashed;">role_id</span>)

#### Transitive Dependency 3: Amenity Attributes
- Extract `AMENITIES` table and link via junction table `ROOM_AMENITIES`:
  - `AMENITIES` (<ins>id</ins>, name, icon, category)
  - `ROOM_AMENITIES` (<ins><span style="text-decoration: underline dashed;">room_id</span></ins>, <ins><span style="text-decoration: underline dashed;">amenity_id</span></ins>)

---

## 5. Summary of Final 3NF Normalized Relations

| Final Relation | Primary Key | Foreign Keys | Normal Form Achieved |
| :--- | :--- | :--- | :--- |
| **ROLES** | `id` | None | **3NF** / BCNF |
| **USERS** | `id` | `role_id` &rarr; `ROLES(id)` | **3NF** / BCNF |
| **GUESTS** | `id` | None | **3NF** / BCNF |
| **ROOM_TYPES** | `id` | None | **3NF** / BCNF |
| **ROOMS** | `id` | `room_type_id` &rarr; `ROOM_TYPES(id)` | **3NF** / BCNF |
| **AMENITIES** | `id` | None | **3NF** / BCNF |
| **ROOM_AMENITIES** | `(room_id, amenity_id)` | `room_id` &rarr; `ROOMS(id)`, `amenity_id` &rarr; `AMENITIES(id)` | **3NF** / BCNF |
| **RESERVATIONS** | `id` | `guest_id` &rarr; `GUESTS(id)`, `created_by_id` &rarr; `USERS(id)` | **3NF** / BCNF |
| **RESERVATION_ROOMS**| `id` | `reservation_id` &rarr; `RESERVATIONS(id)`, `room_id` &rarr; `ROOMS(id)`| **3NF** / BCNF |
| **PAYMENTS** | `id` | `reservation_id` &rarr; `RESERVATIONS(id)`, `processed_by_id` &rarr; `USERS(id)` | **3NF** / BCNF |
| **SERVICES** | `id` | None | **3NF** / BCNF |
| **RESERVATION_SERVICES**| `id` | `reservation_id` &rarr; `RESERVATIONS(id)`, `service_id` &rarr; `SERVICES(id)` | **3NF** / BCNF |
| **STATUS_HISTORY** | `id` | `reservation_id` &rarr; `RESERVATIONS(id)`, `changed_by_id` &rarr; `USERS(id)` | **3NF** / BCNF |

### Conclusion:
Every relation in the Grand Haven Hotel system is in **Third Normal Form (3NF)**:
1. Every attribute is atomic.
2. No partial dependencies exist on any composite key.
3. No transitive dependencies exist between non-key attributes.
4. All update, insertion, and deletion anomalies are eradicated while preserving full referential integrity.
