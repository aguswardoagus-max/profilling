#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script untuk menguji koneksi dan pencarian ke server 116
"""
import sys
import os
import requests
import json
from urllib.parse import urlencode

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Server 116 configuration
SERVER_116_BASE = "http://10.1.54.116"
SERVER_116_LOGIN_URL = f"{SERVER_116_BASE}/auth/login"
SERVER_116_IDENTITY_SEARCH_URL = f"{SERVER_116_BASE}/toolkit/api/identity/search"
SERVER_116_USERNAME = "jambi"
SERVER_116_PASSWORD = "@ab526d"

def test_login():
    """Test login ke server 116"""
    print("=" * 60)
    print("TEST 1: Login ke Server 116")
    print("=" * 60)
    
    session = requests.Session()
    
    try:
        # Get login page
        print(f"\n1. Mengakses halaman login: {SERVER_116_LOGIN_URL}")
        login_page_response = session.get(SERVER_116_LOGIN_URL, timeout=5)
        print(f"   Status Code: {login_page_response.status_code}")
        
        if login_page_response.status_code != 200:
            print(f"   [ERROR] GAGAL: Status code bukan 200")
            return None
        
        # Extract CSRF token
        import re
        csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', login_page_response.text)
        csrf_token = csrf_match.group(1) if csrf_match else 'jbHXcAQGRIgskYpnCBIVo43cTQg='
        print(f"   [OK] CSRF Token ditemukan: {csrf_token[:20]}...")
        
        # Login
        print(f"\n2. Melakukan login dengan username: {SERVER_116_USERNAME}")
        login_data = {
            'username': SERVER_116_USERNAME,
            'password': SERVER_116_PASSWORD,
            '_csrf': csrf_token
        }
        
        login_response = session.post(SERVER_116_LOGIN_URL,
                                     data=login_data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     timeout=10)
        print(f"   Status Code: {login_response.status_code}")
        print(f"   Response URL: {login_response.url}")
        
        if login_response.status_code != 200:
            print(f"   [ERROR] GAGAL: Login gagal dengan status code {login_response.status_code}")
            print(f"   Response text (first 500 chars): {login_response.text[:500]}")
            return None
        
        print(f"   [OK] Login berhasil!")
        return session
        
    except Exception as e:
        print(f"   [ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_search_by_nik(session, nik):
    """Test pencarian dengan NIK"""
    print("\n" + "=" * 60)
    print(f"TEST 2: Pencarian dengan NIK: {nik}")
    print("=" * 60)
    
    if not session:
        print("[ERROR] Session tidak tersedia, tidak dapat melakukan pencarian")
        return None
    
    try:
        # Build search parameters
        search_params = {'ktp_number': nik}
        full_url = f"{SERVER_116_IDENTITY_SEARCH_URL}?{urlencode(search_params)}"
        
        print(f"\n1. Parameter pencarian:")
        print(f"   ktp_number: {nik}")
        print(f"\n2. URL lengkap:")
        print(f"   {full_url}")
        
        # Perform search
        print(f"\n3. Melakukan request GET...")
        search_response = session.get(SERVER_116_IDENTITY_SEARCH_URL, params=search_params, timeout=15)
        
        print(f"   Status Code: {search_response.status_code}")
        print(f"   Response Headers: {dict(search_response.headers)}")
        
        if search_response.status_code != 200:
            print(f"   [ERROR] GAGAL: Status code bukan 200")
            print(f"   Response text (first 1000 chars):")
            print(f"   {search_response.text[:1000]}")
            return None
        
        # Parse response
        print(f"\n4. Parsing response JSON...")
        try:
            data = search_response.json()
            print(f"   [OK] JSON berhasil di-parse")
            print(f"   Response keys: {list(data.keys())}")
        except Exception as json_error:
            print(f"   [ERROR] GAGAL parse JSON: {json_error}")
            print(f"   Response text (first 1000 chars):")
            print(f"   {search_response.text[:1000]}")
            return None
        
        # Check response structure
        print(f"\n5. Analisis response:")
        print(f"   Type: {type(data)}")
        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        if 'error' in data:
            print(f"   Error field: '{data['error']}'")
        
        if 'success' in data:
            print(f"   Success field: {data['success']}")
        
        if 'person' in data:
            person_list = data['person']
            print(f"   Person field type: {type(person_list)}")
            print(f"   Person field length: {len(person_list) if isinstance(person_list, list) else 'N/A'}")
            
            if isinstance(person_list, list) and len(person_list) > 0:
                print(f"\n   [OK] DITEMUKAN {len(person_list)} HASIL!")
                print(f"\n   Contoh hasil pertama:")
                first_person = person_list[0]
                print(f"   - NIK: {first_person.get('ktp_number', 'N/A')}")
                print(f"   - Nama: {first_person.get('full_name', 'N/A')}")
                print(f"   - TTL: {first_person.get('birth_place', 'N/A')}, {first_person.get('date_of_birth', 'N/A')}")
                print(f"   - Alamat: {first_person.get('address', 'N/A')}")
                print(f"\n   Keys dalam person object: {list(first_person.keys())[:10]}...")
                return data
            else:
                print(f"   [WARNING] Person array kosong atau bukan list")
                print(f"   Full response:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
                return data
        else:
            print(f"   [WARNING] Field 'person' tidak ditemukan dalam response")
            print(f"   Full response:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            return data
        
    except Exception as e:
        print(f"   [ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_search_by_name(session, name):
    """Test pencarian dengan nama"""
    print("\n" + "=" * 60)
    print(f"TEST 3: Pencarian dengan Nama: {name}")
    print("=" * 60)
    
    if not session:
        print("[ERROR] Session tidak tersedia, tidak dapat melakukan pencarian")
        return None
    
    try:
        search_params = {'full_name': name, 'limit': '25'}
        full_url = f"{SERVER_116_IDENTITY_SEARCH_URL}?{urlencode(search_params)}"
        
        print(f"\n1. Parameter pencarian:")
        print(f"   full_name: {name}")
        print(f"   limit: 25")
        print(f"\n2. URL lengkap:")
        print(f"   {full_url}")
        
        search_response = session.get(SERVER_116_IDENTITY_SEARCH_URL, params=search_params, timeout=15)
        print(f"\n3. Status Code: {search_response.status_code}")
        
        if search_response.status_code == 200:
            data = search_response.json()
            if 'person' in data and isinstance(data['person'], list):
                print(f"   [OK] DITEMUKAN {len(data['person'])} HASIL!")
                if len(data['person']) > 0:
                    print(f"\n   Contoh hasil pertama:")
                    first = data['person'][0]
                    print(f"   - NIK: {first.get('ktp_number', 'N/A')}")
                    print(f"   - Nama: {first.get('full_name', 'N/A')}")
                return data
            else:
                print(f"   [WARNING] Tidak ada hasil")
                return data
        else:
            print(f"   [ERROR] GAGAL: Status code {search_response.status_code}")
            return None
        
    except Exception as e:
        print(f"   [ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("TESTING SERVER 116 CONNECTION & SEARCH")
    print("=" * 60)
    
    # Test login
    session = test_login()
    
    if not session:
        print("\n" + "=" * 60)
        print("[ERROR] TEST GAGAL: Tidak dapat login ke server 116")
        print("=" * 60)
        return
    
    # Test search by NIK
    test_nik = "1505041107830002"  # NIK dari user
    result_nik = test_search_by_nik(session, test_nik)
    
    # Test search by name (for comparison)
    test_name = "Jefri Ginanjar"
    result_name = test_search_by_name(session, test_name)
    
    # Summary
    print("\n" + "=" * 60)
    print("RINGKASAN TEST")
    print("=" * 60)
    print(f"Login: {'[OK] BERHASIL' if session else '[ERROR] GAGAL'}")
    
    if result_nik:
        if 'person' in result_nik and isinstance(result_nik['person'], list):
            print(f"Pencarian NIK ({test_nik}): [OK] BERHASIL - {len(result_nik['person'])} hasil")
        else:
            print(f"Pencarian NIK ({test_nik}): [WARNING] Response OK tapi tidak ada hasil")
    else:
        print(f"Pencarian NIK ({test_nik}): [ERROR] GAGAL")
    
    if result_name:
        if 'person' in result_name and isinstance(result_name['person'], list):
            print(f"Pencarian Nama ({test_name}): [OK] BERHASIL - {len(result_name['person'])} hasil")
        else:
            print(f"Pencarian Nama ({test_name}): [WARNING] Response OK tapi tidak ada hasil")
    else:
        print(f"Pencarian Nama ({test_name}): [ERROR] GAGAL")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

