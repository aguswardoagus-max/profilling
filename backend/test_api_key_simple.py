#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Google CSE API Key - Simple
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_CSE_API_KEY') or 'AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc'
CSE_ID = '7693f5093e95e4c28'

print("=" * 60)
print("TESTING GOOGLE CSE API KEY")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...")
print(f"CSE ID: {CSE_ID}")
print("-" * 60)

api_url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'key': API_KEY,
    'cx': CSE_ID,
    'q': 'MARGUTIN site:facebook.com',
    'num': 3
}

try:
    print("\n[1/2] Sending API request...")
    response = requests.get(api_url, params=params, timeout=15)
    
    print(f"[2/2] Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f"\n[OK] API Key is VALID!")
        print(f"Found {len(items)} results")
        
        if items:
            print("\nSample Results:")
            for i, item in enumerate(items[:3], 1):
                print(f"\n{i}. {item.get('title', 'No Title')}")
                print(f"   URL: {item.get('link', 'No URL')}")
        else:
            print("\n[WARNING] No results found (but API key is valid)")
    elif response.status_code == 429:
        print("\n[ERROR] API quota exceeded (429)")
        error_data = response.json()
        print(f"Error: {error_data.get('error', {}).get('message', 'Unknown')}")
    else:
        print(f"\n[ERROR] HTTP {response.status_code}")
        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        error_msg = error_data.get('error', {}).get('message', 'Unknown error')
        print(f"Error: {error_msg}")
        
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


