#!/usr/bin/env python3
"""
Test script untuk server alternatif (154.26.138.135)
Menguji login dan pencarian data
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clearance_face_search import _login_server_alt, _search_server_alt

def test_server_alt():
    print("=" * 60)
    print("TEST SERVER ALTERNATIF (154.26.138.135)")
    print("=" * 60)
    
    # Test 1: Direct access to search endpoint (without login)
    print("\n[TEST 1] Testing direct access to search endpoint (no login)...")
    import requests
    test_session = requests.Session()
    
    # Test search by name
    test_url = "http://154.26.138.135/000byte/cari_nama.php"
    test_params = {'nama_lengkap': 'ERVAN RUSNANDAR'}
    response = test_session.get(test_url, params=test_params, timeout=10)
    print(f"Response status: {response.status_code}")
    print(f"Response URL: {response.url}")
    print(f"Response content type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Response preview (first 500 chars):\n{response.text[:500]}")
    
    # Test 1: Login
    print("\n[TEST 2] Testing login...")
    session = _login_server_alt()
    if session:
        print("[OK] Login berhasil!")
    else:
        print("[FAIL] Login gagal! (akan tetap coba search)")
    
    # Test 2: Search by NIK
    print("\n[TEST 2] Testing search by NIK...")
    print("Mencari NIK: 1505041107830002")
    result_nik = _search_server_alt({'nik': '1505041107830002'})
    if result_nik:
        person_list = result_nik.get('person', [])
        print(f"[OK] Search by NIK berhasil! Ditemukan {len(person_list)} hasil")
        if person_list:
            first = person_list[0]
            print(f"   - NIK: {first.get('ktp_number', 'N/A')}")
            print(f"   - Nama: {first.get('full_name', 'N/A')}")
    else:
        print("[FAIL] Search by NIK gagal atau tidak mengembalikan hasil")
    
    # Test 3: Search by Name
    print("\n[TEST 3] Testing search by Name...")
    print("Mencari Nama: ERVAN RUSNANDAR")
    result_name = _search_server_alt({'name': 'ERVAN RUSNANDAR'})
    if result_name:
        person_list = result_name.get('person', [])
        print(f"[OK] Search by Name berhasil! Ditemukan {len(person_list)} hasil")
        if person_list:
            for i, person in enumerate(person_list[:3], 1):
                print(f"   {i}. NIK: {person.get('ktp_number', 'N/A')}, Nama: {person.get('full_name', 'N/A')}")
    else:
        print("[FAIL] Search by Name gagal atau tidak mengembalikan hasil")
    
    # Test 4: Search by Name (KRISTIN ELISA NATALIA TAMBUNAN)
    print("\n[TEST 4] Testing search by Name (KRISTIN ELISA NATALIA TAMBUNAN)...")
    print("Mencari Nama: KRISTIN ELISA NATALIA TAMBUNAN")
    result_name2 = _search_server_alt({'name': 'KRISTIN ELISA NATALIA TAMBUNAN'})
    if result_name2:
        person_list = result_name2.get('person', [])
        print(f"[OK] Search by Name berhasil! Ditemukan {len(person_list)} hasil")
        if person_list:
            for i, person in enumerate(person_list[:5], 1):
                print(f"   {i}. NIK: {person.get('ktp_number', 'N/A')}, Nama: {person.get('full_name', 'N/A')}")
        else:
            print("   [WARN] Tidak ada hasil ditemukan untuk nama ini")
    else:
        print("[FAIL] Search by Name gagal atau tidak mengembalikan hasil")
    
    print("\n" + "=" * 60)
    print("TEST SELESAI")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        test_server_alt()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

