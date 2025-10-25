#!/usr/bin/env python3
"""
Simple Database Setup Script for Clearance Face Search
"""

import mysql.connector
from mysql.connector import Error
import os

def get_db_config():
    """Get database configuration"""
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
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
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
        print("Users table created successfully")
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_token VARCHAR(191) UNIQUE NOT NULL,
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
        print("Sessions table created successfully")
        
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
        print("User activities table created successfully")
        
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
        print("System settings table created successfully")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error creating tables: {e}")
        return False

def create_admin_user():
    """Create default admin user"""
    config = get_db_config()
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("Admin user already exists")
            cursor.close()
            connection.close()
            return True
        
        # Create admin user with hashed password (admin123)
        admin_password_hash = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', ('admin', 'admin@clearancefacesearch.com', admin_password_hash, 'System Administrator', 'admin', 'active'))
        
        print("Default admin user created successfully")
        print("Username: admin")
        print("Password: admin123")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"Error creating admin user: {e}")
        return False

def test_connection():
    """Test database connection"""
    config = get_db_config()
    database_name = config.pop('database')
    
    try:
        # First test connection without database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"Connected to MySQL version: {version[0]}")
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Error testing connection: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up Clearance Face Search Database...")
    print("=" * 50)
    
    # Test connection first
    print("\n1. Testing database connection...")
    if not test_connection():
        print("Cannot connect to database. Please check your configuration.")
        print("\nMake sure to set these environment variables:")
        print("  DB_HOST=localhost")
        print("  DB_PORT=3306")
        print("  DB_USER=root")
        print("  DB_PASSWORD=your_password")
        print("  DB_NAME=clearance_facesearch")
        return False
    
    # Create database
    print("\n2. Creating database...")
    if not create_database():
        return False
    
    # Create tables
    print("\n3. Creating tables...")
    if not create_tables():
        return False
    
    # Create default admin
    print("\n4. Creating default admin user...")
    if not create_admin_user():
        return False
    
    print("\n" + "=" * 50)
    print("Database setup completed successfully!")
    print("\nDefault login credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nYou can now run the application with: python app.py")
    return True

if __name__ == "__main__":
    main()
