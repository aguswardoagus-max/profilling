#!/usr/bin/env python3
"""
Test Google CSE API Key
"""
import requests
import json

API_KEY = 'AIzaSyB4qRiqQ0cpK9_PkV7R0I5NzB1BxEEljIs'
CSE_ID = '7693f5093e95e4c28'
QUERY = '"MARGUTIN"'

print("="*60)
print("  TESTING GOOGLE CSE API KEY")
print("="*60)
print(f"\nAPI Key: {API_KEY[:20]}...")
print(f"CSE ID: {CSE_ID}")
print(f"Query: {QUERY}")
print("\nMaking request to Google CSE API...")

try:
    resp = requests.get(
        'https://www.googleapis.com/customsearch/v1',
        params={
            'key': API_KEY,
            'cx': CSE_ID,
            'q': QUERY,
            'num': 10
        },
        timeout=15
    )
    
    print(f"\n[OK] Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        total_results = data.get('searchInformation', {}).get('totalResults', 0)
        items = data.get('items', [])
        
        print(f"[OK] Total Results Available: {total_results}")
        print(f"[OK] Items Returned: {len(items)}")
        
        if items:
            print("\n" + "="*60)
            print("  HASIL PENCARIAN (Top 5)")
            print("="*60)
            for i, item in enumerate(items[:5], 1):
                title = item.get('title', 'No title')
                link = item.get('link', 'No link')
                snippet = item.get('snippet', 'No snippet')
                
                print(f"\n{i}. {title}")
                print(f"   URL: {link}")
                print(f"   Snippet: {snippet[:100]}...")
            
            print("\n" + "="*60)
            print("  [SUCCESS] API KEY VALID DAN BEKERJA!")
            print("="*60)
            print("\nLangkah selanjutnya:")
            print("1. RESTART SERVER dengan menjalankan: restart_server.bat")
            print("2. Atau manual: Stop server (Ctrl+C) dan start ulang")
            print("3. Refresh browser dengan Ctrl+F5")
            print("4. Test social media search di profiling")
        else:
            print("\n[WARNING] API berhasil tapi tidak ada hasil untuk query ini")
    else:
        error_data = resp.json()
        print(f"\n[ERROR] Error {resp.status_code}:")
        print(json.dumps(error_data, indent=2))
        
except requests.exceptions.RequestException as e:
    print(f"\n[ERROR] Connection Error: {e}")
except Exception as e:
    print(f"\n[ERROR] Unexpected Error: {e}")

print("\n" + "="*60)

