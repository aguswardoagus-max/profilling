# Telegram Bot untuk Profiling

Bot Telegram ini memungkinkan Anda untuk melakukan pencarian profiling melalui Telegram tanpa mengubah logic web yang sudah ada.

## Setup

1. Install dependencies:
```bash
pip install python-telegram-bot==20.7
```

2. Bot token sudah dikonfigurasi di `telegram_bot.py`:
   - Token: `7348743638:AAFfeaHBvnCpLbZ2JnKng0iwq2FG6oF7eTw`

3. Jalankan aplikasi seperti biasa:
```bash
python run.py
```

Bot akan otomatis berjalan di background thread bersamaan dengan Flask app.

## Penggunaan

### 1. Start Bot
Kirim `/start` ke bot untuk melihat menu bantuan.

### 2. Login
```
/login <username> <password>
```
Contoh:
```
/login admin password123
```

### 3. Cari Data Profiling
```
/search nama <nama>
/search nik <nik>
/search phone <nomor_hp>
```
Contoh:
```
/search nama Ahmad
/search nik 1505041107830002
/search phone 081234567890
```

### 4. Lihat Laporan
```
/reports
```

### 5. Logout
```
/logout
```

## Fitur

- ✅ Login/Logout
- ✅ Pencarian berdasarkan nama, NIK, atau nomor HP
- ✅ Melihat laporan profiling
- ✅ Detail lengkap dengan tombol inline
- ✅ Menggunakan API endpoints yang sama dengan web (tidak mengubah logic)

## Catatan

- Bot menggunakan API endpoints yang sama dengan web version
- Semua data diambil dari database yang sama
- Tidak ada perubahan pada logic web yang sudah ada
- Bot berjalan di thread terpisah sehingga tidak mengganggu Flask app




