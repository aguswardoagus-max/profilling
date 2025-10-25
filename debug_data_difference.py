#!/usr/bin/env python3
"""
Script untuk debug perbedaan data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
import json

def debug_data_difference():
    """Debug perbedaan data"""
    
    print("=== DEBUG PERBEDAAN DATA ===\n")
    
    # Get data from database
    profiling_data = db.get_profiling_data(limit=1)
    if not profiling_data:
        print("[FAIL] No data found")
        return
    
    item = profiling_data[0]
    person_data = item.get('person_data', {})
    
    print("1. Data dari database:")
    print(f"   ID: {item['id']}")
    print(f"   Search Type: {item['search_type']}")
    print(f"   Search Timestamp: {item['search_timestamp']}")
    print(f"   Person Data Keys: {list(person_data.keys())}")
    print(f"   Family Data: {item.get('family_data')}")
    print(f"   Phone Data: {item.get('phone_data')}")
    print(f"   Face Data: {item.get('face_data')}")
    
    # Check specific fields
    print(f"\n2. Specific fields:")
    print(f"   full_name: {person_data.get('full_name')} (type: {type(person_data.get('full_name'))})")
    print(f"   ktp_number: {person_data.get('ktp_number')} (type: {type(person_data.get('ktp_number'))})")
    print(f"   tempat_lahir: {person_data.get('tempat_lahir')} (type: {type(person_data.get('tempat_lahir'))})")
    print(f"   tanggal_lahir: {person_data.get('tanggal_lahir')} (type: {type(person_data.get('tanggal_lahir'))})")
    print(f"   alamat: {person_data.get('alamat')} (type: {type(person_data.get('alamat'))})")
    print(f"   foto_bersih_url: {person_data.get('foto_bersih_url')} (type: {type(person_data.get('foto_bersih_url'))})")
    
    # Check for None values
    print(f"\n3. None values check:")
    none_fields = []
    for key, value in person_data.items():
        if value is None:
            none_fields.append(key)
    
    if none_fields:
        print(f"   Fields with None values: {none_fields}")
    else:
        print(f"   No None values found")
    
    # Check for empty strings
    print(f"\n4. Empty strings check:")
    empty_fields = []
    for key, value in person_data.items():
        if isinstance(value, str) and value.strip() == '':
            empty_fields.append(key)
    
    if empty_fields:
        print(f"   Fields with empty strings: {empty_fields}")
    else:
        print(f"   No empty strings found")
    
    # Check data types
    print(f"\n5. Data types check:")
    for key, value in person_data.items():
        if not isinstance(value, (str, int, float, bool)) and value is not None:
            print(f"   {key}: {type(value)} - {value}")
    
    # Create transformed data
    print(f"\n6. Transformed data:")
    report = {
        'id': item['id'],
        'nama': person_data.get('full_name', 'N/A'),
        'nik': person_data.get('ktp_number', 'N/A'),
        'ttl': f"{person_data.get('tempat_lahir', 'N/A')}, {person_data.get('tanggal_lahir', 'N/A')}",
        'alamat': person_data.get('alamat', 'N/A'),
        'kab_kota': 'Jambi',
        'prov': 'Jambi',
        'kategori': 'Identity Search',
        'subkategori': 'KTP Search',
        'status_verifikasi': 'verified',
        'foto_url': person_data.get('foto_bersih_url', ''),
        'tanggal_input': item['search_timestamp'],
        'search_type': item['search_type'],
        'person_data': person_data,
        'family_data': item.get('family_data', {}),
        'phone_data': item.get('phone_data', []),
        'face_data': item.get('face_data', {})
    }
    
    print(f"   Transformed report keys: {list(report.keys())}")
    print(f"   Nama: {report['nama']} (type: {type(report['nama'])})")
    print(f"   NIK: {report['nik']} (type: {type(report['nik'])})")
    print(f"   TTL: {report['ttl']} (type: {type(report['ttl'])})")
    print(f"   Alamat: {report['alamat']} (type: {type(report['alamat'])})")
    print(f"   Foto URL: {report['foto_url']} (type: {type(report['foto_url'])})")
    print(f"   Tanggal Input: {report['tanggal_input']} (type: {type(report['tanggal_input'])})")
    
    # Check if any values are None
    print(f"\n7. None values in transformed data:")
    none_values = []
    for key, value in report.items():
        if value is None:
            none_values.append(key)
    
    if none_values:
        print(f"   Fields with None values: {none_values}")
    else:
        print(f"   No None values in transformed data")

if __name__ == "__main__":
    debug_data_difference()
