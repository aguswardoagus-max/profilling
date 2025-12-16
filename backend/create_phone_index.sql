-- Script untuk membuat index pada kolom hp di tabel penduduk
-- Index ini sangat penting untuk mempercepat query di database besar (30 juta record)
-- Jalankan script ini di MySQL/MariaDB server dengan akses admin

USE sipudat1;

-- Buat index pada kolom hp (kolom utama untuk pencarian nomor HP)
-- Index akan mempercepat query SELECT dengan WHERE hp = ...
CREATE INDEX IF NOT EXISTS idx_hp ON penduduk(hp);

-- Buat index pada kolom phone jika ada (fallback)
CREATE INDEX IF NOT EXISTS idx_phone ON penduduk(phone);

-- Buat index pada kolom nomor_hp jika ada (fallback)
CREATE INDEX IF NOT EXISTS idx_nomor_hp ON penduduk(nomor_hp);

-- Tampilkan index yang sudah dibuat
SHOW INDEX FROM penduduk WHERE Column_name IN ('hp', 'phone', 'nomor_hp');

-- Catatan:
-- - Index akan mempercepat query SELECT dengan WHERE clause pada kolom tersebut
-- - Index membutuhkan ruang disk tambahan, tapi sangat penting untuk performa
-- - Setelah index dibuat, query akan jauh lebih cepat (dari beberapa menit menjadi beberapa detik)

