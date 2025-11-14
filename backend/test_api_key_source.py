#!/usr/bin/env python3
"""
Script untuk test apakah sistem menggunakan API key dari database atau environment variable
"""

import sys
import os
from database import db

# Import helper function dari app.py
# Karena app.py mungkin belum di-import, kita test langsung
def test_api_key_source():
    """Test dari mana API key diambil"""
    print("=" * 60)
    print("TESTING API KEY SOURCE")
    print("=" * 60)
    
    # Test 1: Cek dari database
    print("\n1. Checking database...")
    db_api_key = db.get_setting('GOOGLE_CSE_API_KEY')
    if db_api_key:
        masked_db = f"{db_api_key[:10]}...{db_api_key[-4:]}" if len(db_api_key) > 14 else "***"
        print(f"   ✅ Found in database: {masked_db} ({len(db_api_key)} chars)")
    else:
        print("   ❌ NOT found in database")
    
    # Test 2: Cek dari environment variable
    print("\n2. Checking environment variable...")
    env_api_key = os.getenv('GOOGLE_CSE_API_KEY', '')
    if env_api_key:
        masked_env = f"{env_api_key[:10]}...{env_api_key[-4:]}" if len(env_api_key) > 14 else "***"
        print(f"   ✅ Found in environment: {masked_env} ({len(env_api_key)} chars)")
    else:
        print("   ❌ NOT found in environment")
    
    # Test 3: Simulasi get_google_cse_api_key() logic
    print("\n3. Testing get_google_cse_api_key() logic...")
    if db_api_key:
        final_key = db_api_key
        source = "DATABASE"
    elif env_api_key:
        final_key = env_api_key
        source = "ENVIRONMENT VARIABLE"
    else:
        final_key = ""
        source = "NONE"
    
    if final_key:
        masked_final = f"{final_key[:10]}...{final_key[-4:]}" if len(final_key) > 14 else "***"
        print(f"   ✅ Final API key source: {source}")
        print(f"   ✅ Final API key: {masked_final} ({len(final_key)} chars)")
        
        if source == "DATABASE":
            print("\n" + "=" * 60)
            print("✅ SUCCESS - Sistem menggunakan API key dari DATABASE!")
            print("=" * 60)
            print("\n💡 API key yang Anda input di Settings page akan digunakan")
            return True
        else:
            print("\n" + "=" * 60)
            print("⚠️  WARNING - Sistem menggunakan API key dari ENVIRONMENT VARIABLE")
            print("=" * 60)
            print("\n💡 Untuk menggunakan API key dari database:")
            print("   1. Pastikan API key sudah diinput di Settings page")
            print("   2. Restart server Flask")
            print("   3. Sistem akan otomatis menggunakan API key dari database")
            return False
    else:
        print("\n" + "=" * 60)
        print("❌ ERROR - API key tidak ditemukan!")
        print("=" * 60)
        print("\n💡 Solusi:")
        print("   1. Input API key di Settings page (http://127.0.0.1:5000/settings)")
        print("   2. Atau set di file .env: GOOGLE_CSE_API_KEY=your_key_here")
        return False

if __name__ == "__main__":
    success = test_api_key_source()
    sys.exit(0 if success else 1)

