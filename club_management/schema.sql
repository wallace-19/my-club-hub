-- Club Management System Database Schema
-- Run this file to initialize the database

CREATE DATABASE IF NOT EXISTS club_management;
USE club_management;

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Members table
CREATE TABLE IF NOT EXISTS members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    club_affiliation VARCHAR(100) DEFAULT 'General',
    status ENUM('active', 'inactive', 'pending') DEFAULT 'active',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    profile_bio TEXT
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_time TIME,
    location VARCHAR(200),
    category VARCHAR(50) DEFAULT 'General',
    max_attendees INT DEFAULT 0,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
);

-- Announcements table
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATE,
    FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
);

-- Event registrations (members signing up for events)
CREATE TABLE IF NOT EXISTS event_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    member_id INT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    UNIQUE KEY unique_registration (event_id, member_id)
);

-- Insert default admin (password: admin123)
INSERT IGNORE INTO admins (name, email, password_hash) VALUES
('System Admin', 'admin@clubmanager.com', 'pbkdf2:sha256:260000$placeholder$hash');

-- Sample data for development
INSERT IGNORE INTO members (name, email, password_hash, phone, club_affiliation, status) VALUES
('Alice Johnson', 'alice@example.com', 'pbkdf2:sha256:placeholder', '555-0101', 'Technology', 'active'),
('Bob Smith', 'bob@example.com', 'pbkdf2:sha256:placeholder', '555-0102', 'Arts', 'active'),
('Carol White', 'carol@example.com', 'pbkdf2:sha256:placeholder', '555-0103', 'Sports', 'active');
