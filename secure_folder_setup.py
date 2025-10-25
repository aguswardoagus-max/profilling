#!/usr/bin/env python3
"""
Script untuk mengatur folder aplikasi dengan keamanan
Membuat folder tersembunyi dan mengatur permissions
"""

import os
import sys
import shutil
import stat
from pathlib import Path

def create_secure_folder():
    """Membuat folder aplikasi yang aman"""
    
    # Nama folder tersembunyi
    secure_folder = ".clearance_app"
    
    print("🔒 Mengatur folder aplikasi yang aman...")
    
    # Buat folder tersembunyi jika belum ada
    if not os.path.exists(secure_folder):
        os.makedirs(secure_folder)
        print(f"✅ Folder {secure_folder} berhasil dibuat")
    else:
        print(f"✅ Folder {secure_folder} sudah ada")
    
    # Daftar file yang perlu dipindahkan
    files_to_move = [
        'app.py',
        'database.py', 
        'cekplat.py',
        'clearance_face_search.py',
        'run_app.py',
        'requirements.txt',
        'config_example.env',
        'database_setup.sql',
        'setup_database.py',
        'static',
        'uploads',
        'faces',
        'logs'
    ]
    
    # Pindahkan file ke folder aman
    moved_files = []
    for file_name in files_to_move:
        if os.path.exists(file_name):
            source = file_name
            destination = os.path.join(secure_folder, file_name)
            
            if os.path.isdir(source):
                if os.path.exists(destination):
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            
            moved_files.append(file_name)
            print(f"📁 {file_name} dipindahkan ke {secure_folder}/")
    
    # Set permissions (Linux/Mac)
    if os.name != 'nt':  # Bukan Windows
        try:
            # Set folder permissions: hanya owner yang bisa akses
            os.chmod(secure_folder, stat.S_IRWXU)  # 700
            
            # Set file permissions
            for root, dirs, files in os.walk(secure_folder):
                for d in dirs:
                    os.chmod(os.path.join(root, d), stat.S_IRWXU)
                for f in files:
                    os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR)  # 600
            
            print("🔐 Permissions berhasil diatur (700/600)")
        except Exception as e:
            print(f"⚠️ Gagal mengatur permissions: {e}")
    
    # Buat script launcher di root
    create_launcher_script(secure_folder)
    
    # Buat .env file untuk path
    create_env_config(secure_folder)
    
    print(f"\n🎉 Setup selesai!")
    print(f"📁 Aplikasi sekarang ada di folder: {secure_folder}")
    print(f"🚀 Jalankan dengan: python launcher.py")
    
    return secure_folder

def create_launcher_script(secure_folder):
    """Membuat script launcher"""
    
    launcher_content = f'''#!/usr/bin/env python3
"""
Launcher script untuk aplikasi Clearance Face Search
Script ini akan menjalankan aplikasi dari folder yang aman
"""

import os
import sys
from pathlib import Path

def main():
    # Path ke folder aplikasi
    app_folder = "{secure_folder}"
    
    # Pastikan folder ada
    if not os.path.exists(app_folder):
        print(f"❌ Folder aplikasi tidak ditemukan: {{app_folder}}")
        print("Jalankan secure_folder_setup.py terlebih dahulu")
        sys.exit(1)
    
    # Ubah working directory ke folder aplikasi
    os.chdir(app_folder)
    
    # Tambahkan path ke sys.path
    sys.path.insert(0, app_folder)
    
    print("🚀 Menjalankan Clearance Face Search...")
    print(f"📁 Working directory: {{os.getcwd()}}")
    
    # Import dan jalankan aplikasi
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except ImportError as e:
        print(f"❌ Gagal mengimpor aplikasi: {{e}}")
        print("Pastikan semua file ada di folder aplikasi")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error menjalankan aplikasi: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('launcher.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    # Set executable permission (Linux/Mac)
    if os.name != 'nt':
        os.chmod('launcher.py', stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)  # 755
    
    print("📝 Script launcher.py berhasil dibuat")

def create_env_config(secure_folder):
    """Membuat konfigurasi environment"""
    
    env_content = f'''# Konfigurasi Path Aplikasi
APP_FOLDER={secure_folder}
APP_NAME=Clearance Face Search
APP_VERSION=1.0.0

# Path ke folder aplikasi (untuk referensi)
# Aplikasi akan berjalan dari folder ini
'''
    
    with open('.app_config', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("⚙️ File konfigurasi .app_config berhasil dibuat")

def restore_original_structure():
    """Mengembalikan struktur folder ke semula"""
    
    secure_folder = ".clearance_app"
    
    if not os.path.exists(secure_folder):
        print(f"❌ Folder {secure_folder} tidak ditemukan")
        return
    
    print("🔄 Mengembalikan struktur folder ke semula...")
    
    # Pindahkan file kembali ke root
    for item in os.listdir(secure_folder):
        source = os.path.join(secure_folder, item)
        destination = item
        
        if os.path.exists(destination):
            if os.path.isdir(destination):
                shutil.rmtree(destination)
            else:
                os.remove(destination)
        
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        
        print(f"📁 {item} dikembalikan ke root")
    
    # Hapus folder aman
    shutil.rmtree(secure_folder)
    
    # Hapus file launcher dan config
    for file in ['launcher.py', '.app_config']:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ {file} dihapus")
    
    print("✅ Struktur folder berhasil dikembalikan")

def show_status():
    """Menampilkan status keamanan folder"""
    
    secure_folder = ".clearance_app"
    
    print("📊 Status Keamanan Folder:")
    print("=" * 40)
    
    if os.path.exists(secure_folder):
        print(f"✅ Folder aman: {secure_folder}")
        
        # Cek permissions (Linux/Mac)
        if os.name != 'nt':
            stat_info = os.stat(secure_folder)
            permissions = oct(stat_info.st_mode)[-3:]
            print(f"🔐 Permissions: {permissions}")
        
        # List isi folder
        files = os.listdir(secure_folder)
        print(f"📁 Jumlah file/folder: {len(files)}")
        
        if 'launcher.py' in os.listdir('.'):
            print("✅ Script launcher tersedia")
        else:
            print("❌ Script launcher tidak ditemukan")
            
    else:
        print("❌ Folder aman belum dibuat")
        print("Jalankan: python secure_folder_setup.py")

def main():
    """Main function"""
    
    print("🔒 Clearance Face Search - Secure Folder Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'setup':
            create_secure_folder()
        elif command == 'restore':
            restore_original_structure()
        elif command == 'status':
            show_status()
        else:
            print("❌ Command tidak dikenal")
            print("Gunakan: setup, restore, atau status")
    else:
        print("Pilih opsi:")
        print("1. Setup folder aman")
        print("2. Kembalikan struktur semula")
        print("3. Lihat status")
        print("4. Keluar")
        
        choice = input("\nPilihan (1-4): ").strip()
        
        if choice == '1':
            create_secure_folder()
        elif choice == '2':
            restore_original_structure()
        elif choice == '3':
            show_status()
        elif choice == '4':
            print("👋 Sampai jumpa!")
        else:
            print("❌ Pilihan tidak valid")

if __name__ == "__main__":
    main()


