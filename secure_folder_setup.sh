#!/bin/bash

# 🔒 Clearance Face Search - Secure Folder Setup (Linux/Mac)

echo "🔒 Clearance Face Search - Secure Folder Setup"
echo "================================================"

# Buat folder tersembunyi
SECURE_FOLDER=".clearance_app"

if [ ! -d "$SECURE_FOLDER" ]; then
    mkdir "$SECURE_FOLDER"
    echo "✅ Folder $SECURE_FOLDER berhasil dibuat"
else
    echo "✅ Folder $SECURE_FOLDER sudah ada"
fi

# Daftar file yang perlu dipindahkan
FILES_TO_MOVE=(
    "app.py"
    "database.py"
    "cekplat.py"
    "clearance_face_search.py"
    "run_app.py"
    "requirements.txt"
    "config_example.env"
    "database_setup.sql"
    "setup_database.py"
)

# Pindahkan file ke folder aman
echo "📁 Memindahkan file ke folder aman..."
for file in "${FILES_TO_MOVE[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$SECURE_FOLDER/"
        echo "📁 $file dipindahkan ke $SECURE_FOLDER/"
    fi
done

# Pindahkan folder
for folder in "static" "uploads" "faces" "logs"; do
    if [ -d "$folder" ]; then
        cp -r "$folder" "$SECURE_FOLDER/"
        echo "📁 $folder dipindahkan ke $SECURE_FOLDER/"
    fi
done

# Set permissions untuk keamanan
echo "🔐 Mengatur permissions untuk keamanan..."
chmod 700 "$SECURE_FOLDER"  # Hanya owner yang bisa akses

# Set permissions untuk file dan folder di dalamnya
find "$SECURE_FOLDER" -type d -exec chmod 700 {} \;  # Folder: 700
find "$SECURE_FOLDER" -type f -exec chmod 600 {} \;  # File: 600

echo "🔐 Permissions berhasil diatur (700/600)"

# Buat script launcher
echo "📝 Membuat script launcher..."

cat > launcher.sh << 'EOF'
#!/bin/bash
# 🚀 Clearance Face Search Launcher

echo "🚀 Menjalankan Clearance Face Search..."
echo "📁 Working directory: $(pwd)"

# Path ke folder aplikasi
APP_FOLDER=".clearance_app"

# Pastikan folder ada
if [ ! -d "$APP_FOLDER" ]; then
    echo "❌ Folder aplikasi tidak ditemukan: $APP_FOLDER"
    echo "Jalankan secure_folder_setup.sh terlebih dahulu"
    exit 1
fi

# Ubah ke folder aplikasi
cd "$APP_FOLDER"

# Jalankan aplikasi
python3 app.py
EOF

chmod +x launcher.sh
echo "✅ Script launcher.sh berhasil dibuat"

# Buat file konfigurasi
cat > .app_config << EOF
# Konfigurasi Path Aplikasi
APP_FOLDER=$SECURE_FOLDER
APP_NAME=Clearance Face Search
APP_VERSION=1.0.0

# Path ke folder aplikasi (untuk referensi)
# Aplikasi akan berjalan dari folder ini
EOF

echo "✅ File konfigurasi .app_config berhasil dibuat"

echo ""
echo "🎉 Setup selesai!"
echo "📁 Aplikasi sekarang ada di folder: $SECURE_FOLDER"
echo "🚀 Jalankan dengan: ./launcher.sh"
echo ""
echo "🔒 Folder tersembunyi dan aman dari akses sembarangan"
echo "💡 Untuk mengembalikan struktur semula, jalankan: ./restore.sh"
echo ""


