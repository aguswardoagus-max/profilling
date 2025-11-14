#!/usr/bin/env python3
"""
Script sederhana untuk membuat tabel system_settings secara manual
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_system_settings_table():
    """Buat tabel system_settings secara manual"""
    
    # Konfigurasi database
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'clearance_facesearch')
    }
    
    print("=" * 60)
    print("MEMBUAT TABEL system_settings")
    print("=" * 60)
    print(f"Database: {config['database']}")
    print(f"Host: {config['host']}:{config['port']}")
    print(f"User: {config['user']}")
    print()
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("✅ Terhubung ke database")
        
        # Create table
        print("\n📝 Membuat tabel system_settings...")
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
        
        connection.commit()
        print("✅ Tabel system_settings berhasil dibuat!")
        
        # Verify table exists
        print("\n🔍 Memverifikasi tabel...")
        cursor.execute("SHOW TABLES LIKE 'system_settings'")
        result = cursor.fetchone()
        
        if result:
            print("✅ Tabel ditemukan di database")
            
            # Show table structure
            print("\n📋 Struktur tabel:")
            cursor.execute("DESCRIBE system_settings")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[0]:20} {col[1]:20} {col[2]}")
            
            # Check if table is empty
            cursor.execute("SELECT COUNT(*) FROM system_settings")
            count = cursor.fetchone()[0]
            print(f"\n📊 Jumlah data: {count} record(s)")
            
            if count == 0:
                print("   (Tabel kosong - siap digunakan)")
            else:
                print("\n📝 Data yang ada:")
                cursor.execute("SELECT setting_key, LEFT(setting_value, 30) as value_preview, description FROM system_settings")
                rows = cursor.fetchall()
                for row in rows:
                    print(f"   - {row[0]}: {row[1]}...")
        
        print("\n" + "=" * 60)
        print("✅ SELESAI - Tabel system_settings siap digunakan!")
        print("=" * 60)
        print("\n💡 Sekarang Anda bisa:")
        print("   1. Menjalankan aplikasi: python app.py")
        print("   2. Mengakses Settings page untuk menambahkan API key")
        print("   3. API key akan tersimpan di tabel ini")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Pastikan:")
        print("   1. MySQL server sedang berjalan")
        print("   2. Database 'clearance_facesearch' sudah dibuat")
        print("   3. User memiliki permission untuk create table")
        print("   4. Konfigurasi di .env file sudah benar")
        return False

if __name__ == "__main__":
    success = create_system_settings_table()
    exit(0 if success else 1)

