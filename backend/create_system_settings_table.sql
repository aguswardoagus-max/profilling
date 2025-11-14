-- SQL Script untuk membuat tabel system_settings
-- Jalankan script ini di MySQL database Anda

-- Buat tabel system_settings jika belum ada
CREATE TABLE IF NOT EXISTS system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verifikasi tabel sudah dibuat
SELECT 'Tabel system_settings berhasil dibuat!' AS status;

-- Tampilkan struktur tabel
DESCRIBE system_settings;

