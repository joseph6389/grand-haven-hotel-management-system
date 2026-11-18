-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase II: Synthetic Dataset Population
-- Target: MySQL Server 8.0+
-- ============================================================================

USE hotelreservationdb;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Insert Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'admin', 'Complete property administration, financial reconciliation, and user management'),
(2, 'receptionist', 'Front desk reservations, guest folio management, check-in, and check-out'),
(3, 'guest', 'Guest reservation and profile self-service')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- 2. Insert Staff Users
-- Password hashes use Werkzeug scrypt format.
-- DEVELOPMENT ONLY: Seed accounts are for local testing.
-- Change default credentials before any production deployment.
INSERT INTO users (id, username, email, password_hash, full_name, phone, role_id, is_active) VALUES
(1, 'admin', 'admin@grandhavenhotel.com', 'scrypt:32768:8:1$qrZ6Vj3DDBwaVpNh$354aa7df636d21fa4bea634d5dc3331417419a5b464425120523b07dba65a7e68d08bd5b82931d34cd10ee567677708b71f60027de306e6d1ac04df6c9236700', 'Alexander Vance', '+91 98765 43210', 1, TRUE),
(2, 'receptionist', 'reception@grandhavenhotel.com', 'scrypt:32768:8:1$2SeebdKEvbHTsUyp$31b3c7d80e4549e946e8af158144336ea1d85e0bc7472ecc624af0f52a33a06cebc5e4fa1442e1da6e4508f1bb201ec83d86b2dab950528d351d27b5ad8a0bfc', 'Elena Rostova','+91 98765 43211', 2, TRUE)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 3. Insert Amenities
INSERT INTO amenities (id, name, icon, category) VALUES
(1, 'Oceanfront Balcony', 'bi-water', 'View'),
(2, 'King Featherbed', 'bi-moon-stars', 'Comfort'),
(3, 'High-Speed Fiber Wi-Fi', 'bi-wifi', 'Technology'),
(4, 'Marble Jacuzzi Tub', 'bi-droplet', 'Bathroom'),
(5, 'Nespresso Artisan Bar', 'bi-cup-hot', 'Refreshment'),
(6, '65" 4K OLED Screen', 'bi-tv', 'Entertainment'),
(7, 'Dedicated Butler Service', 'bi-bell', 'Service'),
(8, 'Smart Climate Control', 'bi-snow', 'Comfort'),
(9, 'Rainfall Shower', 'bi-cloud-rain', 'Bathroom'),
(10, 'Mini Bar & Wine Cellar', 'bi-cup-straw', 'Refreshment')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 4. Insert Room Types
INSERT INTO room_types (id, code, name, description, base_price, default_capacity, max_capacity, bed_type, image_url) VALUES
(1, 'STD', 'Classic King Sanctuary', 'A serene refuge featuring an imported king featherbed, warm walnut finishes, custom acoustic soundproofing, and a spa-inspired rainfall bath.', 12000.00, 2, 2, '1 King Bed', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1000&q=80'),
(2, 'DLX', 'Deluxe Oceanfront Haven', 'Panoramic floor-to-ceiling coastal vistas overlooking the Atlantic breakers. Features private terrace, oversized marble bathroom, and artisan bar.', 18000.00, 2, 3, '1 King Bed + Daybed', 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1000&q=80'),
(3, 'STE', 'Grand Harbor Executive Suite', 'Expansive residential luxury featuring separated entertaining salon, master bedroom suite, dual vanity dressing room, and bespoke hospitality lounge.', 42000.00, 3, 4, '1 King + Living Sofa Bed', 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1000&q=80'),
(4, 'PRE', 'Presidential Panorama Penthouse', 'The pinnacle of Grand Haven hospitality. Private rooftop glass terrace, 360-degree ocean views, dining parlor for eight, and private butler service.', 85000.00, 4, 6, '2 King Beds + Master Parlor', 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1000&q=80')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 5. Insert Physical Rooms (16 units across 4 floors)
INSERT INTO rooms (id, room_number, room_type_id, floor, capacity, operational_status, is_active, notes) VALUES
(1, '101', 1, 1, 2, 'operational', TRUE, 'Quiet garden facing room'),
(2, '102', 1, 1, 2, 'operational', TRUE, 'Convenient ground level access'),
(3, '103', 2, 1, 3, 'operational', TRUE, 'Direct beach access terrace'),
(4, '104', 2, 1, 3, 'operational', TRUE, 'Garden and ocean horizon blend'),
(5, '201', 1, 2, 2, 'operational', TRUE, 'Elevated ocean breeze view'),
(6, '202', 1, 2, 2, 'operational', TRUE, 'Contemporary interior finish'),
(7, '203', 2, 2, 3, 'operational', TRUE, 'Full unobstructed oceanfront view'),
(8, '204', 2, 2, 3, 'maintenance', TRUE, 'Scheduled plumbing overhaul (demo maintenance filter)'),
(9, '301', 2, 3, 3, 'operational', TRUE, 'Panoramic sea vista'),
(10, '302', 2, 3, 3, 'operational', TRUE, 'Corner suite perspective'),
(11, '303', 3, 3, 4, 'operational', TRUE, 'Executive corner suite with dual wrap balcony'),
(12, '304', 3, 3, 4, 'operational', TRUE, 'Luxury living parlor suite'),
(13, '401', 3, 4, 4, 'operational', TRUE, 'Top-floor harbor executive suite'),
(14, '402', 3, 4, 4, 'operational', TRUE, 'High-ceiling master salon suite'),
(15, '403', 4, 4, 6, 'operational', TRUE, 'The Grand Haven Presidential Penthouse'),
(16, '404', 4, 4, 6, 'operational', TRUE, 'The Royal Ocean Pavilion Penthouse')
ON DUPLICATE KEY UPDATE operational_status=VALUES(operational_status);

-- 6. Insert Room Amenities Associations
INSERT IGNORE INTO room_amenities (room_id, amenity_id) VALUES
(1, 2), (1, 3), (1, 9), (1, 5), (1, 8),
(2, 2), (2, 3), (2, 9), (2, 5), (2, 8),
(3, 1), (3, 2), (3, 3), (3, 4), (3, 6), (3, 5),
(4, 1), (4, 2), (4, 3), (4, 4), (4, 6), (4, 5),
(7, 1), (7, 2), (7, 3), (7, 4), (7, 6), (7, 5),
(11, 1), (11, 2), (11, 3), (11, 4), (11, 6), (11, 7), (11, 10),
(12, 1), (12, 2), (12, 3), (12, 4), (12, 6), (12, 7), (12, 10),
(15, 1), (15, 2), (15, 3), (15, 4), (15, 6), (15, 7), (15, 8), (15, 10),
(16, 1), (16, 2), (16, 3), (16, 4), (16, 6), (16, 7), (16, 8), (16, 10);

-- 7. Insert Guests
INSERT INTO guests (id, first_name, last_name, email, phone, address, city, country, identification_type, identification_number) VALUES
(1, 'Julian', 'Thorne', 'julian.thorne@example.com', '+91 9876500011', '12 Example Residency', 'Bengaluru', 'India', 'Passport', 'P9841203A'),
(2, 'Vivienne', 'St. Claire', 'vivienne.stclaire@example.com', '+91 9876500012', '24 Lake View Road', 'Mysuru', 'India', 'Passport', 'P7739102B'),
(3, 'Marcus', 'Sterling', 'marcus.sterling@example.com', '+91 9876500013', '8 Market Street', 'Kochi', 'India', 'Passport', 'GB8821901'),
(4, 'Sophia', 'Chen', 'sophia.chen@example.com', '+91 9876500014', '16 Garden Lane', 'Chennai', 'India', 'Driver License', 'BC-4491029'),
(5, 'Liam', 'Gallagher', 'liam.gallagher@example.com', '+91 9876500015', '31 Residency Road', 'Bengaluru', 'India', 'Passport', 'IE5512903'),
(6, 'Aris', 'Vanderbilt', 'aris.vanderbilt@example.com', '+91 9876500016', '5 Hill View', 'Pune', 'India', 'Passport', 'P1298402X'),
(7, 'Camille', 'Dupont', 'camille.dupont@example.com', '+91 9876500017', '19 Riverside Avenue', 'Kochi', 'India', 'Passport', 'FR9021482'),
(8, 'Hiroshi', 'Tanaka', 'hiroshi.tanaka@example.com', '+91 9876500018', '42 Park Street', 'Kolkata', 'India', 'Passport', 'JP7749102')
ON DUPLICATE KEY UPDATE email=VALUES(email);

-- 8. Insert Extra Services
INSERT INTO services (id, name, description, unit_price, is_active) VALUES
(1, 'Airport Luxury Chauffeur', 'Private Mercedes S-Class transfer between airport and hotel', 5000.00, TRUE),
(2, 'Couples Ocean Spa Ritual', '90-minute aromatherapy massage overlooking the sea', 8000.00, TRUE),
(3, 'Champagne Breakfast Buffet', 'Artisan bakery, caviar station, and vintage champagne service', 1500.00, TRUE),
(4, 'Valet Parking Service', 'Secured 24-hour underground valet parking', 1000.00, TRUE),
(5, 'Private Yacht Sunset Charter', '2-hour private yacht cruise along the coastline', 25000.00, TRUE)
ON DUPLICATE KEY UPDATE unit_price=VALUES(unit_price);

-- 9. Insert Reservations (Past, Active, Future, Cancelled)
INSERT INTO reservations (id, confirmation_number, guest_id, check_in_date, check_out_date, adults_count, children_count, tax_amount, discount_amount, status, special_requests, created_by_id) VALUES

(1, 'GH-20260901-7A1C', 1, '2026-09-01', '2026-09-05', 2, 0, 5760.00, 0.00, 'checked_out', 'High floor preferred, late arrival.', 1),
(2, 'GH-20260910-3F8E', 2, '2026-09-10', '2026-09-13', 2, 1, 15120.00, 0.00, 'checked_out', 'Celebrating wedding anniversary. Chilled champagne in suite.', 1),
(3, 'GH-20261014-9B2D', 3, '2026-10-14', '2026-10-18', 2, 0, 8640.00, 0.00, 'checked_in', 'Extra feather pillows requested.', 1),
(4, 'GH-20261015-4E1A', 4, '2026-10-15', '2026-10-19', 4, 0, 40800.00, 0.00, 'checked_in', 'Presidential butler orientation requested.', 1),
(5, 'GH-20261018-8A3F', 5, '2026-10-18', '2026-10-22', 2, 0, 8640.00, 0.00, 'confirmed', 'Airport transfer booking required.', 1),
(6, 'GH-20261020-5C2B', 6, '2026-10-20', '2026-10-24', 3, 1, 20160.00, 0.00, 'confirmed', 'Child cot and baby highchair required.', 1),
(7, 'GH-20261016-1D9X', 7, '2026-10-17', '2026-10-20', 2, 0, 4320.00, 0.00, 'cancelled', 'Flight cancelled due to storm.', 1)
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- 10. Insert Reservation Room Allocations
INSERT INTO reservation_rooms (id, reservation_id, room_id, nightly_rate, nights) VALUES
(1, 1, 1, 12000.00, 4),
(2, 2, 11, 42000.00, 3),
(3, 3, 7, 18000.00, 4),
(4, 4, 15, 85000.00, 4),
(5, 5, 3, 18000.00, 4),
(6, 6, 12, 42000.00, 4),
(7, 7, 5, 12000.00, 3)
ON DUPLICATE KEY UPDATE nightly_rate=VALUES(nightly_rate), nights=VALUES(nights);

-- 11. Insert Payments
INSERT INTO payments (id, reservation_id, payment_reference, amount, currency, payment_method, payment_status, transaction_reference, notes, processed_by_id) VALUES
(1, 1, 'PAY-20260901-7A1C-1', 53760.00, 'INR', 'credit_card', 'paid', 'SIM-TXN-1001', 'Settled upon departure', 1),
(2, 2, 'PAY-20260910-3F8E-1', 141120.00, 'INR', 'credit_card', 'paid', 'SIM-TXN-1002', 'Full advance settlement', 1),
(3, 3, 'PAY-20261014-9B2D-1', 80640.00, 'INR', 'credit_card', 'paid', 'SIM-TXN-1003', 'Initial check-in payment', 1),
(4, 4, 'PAY-20261015-4E1A-1', 380800.00, 'INR', 'bank_transfer', 'paid', 'SIM-TXN-1004', 'Wire transfer deposit confirmed', 1),
(5, 5, 'PAY-20261018-8A3F-1', 80640.00, 'INR', 'credit_card', 'paid', 'SIM-TXN-1005', 'Online advance payment', 1),
(6, 6, 'PAY-20261020-5C2B-1', 94080.00, 'INR', 'credit_card', 'paid', 'SIM-TXN-1006', '50% booking deposit paid', 1)
ON DUPLICATE KEY UPDATE amount=VALUES(amount);

-- 12. Insert Hotel Settings
INSERT INTO hotel_settings (setting_key, setting_value, setting_type, description) VALUES
('HOTEL_NAME', 'Grand Haven Hotel', 'string', 'Hotel property brand name'),
('HOTEL_EMAIL', 'reservations@grandhavenhotel.com', 'string', 'Concierge email address'),
('HOTEL_PHONE', '', 'string', 'Configure the verified front desk telephone'),
('HOTEL_CURRENCY', 'INR', 'string', 'Standard operating currency'),
('HOTEL_TAX_RATE', '0.12', 'float', 'Lodging tax multiplier'),
('DEFAULT_CHECKIN_TIME', '15:00', 'string', 'Standard check-in time'),
('DEFAULT_CHECKOUT_TIME', '11:00', 'string', 'Standard check-out time'),
('CANCELLATION_POLICY', 'Full refund available if cancelled 48 hours before check-in date.', 'string', 'Terms')
ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value);

SET FOREIGN_KEY_CHECKS = 1;

-- Verification of seeded counts
SELECT
  (SELECT COUNT(*) FROM roles) AS total_roles,
  (SELECT COUNT(*) FROM users) AS total_users,
  (SELECT COUNT(*) FROM guests) AS total_guests,
  (SELECT COUNT(*) FROM room_types) AS total_room_types,
  (SELECT COUNT(*) FROM rooms) AS total_rooms,
  (SELECT COUNT(*) FROM reservations) AS total_reservations,
  (SELECT COUNT(*) FROM payments) AS total_payments;
