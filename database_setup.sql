-- Database setup script for Clearance Face Search
-- Run this script to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS clearance_facesearch 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE clearance_facesearch;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user',
    status ENUM('active', 'inactive', 'pending') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create user activities table
CREATE TABLE IF NOT EXISTS user_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_activity_type (activity_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create system settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user
-- Password: admin123 (hashed with salt)
INSERT IGNORE INTO users (username, email, password_hash, full_name, role, status) 
VALUES (
    'admin', 
    'admin@clearancefacesearch.com', 
    'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 
    'System Administrator', 
    'admin', 
    'active'
);

-- Insert some sample users for testing
INSERT IGNORE INTO users (username, email, password_hash, full_name, role, status) 
VALUES 
(
    'user1', 
    'user1@example.com', 
    'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 
    'John Doe', 
    'user', 
    'active'
),
(
    'viewer1', 
    'viewer1@example.com', 
    'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 
    'Jane Smith', 
    'viewer', 
    'active'
);

-- Insert some system settings
INSERT IGNORE INTO system_settings (setting_key, setting_value, description) 
VALUES 
('app_name', 'Clearance Face Search', 'Application name'),
('app_version', '1.0.0', 'Application version'),
('max_login_attempts', '5', 'Maximum login attempts before account lock'),
('session_timeout', '24', 'Session timeout in hours'),
('maintenance_mode', 'false', 'Maintenance mode status');

-- Show tables
SHOW TABLES;

-- Show users
SELECT id, username, email, full_name, role, status, created_at FROM users;
