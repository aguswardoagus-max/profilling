-- Script untuk membuat database MySQL jika belum ada
-- Jalankan script ini di MySQL sebelum menjalankan aplikasi

-- Buat database jika belum ada
CREATE DATABASE IF NOT EXISTS clearance_facesearch 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Gunakan database
USE clearance_facesearch;

-- Catatan: Tabel-tabel akan dibuat otomatis oleh aplikasi saat pertama kali dijalankan
-- melalui fungsi init_database() di database.py

-- Tabel yang akan dibuat otomatis:
-- - users
-- - sessions
-- - user_activities
-- - system_settings
-- - api_keys
-- - profiling_data
-- - telegram_users (untuk whitelist Telegram bot)
-- - cek_plat_data



