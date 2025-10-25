#!/usr/bin/env python3
"""
Database setup script for Clearance Face Search
This script will create the database and tables if they don't exist
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
from pathlib import Path

def get_db_config():
    """Get database configuration from environment variables or defaults"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'clearance_facesearch')
    }

def create_database():
    """Create database if it doesn't exist"""
    config = get_db_config()
    database_name = config.pop('database')
    
    try:
        # Connect without specifying database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{database_name}' created successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error creating database: {e}")
        return False

def create_tables():
    """Create tables in the database"""
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Users table
        cursor.execute('''
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        print("✅ Users table created successfully")
        
        # Sessions table
        cursor.execute('''
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        print("✅ Sessions table created successfully")
        
        # User activities table
        cursor.execute('''
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        print("✅ User activities table created successfully")
        
        # System settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_setting_key (setting_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        print("✅ System settings table created successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error creating tables: {e}")
        return False

def create_default_admin():
    """Create default admin user"""
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("✅ Admin user already exists")
            cursor.close()
            connection.close()
            return True
        
        # Create admin user with hashed password (admin123)
        # This is a sample hash - in production, use proper password hashing
        admin_password_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('admin', 'admin@clearancefacesearch.com', admin_password_hash, 'System Administrator', 'admin', 'active'))
        
        print("✅ Default admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error creating admin user: {e}")
        return False

def insert_sample_data():
    """Insert sample data for testing"""
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Sample users
        sample_users = [
            ('user1', 'user1@example.com', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'John Doe', 'user', 'active'),
            ('viewer1', 'viewer1@example.com', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'Jane Smith', 'viewer', 'active'),
            ('user2', 'user2@example.com', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'Bob Johnson', 'user', 'pending')
        ]
        
        for user_data in sample_users:
            cursor.execute('''
                INSERT IGNORE INTO users (username, email, password_hash, full_name, role, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', user_data)
        
        # System settings
        settings = [
            ('app_name', 'Clearance Face Search', 'Application name'),
            ('app_version', '1.0.0', 'Application version'),
            ('max_login_attempts', '5', 'Maximum login attempts before account lock'),
            ('session_timeout', '24', 'Session timeout in hours'),
            ('maintenance_mode', 'false', 'Maintenance mode status')
        ]
        
        for setting in settings:
            cursor.execute('''
                INSERT IGNORE INTO system_settings (setting_key, setting_value, description)
                VALUES (%s, %s, %s)
            ''', setting)
        
        print("✅ Sample data inserted successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error inserting sample data: {e}")
        return False

def test_connection():
    """Test database connection"""
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Connected to MySQL version: {version[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Found {user_count} users in database")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error testing connection: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Clearance Face Search Database...")
    print("=" * 50)
    
    # Test connection first
    print("\n1. Testing database connection...")
    if not test_connection():
        print("❌ Cannot connect to database. Please check your configuration.")
        print("\nMake sure to set these environment variables:")
        print("  DB_HOST=localhost")
        print("  DB_PORT=3306")
        print("  DB_USER=root")
        print("  DB_PASSWORD=your_password")
        print("  DB_NAME=clearance_facesearch")
        sys.exit(1)
    
    # Create database
    print("\n2. Creating database...")
    if not create_database():
        sys.exit(1)
    
    # Create tables
    print("\n3. Creating tables...")
    if not create_tables():
        sys.exit(1)
    
    # Create default admin
    print("\n4. Creating default admin user...")
    if not create_default_admin():
        sys.exit(1)
    
    # Insert sample data
    print("\n5. Inserting sample data...")
    if not insert_sample_data():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\nDefault login credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nYou can now run the application with: python app.py")

if __name__ == "__main__":
    main()
