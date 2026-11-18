# Grand Haven Hotel — REST API Documentation
## Client & AJAX Asynchronous Integration Reference

This document outlines the REST API endpoints available in the Grand Haven Hotel application for asynchronous Fetch requests, dynamic frontend widgets, and third-party integrations.

---

## Base URL & Authentication
- **Base URL**: `http://localhost:5000/api`
- **Session Authentication**: Browser session cookie with Flask-Login.
- **CSRF Behavior**: The `/api/` blueprint is configured for asynchronous JSON calls without token friction, while standard web forms enforce strict CSRF protection.

---

## 1. Room Availability & Quotation Endpoints

### 1.1 `GET /api/available-rooms`
Retrieves all operational rooms that have no conflicting reservations for the specified date range.

**Query Parameters:**
| Parameter | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `check_in` | `string` | **Yes** | Check-in date (`YYYY-MM-DD`) | `2026-11-01` |
| `check_out` | `string` | **Yes** | Check-out date (`YYYY-MM-DD`) | `2026-11-04` |
| `room_type_id` | `int` | No | Filter by specific room classification ID | `2` |
| `capacity` | `int` | No | Minimum guest capacity | `2` |

**Sample Response (`200 OK`):**
```json
{
  "check_in": "2026-11-01",
  "check_out": "2026-11-04",
  "nights": 3,
  "count": 2,
  "rooms": [
    {
      "id": 1,
      "room_number": "101",
      "room_type_id": 1,
      "room_type_name": "Classic King Sanctuary",
      "room_type_code": "STD",
      "floor": 1,
      "capacity": 2,
      "price_per_night": 180.00,
      "formatted_price": "₹180.00",
      "bed_type": "1 King Bed",
      "operational_status": "operational",
      "is_operational": true,
      "image_url": "https://images.unsplash.com/...",
      "amenities": [
        {"id": 2, "name": "King Featherbed", "icon": "bi-moon-stars", "category": "Comfort"}
      ]
    }
  ]
}
```

---

### 1.2 `GET /api/pricing-quote`
Calculates server-side subtotal, taxes, and final billing for selected room IDs and dates. Never trust client pricing.

**Query Parameters:**
- `check_in`: `2026-11-01`
- `check_out`: `2026-11-04`
- `room_ids`: `1` (can be passed multiple times for multi-room bookings)

**Sample Response (`200 OK`):**
```json
{
  "nights": 3,
  "room_charges": 540.00,
  "tax_amount": 64.80,
  "total_amount": 604.80,
  "rooms": [
    {
      "room_id": 1,
      "room_number": "101",
      "nightly_rate": 180.00,
      "subtotal": 540.00
    }
  ]
}
```

---

## 2. Dashboard Analytics Endpoints

### 2.1 `GET /api/dashboard/stats`
Returns aggregated real-time hotel operational metrics.

**Sample Response (`200 OK`):**
```json
{
  "total_rooms": 16,
  "available_rooms": 13,
  "occupied_rooms": 2,
  "maintenance_rooms": 1,
  "total_reservations": 7,
  "confirmed_reservations": 2,
  "today_arrivals": 0,
  "today_departures": 0,
  "total_guests": 8,
  "monthly_revenue": 940.80,
  "all_time_revenue": 9301.20,
  "occupancy_rate": 13.3
}
```

---

### 2.2 `GET /api/dashboard/revenue-trend`
Supplies rolling 6-month historical revenue data for Chart.js rendering.

**Sample Response (`200 OK`):**
```json
{
  "labels": ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026"],
  "data": [0.00, 0.00, 0.00, 0.00, 2217.60, 7083.60]
}
```

---

### 2.3 `GET /api/dashboard/status-distribution`
Supplies reservation status distribution counts for Chart.js doughnut visualizations.

**Sample Response (`200 OK`):**
```json
{
  "labels": ["Confirmed", "Checked In", "Checked Out", "Cancelled", "Pending"],
  "data": [2, 2, 2, 1, 0]
}
```

---

## 3. Reservation Management Endpoints

### 3.1 `PATCH /api/reservations/<id>/check-in`
Executes front desk arrival check-in.
- **Success (`200 OK`)**: Returns updated reservation object with status `'checked_in'`.
- **Failure (`400 Bad Request`)**: When reservation is in an invalid transition state.

### 3.2 `PATCH /api/reservations/<id>/check-out`
Executes front desk departure check-out.
- **Success (`200 OK`)**: Returns updated reservation object with status `'checked_out'`.

### 3.3 `PATCH /api/reservations/<id>/cancel`
Cancels reservation and immediately frees room inventory.
- **Request Body (`application/json`)**: `{"reason": "Guest emergency"}`
- **Success (`200 OK`)**: Returns status `'cancelled'`.
