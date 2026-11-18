-- ============================================================================
-- GRAND HAVEN HOTEL — HOTEL RESERVATION MANAGEMENT SYSTEM
-- ADBMS Phase II: MySQL Schema DDL Script
-- Target Engine: MySQL Server 8.0+ (InnoDB Engine)
-- ============================================================================

-- Canonical application database: hotelreservationdb (the configured live schema).
-- This script is for a new schema. IF NOT EXISTS does not migrate existing tables.
CREATE DATABASE IF NOT EXISTS hotelreservationdb
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE hotelreservationdb;

-- Disable foreign key checks during batch table creation
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. ROLES TABLE (RBAC Security)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_roles_name (name)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. USERS TABLE (Hotel Staff & Administrators)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  phone VARCHAR(30) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  role_id INT NOT NULL,
  guest_profile_id INT NULL,
  last_login DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT,
  INDEX idx_users_username (username),
  INDEX idx_users_email (email),
  UNIQUE KEY uq_users_guest_profile (guest_profile_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. GUESTS TABLE (Guest Directory)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS guests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(60) NOT NULL,
  last_name VARCHAR(60) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  phone VARCHAR(30) NOT NULL,
  address VARCHAR(255) NULL,
  city VARCHAR(100) NULL,
  state VARCHAR(100) NULL,
  postal_code VARCHAR(20) NULL,
  country VARCHAR(100) NULL DEFAULT 'India',
  identification_type VARCHAR(50) NULL,
  identification_number VARCHAR(100) NULL,
  notes TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_guests_names (last_name, first_name),
  INDEX idx_guests_email (email),
  INDEX idx_guests_phone (phone)
) ENGINE=InnoDB;

ALTER TABLE users
  ADD CONSTRAINT fk_users_guest_profile FOREIGN KEY (guest_profile_id)
  REFERENCES guests (id) ON DELETE SET NULL;

