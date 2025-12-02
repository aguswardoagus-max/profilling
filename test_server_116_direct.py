# -*- coding: utf-8 -*-
"""Test langsung menggunakan fungsi yang sama seperti di aplikasi"""
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Import fungsi yang sama seperti di aplikasi
from clearance_face_search import call_search, ensure_token

print("=" * 70)
print("TEST LANGSUNG DENGAN FUNGSI APLIKASI")
print("=" * 70)

# Simulasi seperti di aplikasi
username = "rezarios"
password = "12345678"
nik = "1505041107830002"

print(f"\n1. Menguji ensure_token dengan username: {username}")
print("-" * 70)
token = ensure_token(username, password, force_refresh=True)
print(f"Token yang didapat: {token[:50]}...")
print(f"Apakah fallback token? {token.startswith('fallback_token_')}")

print(f"\n2. Menguji call_search dengan NIK: {nik}")
print("-" * 70)
params = {
    "name": "",
    "nik": nik,
    "family_cert_number": "",
    "tempat_lahir": "",
    "tanggal_lahir": "",
    "no_prop": "",
    "no_kab": "",
    "no_kec": "",
    "no_desa": "",
    "page": "1",
    "limit": "100"
}

print(f"Parameter yang dikirim:")
for key, value in params.items():
    if value:  # Hanya tampilkan yang tidak kosong
        print(f"  {key}: {value}")

result = call_search(token, params)

print(f"\n3. Hasil dari call_search:")
print("-" * 70)
print(f"Type: {type(result)}")
if isinstance(result, dict):
    print(f"Keys: {list(result.keys())}")
    
    if 'person' in result:
        person_list = result['person']
        print(f"Person field type: {type(person_list)}")
        print(f"Person field length: {len(person_list) if isinstance(person_list, list) else 'N/A'}")
        
        if isinstance(person_list, list) and len(person_list) > 0:
            print(f"\n[SUCCESS] DITEMUKAN {len(person_list)} HASIL!")
            print(f"\nContoh hasil pertama:")
            first = person_list[0]
            print(f"  NIK: {first.get('ktp_number', first.get('nik', 'N/A'))}")
            print(f"  Nama: {first.get('full_name', 'N/A')}")
            print(f"  TTL: {first.get('birth_place', 'N/A')}, {first.get('date_of_birth', 'N/A')}")
            print(f"  Alamat: {first.get('address', 'N/A')}")
            print(f"\nSemua keys dalam person: {list(first.keys())[:15]}...")
        else:
            print(f"\n[WARNING] Person array kosong!")
            print(f"Full result:")
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    else:
        print(f"\n[ERROR] Field 'person' tidak ditemukan!")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
else:
    print(f"Result bukan dict: {result}")

print("\n" + "=" * 70)

