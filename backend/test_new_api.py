#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test NEW Google CSE API Key"""

import requests
import sys

# NEW API KEY
API_KEY = 'AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc'
CSE_ID = '7693f5093e95e4c28'

print("="*60)
print("TESTING NEW GOOGLE CSE API KEY")
print("="*60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
print(f"CSE ID:  {CSE_ID}")
print("-"*60)

query = "MARGUTIN"
search_url = 'https://www.googleapis.com/customsearch/v1'

params = {
    'key': API_KEY,
    'cx': CSE_ID,
    'q': query,
    'num': 10,
    'safe': 'active'
}

print(f"Testing query: '{query}'")
print("-"*60)

try:
    print("\n[1/3] Sending request...")
    response = requests.get(search_url, params=params, timeout=15)
    
    print(f"[2/3] Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        search_info = data.get('searchInformation', {})
        
        print(f"[3/3] SUCCESS!")
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(f"Total Results: {search_info.get('totalResults', 'N/A')}")
        print(f"Search Time:   {search_info.get('searchTime', 'N/A')}s")
        print(f"Items Found:   {len(items)}")
        print("-"*60)
        
        if items:
            print("\nFirst 3 Results:")
            for i, item in enumerate(items[:3], 1):
                print(f"\n{i}. {item.get('title', 'No Title')}")
                print(f"   URL: {item.get('link', 'No URL')}")
                print(f"   Snippet: {item.get('snippet', 'No snippet')[:80]}...")
        
        print("\n" + "="*60)
        print("[OK] API KEY IS VALID AND WORKING!")
        print("="*60)
        sys.exit(0)
        
    else:
        error_data = response.json()
        error = error_data.get('error', {})
        print(f"[ERROR] Status {response.status_code}")
        print(f"Message: {error.get('message', 'Unknown error')}")
        
        if response.status_code == 400:
            print("\n[FIX] API Key is invalid or expired")
        elif response.status_code == 403:
            print("\n[FIX] Custom Search API not enabled or restricted")
        elif response.status_code == 429:
            print("\n[FIX] Quota exceeded (100 requests/day)")
        
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    sys.exit(1)


