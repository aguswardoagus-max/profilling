#!/usr/bin/env python3
"""
Script untuk menghapus cache foto bersih agar bisa test dengan algoritma baru
"""

import os
from pathlib import Path

def clear_photo_cache():
    """Hapus semua file cache foto bersih"""
    clean_photos_folder = Path("static/clean_photos")
    
    if not clean_photos_folder.exists():
        print("Folder static/clean_photos tidak ditemukan")
        return
    
    # Get all files in the folder
    files = list(clean_photos_folder.glob("*.jpg"))
    
    if not files:
        print("Tidak ada file cache foto yang ditemukan")
        return
    
    print(f"Menemukan {len(files)} file cache foto:")
    for file in files:
        print(f"  - {file.name}")
    
    # Ask for confirmation
    response = input("\nApakah Anda yakin ingin menghapus semua file cache? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        deleted_count = 0
        for file in files:
            try:
                file.unlink()
                print(f"[OK] Deleted: {file.name}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to delete {file.name}: {e}")
        
        print(f"\n[OK] Berhasil menghapus {deleted_count} file cache")
        print("Sekarang foto akan diproses ulang dengan algoritma terbaru")
    else:
        print("Operasi dibatalkan")

def clear_specific_photo(nik):
    """Hapus cache foto untuk NIK tertentu"""
    clean_photos_folder = Path("static/clean_photos")
    photo_path = clean_photos_folder / f"{nik}.jpg"
    
    if photo_path.exists():
        try:
            photo_path.unlink()
            print(f"[OK] Cache foto untuk NIK {nik} berhasil dihapus")
            return True
        except Exception as e:
            print(f"[ERROR] Gagal menghapus cache foto untuk NIK {nik}: {e}")
            return False
    else:
        print(f"[INFO] Cache foto untuk NIK {nik} tidak ditemukan")
        return False

def main():
    """Main function"""
    print("Clear Photo Cache Tool")
    print("=" * 30)
    print()
    
    print("Pilihan:")
    print("1. Hapus semua cache foto")
    print("2. Hapus cache foto untuk NIK tertentu")
    print("3. Keluar")
    
    choice = input("\nPilih opsi (1-3): ")
    
    if choice == "1":
        clear_photo_cache()
    elif choice == "2":
        nik = input("Masukkan NIK: ").strip()
        if nik:
            clear_specific_photo(nik)
        else:
            print("NIK tidak boleh kosong")
    elif choice == "3":
        print("Keluar...")
    else:
        print("Pilihan tidak valid")

if __name__ == "__main__":
    main()