-- ----------------------------------------------------------------------------
-- 4. ROOM_TYPES TABLE (Room Classifications & Base Rates)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS room_types (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description TEXT NULL,
  base_price DECIMAL(10, 2) NOT NULL,
  default_capacity INT NOT NULL DEFAULT 2,
  max_capacity INT NOT NULL DEFAULT 4,
  bed_type VARCHAR(80) NOT NULL DEFAULT '1 King Bed',
  image_url VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_room_type_price CHECK (base_price >= 0.00),
  CONSTRAINT chk_room_type_capacity CHECK (max_capacity >= default_capacity),
  INDEX idx_room_types_code (code)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. AMENITIES TABLE (Property & Room Features)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS amenities (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  icon VARCHAR(50) NULL DEFAULT 'bi-check-circle',
  category VARCHAR(50) NULL DEFAULT 'General',
  INDEX idx_amenities_name (name)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. ROOMS TABLE (Physical Hotel Inventory)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rooms (
  id INT AUTO_INCREMENT PRIMARY KEY,
  room_number VARCHAR(20) NOT NULL UNIQUE,
  room_type_id INT NOT NULL,
  floor INT NOT NULL DEFAULT 1,
  capacity INT NOT NULL DEFAULT 2,
  operational_status ENUM('operational', 'maintenance', 'out_of_order') NOT NULL DEFAULT 'operational',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  notes TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_rooms_room_type FOREIGN KEY (room_type_id) REFERENCES room_types (id) ON DELETE RESTRICT,
  CONSTRAINT chk_rooms_floor CHECK (floor > 0),
  CONSTRAINT chk_rooms_capacity CHECK (capacity > 0),
  INDEX idx_rooms_number (room_number),
  INDEX idx_rooms_status (operational_status),
  INDEX idx_rooms_floor (floor)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. ROOM_AMENITIES TABLE (Normalized M:N Association)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS room_amenities (
  room_id INT NOT NULL,
  amenity_id INT NOT NULL,
  PRIMARY KEY (room_id, amenity_id),
  CONSTRAINT fk_ra_room FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE CASCADE,
  CONSTRAINT fk_ra_amenity FOREIGN KEY (amenity_id) REFERENCES amenities (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8. RESERVATIONS TABLE (Master Booking Records)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  confirmation_number VARCHAR(32) NOT NULL UNIQUE,
  guest_id INT NOT NULL,
  check_in_date DATE NOT NULL,
  check_out_date DATE NOT NULL,
  adults_count INT NOT NULL DEFAULT 1,
  children_count INT NOT NULL DEFAULT 0,
  tax_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  status ENUM('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled') NOT NULL DEFAULT 'confirmed',
  special_requests TEXT NULL,
  created_by_id INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_res_guest FOREIGN KEY (guest_id) REFERENCES guests (id) ON DELETE RESTRICT,
  CONSTRAINT fk_res_user FOREIGN KEY (created_by_id) REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT chk_res_dates CHECK (check_out_date > check_in_date),
  INDEX idx_res_confirmation (confirmation_number),
  INDEX idx_res_dates (check_in_date, check_out_date),
  INDEX idx_res_status (status),
  INDEX idx_res_guest (guest_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 9. RESERVATION_ROOMS TABLE (Room Allocations with Rate Snapshots)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservation_rooms (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_id INT NOT NULL,
  room_id INT NOT NULL,
  nightly_rate DECIMAL(10, 2) NOT NULL,
  nights INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_reservation_room UNIQUE (reservation_id, room_id),
  CONSTRAINT fk_rr_reservation FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE CASCADE,
  CONSTRAINT fk_rr_room FOREIGN KEY (room_id) REFERENCES rooms (id) ON DELETE RESTRICT,
  CONSTRAINT chk_rr_rate CHECK (nightly_rate >= 0.00),
  CONSTRAINT chk_rr_nights CHECK (nights > 0),
  INDEX idx_rr_res_id (reservation_id),
  INDEX idx_rr_room_id (room_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 10. RESERVATION_STATUS_HISTORY TABLE (Lifecycle Audit Progression)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservation_status_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_id INT NOT NULL,
  previous_status VARCHAR(20) NULL,
  new_status VARCHAR(20) NOT NULL,
  changed_by_id INT NULL,
  reason VARCHAR(255) NULL,
  request_source VARCHAR(20) NULL,
  requested_by_guest_id INT NULL,
  cancellation_fee DECIMAL(10, 2) NULL,
  refund_status VARCHAR(30) NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rsh_res FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE CASCADE,
  CONSTRAINT fk_rsh_user FOREIGN KEY (changed_by_id) REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT fk_rsh_request_guest FOREIGN KEY (requested_by_guest_id) REFERENCES guests (id) ON DELETE SET NULL,
  INDEX idx_rsh_res_id (reservation_id),
  INDEX idx_rsh_request_guest (requested_by_guest_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 11. PAYMENTS TABLE (Financial Transactions & Refunds)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_id INT NOT NULL,
  payment_reference VARCHAR(40) NOT NULL UNIQUE,
  amount DECIMAL(10, 2) NOT NULL,
  refunded_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  currency VARCHAR(3) NOT NULL DEFAULT 'INR',
  payment_method VARCHAR(30) NOT NULL DEFAULT 'credit_card',
  payment_status ENUM('paid', 'partially_refunded', 'refunded', 'failed') NOT NULL DEFAULT 'paid',
  transaction_reference VARCHAR(100) NULL,
  notes VARCHAR(255) NULL,
  processed_by_id INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_pay_res FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE RESTRICT,
  CONSTRAINT fk_pay_user FOREIGN KEY (processed_by_id) REFERENCES users (id) ON DELETE SET NULL,
  CONSTRAINT chk_pay_amount CHECK (amount > 0.00),
  CONSTRAINT chk_pay_refunded_amount CHECK (refunded_amount >= 0.00 AND refunded_amount <= amount),
  INDEX idx_pay_reference (payment_reference),
  INDEX idx_pay_res_id (reservation_id),
  INDEX idx_pay_status (payment_status),
  INDEX idx_pay_created (created_at)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 12. SERVICES TABLE (Ancillary Hotel Amenities)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS services (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255) NULL,
  unit_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_service_price CHECK (unit_price >= 0.00)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 13. RESERVATION_SERVICES TABLE (Ancillary Line Items)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservation_services (
  id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_id INT NOT NULL,
  service_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  unit_price DECIMAL(10, 2) NOT NULL,
  service_date DATE NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rs_res FOREIGN KEY (reservation_id) REFERENCES reservations (id) ON DELETE CASCADE,
  CONSTRAINT fk_rs_service FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE RESTRICT,
  CONSTRAINT chk_rs_qty CHECK (quantity > 0)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 14. AUDIT_LOGS TABLE (System-Wide Security & Event Audit)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  action VARCHAR(50) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id VARCHAR(50) NULL,
  details TEXT NULL,
  ip_address VARCHAR(45) NULL,
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
  INDEX idx_audit_action (action),
  INDEX idx_audit_entity (entity_type, entity_id),
  INDEX idx_audit_timestamp (timestamp)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 15. HOTEL_SETTINGS TABLE (Runtime System Parameters)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hotel_settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  setting_key VARCHAR(50) NOT NULL UNIQUE,
  setting_value TEXT NOT NULL,
  setting_type VARCHAR(20) NOT NULL DEFAULT 'string',
  description VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_settings_key (setting_key)
) ENGINE=InnoDB;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Verification of created tables
SHOW TABLES;
