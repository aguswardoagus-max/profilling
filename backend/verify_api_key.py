#!/usr/bin/env python3
"""
Verifikasi API key Google CSE yang digunakan di app.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Read app.py and extract API key
app_py_path = os.path.join(os.path.dirname(__file__), 'app.py')

with open(app_py_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
    # Find API key
    if 'AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc' in content:
        print("=" * 60)
        print("[OK] API Key Baru Ditemukan di app.py")
        print("=" * 60)
        print("API Key: AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc")
        print("\nStatus: API Key sudah diupdate!")
        print("\nPENTING: Restart server Flask agar perubahan berlaku!")
        print("  1. Stop server (Ctrl+C)")
        print("  2. Start server lagi: python app.py")
        print("=" * 60)
        sys.exit(0)
    elif 'AIzaSyB4qRiqQ0cpK9_PkV7R0I5NzB1BxEEljIs' in content:
        print("=" * 60)
        print("[ERROR] API Key Lama Masih Digunakan!")
        print("=" * 60)
        print("API Key Lama: AIzaSyB4qRiqQ0cpK9_PkV7R0I5NzB1BxEEljIs")
        print("\nStatus: API Key BELUM diupdate!")
        print("=" * 60)
        sys.exit(1)
    else:
        print("=" * 60)
        print("[INFO] API Key menggunakan environment variable")
        print("=" * 60)
        print("Cek .env file untuk GOOGLE_CSE_API_KEY")
        sys.exit(0)

