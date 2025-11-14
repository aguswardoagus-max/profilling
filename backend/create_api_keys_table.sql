-- SQL Script untuk membuat tabel api_keys
-- Jalankan script ini di MySQL database Anda

-- Buat tabel api_keys untuk multiple API key management
CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    api_key VARCHAR(255) NOT NULL,
    api_type VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_CSE',
    status ENUM('active', 'quota_exceeded', 'disabled', 'error') NOT NULL DEFAULT 'active',
    usage_count INT DEFAULT 0,
    last_used TIMESTAMP NULL,
    quota_exceeded_at TIMESTAMP NULL,
    error_message TEXT,
    description VARCHAR(255),
    priority INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_api_type (api_type),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_status_priority (status, priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verifikasi tabel sudah dibuat
SELECT 'Tabel api_keys berhasil dibuat!' AS status;

-- Tampilkan struktur tabel
DESCRIBE api_keys;

