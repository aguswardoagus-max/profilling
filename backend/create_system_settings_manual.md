# Cara Manual Membuat Tabel system_settings

## Opsi 1: Menggunakan MySQL Command Line

```bash
# Login ke MySQL
mysql -u root -p

# Pilih database
USE clearance_facesearch;

# Jalankan SQL script
SOURCE backend/create_system_settings_table.sql;

# Atau copy-paste SQL langsung:
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Opsi 2: Menggunakan phpMyAdmin atau MySQL Workbench

1. Buka phpMyAdmin atau MySQL Workbench
2. Pilih database `clearance_facesearch`
3. Buka tab SQL
4. Copy-paste SQL berikut:

```sql
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

5. Klik "Go" atau "Execute"

## Opsi 3: Menggunakan Python Script

Jalankan script Python sederhana:

```python
import mysql.connector
import os

# Konfigurasi database
config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'clearance_facesearch')
}

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    
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
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
```

## Verifikasi

Setelah membuat tabel, verifikasi dengan:

```sql
-- Cek apakah tabel ada
SHOW TABLES LIKE 'system_settings';

-- Lihat struktur tabel
DESCRIBE system_settings;

-- Atau
SHOW CREATE TABLE system_settings;
```

