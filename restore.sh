#!/bin/bash

# 🔄 Restore Original Folder Structure (Linux/Mac)

echo "🔄 Mengembalikan struktur folder ke semula..."
echo "================================================"

SECURE_FOLDER=".clearance_app"

if [ ! -d "$SECURE_FOLDER" ]; then
    echo "❌ Folder $SECURE_FOLDER tidak ditemukan"
    echo "Jalankan secure_folder_setup.sh terlebih dahulu"
    exit 1
fi

echo "📁 Mengembalikan file dari $SECURE_FOLDER..."

# Daftar file yang perlu dikembalikan
FILES_TO_RESTORE=(
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

# Pindahkan file kembali ke root
for file in "${FILES_TO_RESTORE[@]}"; do
    if [ -f "$SECURE_FOLDER/$file" ]; then
        cp "$SECURE_FOLDER/$file" "$file"
        echo "📁 $file dikembalikan ke root"
    fi
done

# Pindahkan folder kembali
for folder in "static" "uploads" "faces" "logs"; do
    if [ -d "$SECURE_FOLDER/$folder" ]; then
        cp -r "$SECURE_FOLDER/$folder" "$folder"
        echo "📁 $folder dikembalikan ke root"
    fi
done

# Hapus folder aman
rm -rf "$SECURE_FOLDER"
echo "🗑️ Folder $SECURE_FOLDER dihapus"

# Hapus file launcher dan config
if [ -f "launcher.sh" ]; then
    rm "launcher.sh"
    echo "🗑️ launcher.sh dihapus"
fi

if [ -f ".app_config" ]; then
    rm ".app_config"
    echo "🗑️ .app_config dihapus"
fi

echo ""
echo "✅ Struktur folder berhasil dikembalikan ke semula"
echo "🚀 Sekarang bisa menjalankan: python3 app.py"
echo ""


