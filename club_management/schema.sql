-- ================================================================
-- ClubHub — Club Management System
-- schema.sql: FRESH INSTALL ONLY
-- WARNING: Running this file drops and recreates all tables.
-- For an existing installation, use schema_updates.sql instead.
-- ================================================================

CREATE DATABASE IF NOT EXISTS club_management;
USE club_management;

-- Drop existing tables (safe order to respect foreign keys)
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS event_registrations;
DROP TABLE IF EXISTS password_reset_tokens;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS announcements;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS admins;

-- ── Admins ───────────────────────────────────────────────────────
CREATE TABLE admins (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  UNIQUE NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    club_name     VARCHAR(150)  NOT NULL DEFAULT 'My Club',
    club_type     ENUM('sports','private','campus','fitness') NOT NULL DEFAULT 'sports',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Members ──────────────────────────────────────────────────────
CREATE TABLE members (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(100)  NOT NULL,
    email            VARCHAR(150)  UNIQUE NOT NULL,
    password_hash    VARCHAR(255)  NOT NULL,
    phone            VARCHAR(20),
    club_affiliation VARCHAR(100)  DEFAULT 'General',
    club_type        ENUM('sports','private','campus','fitness') NOT NULL DEFAULT 'sports',
    membership_tier  VARCHAR(50)   DEFAULT 'Standard',
    renewal_date     DATE          NULL,
    status           ENUM('active','inactive','pending') DEFAULT 'pending',
    joined_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_bio      TEXT,
    profile_pic      VARCHAR(255) DEFAULT NULL,
    INDEX idx_email      (email),
    INDEX idx_status     (status),
    INDEX idx_joined_at  (joined_at),
    INDEX idx_club_type  (club_type),
    INDEX idx_renewal    (renewal_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Events ───────────────────────────────────────────────────────
CREATE TABLE events (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(200) NOT NULL,
    description    TEXT,
    event_date     DATE         NOT NULL,
    event_time     TIME,
    location       VARCHAR(200),
    instructor     VARCHAR(100),
    category       VARCHAR(50)  DEFAULT 'General',
    max_attendees  INT          DEFAULT 0,
    status         ENUM('scheduled','cancelled','completed') DEFAULT 'scheduled',
    created_by     INT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_event_date (event_date),
    INDEX idx_status     (status),
    INDEX idx_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Announcements ─────────────────────────────────────────────────
CREATE TABLE announcements (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(200) NOT NULL,
    content    TEXT         NOT NULL,
    priority   ENUM('low','medium','high') DEFAULT 'medium',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATE,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL,
    INDEX idx_expires_at (expires_at),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Password Reset Tokens ─────────────────────────────────────────
CREATE TABLE password_reset_tokens (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(150) NOT NULL,
    role       ENUM('admin','member') NOT NULL,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP   NOT NULL,
    used_at    TIMESTAMP   NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_token_hash (token_hash),
    INDEX idx_email      (email),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Event Registrations ───────────────────────────────────────────
CREATE TABLE event_registrations (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    event_id      INT NOT NULL,
    member_id     INT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id)  REFERENCES events(id)  ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    UNIQUE KEY unique_registration (event_id, member_id),
    INDEX idx_event_id  (event_id),
    INDEX idx_member_id (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Attendance ────────────────────────────────────────────────────
CREATE TABLE attendance (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    event_id   INT NOT NULL,
    member_id  INT NOT NULL,
    marked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id)  REFERENCES events(id)  ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (event_id, member_id),
    INDEX idx_event_id  (event_id),
    INDEX idx_member_id (member_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- Sample data for development
-- Default password for all sample accounts: password123
-- ================================================================
INSERT IGNORE INTO admins (name, email, password_hash, club_name, club_type) VALUES
('System Admin', 'admin@example.com',
 'pbkdf2:sha256:260000$salt0000$5e7f1c1dc3f9c9e9e5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3',
 'My Club', 'sports');

INSERT IGNORE INTO members (name, email, password_hash, phone, club_affiliation, club_type, membership_tier, status) VALUES
('Alice Johnson', 'alice@example.com',
 'pbkdf2:sha256:260000$salt1234$8ff3544c9e329ed408a8918d17311462dca65724f6f473ed4bdb6aa6843d1d51',
 '555-0101', 'Technology', 'sports', 'Standard', 'active'),
('Bob Smith', 'bob@example.com',
 'pbkdf2:sha256:260000$salt5678$bfb29b5fa9c164a0d918707e9bf2de22046730f3ff8cef80fe06d619cf59fc6e',
 '555-0102', 'Arts', 'sports', 'Standard', 'active'),
('Carol White', 'carol@example.com',
 'pbkdf2:sha256:260000$salt9012$d8002be3dd970ea27ce3f77c188775902b4e481f057ac094e0db9a4b9585989d',
 '555-0103', 'Sports', 'sports', 'Standard', 'active');
