#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Google CSE API Key
"""

import requests
import sys

# API Configuration
API_KEY = 'AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc'
CSE_ID = '7693f5093e95e4c28'

print("=" * 60)
print("TESTING GOOGLE CSE API KEY")
print("=" * 60)
print(f"API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
print(f"CSE ID:  {CSE_ID}")
print("-" * 60)

# Test query
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
print(f"Request URL: {search_url}")
print("-" * 60)

try:
    print("\n[1/3] Sending request to Google CSE API...")
    response = requests.get(search_url, params=params, timeout=15)
    
    print(f"[2/3] Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        search_info = data.get('searchInformation', {})
        
        print(f"[3/3] SUCCESS! API Key is VALID!")
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(f"Total Results: {search_info.get('totalResults', 'N/A')}")
        print(f"Search Time:   {search_info.get('searchTime', 'N/A')}s")
        print(f"Items Found:   {len(items)}")
        print("-" * 60)
        
        if items:
            print("\nFirst 3 Results:")
            for i, item in enumerate(items[:3], 1):
                print(f"\n{i}. {item.get('title', 'No Title')}")
                print(f"   URL: {item.get('link', 'No URL')}")
                print(f"   Snippet: {item.get('snippet', 'No snippet')[:100]}...")
        
        print("\n" + "=" * 60)
        print("[OK] Google CSE API is working correctly!")
        print("=" * 60)
        sys.exit(0)
        
    elif response.status_code == 400:
        error_data = response.json()
        error = error_data.get('error', {})
        print(f"[ERROR] Bad Request (400)")
        print(f"Message: {error.get('message', 'Unknown error')}")
        print(f"Reason:  {error.get('errors', [{}])[0].get('reason', 'Unknown')}")
        print("\n[FIX] Possible issues:")
        print("  1. API Key is invalid")
        print("  2. CSE ID is incorrect")
        print("  3. API Key restrictions (IP/domain)")
        sys.exit(1)
        
    elif response.status_code == 403:
        error_data = response.json()
        error = error_data.get('error', {})
        print(f"[ERROR] Forbidden (403)")
        print(f"Message: {error.get('message', 'Unknown error')}")
        print("\n[FIX] Possible issues:")
        print("  1. Custom Search API not enabled in Google Cloud Console")
        print("  2. API Key has domain/IP restrictions")
        print("  3. API Key is invalid")
        print("\nSteps to fix:")
        print("  1. Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com")
        print("  2. Enable 'Custom Search API'")
        print("  3. Check API Key restrictions in Credentials page")
        sys.exit(1)
        
    elif response.status_code == 429:
        print(f"[ERROR] Quota Exceeded (429)")
        print("Daily quota limit reached (100 requests/day for free tier)")
        print("\n[FIX]:")
        print("  1. Wait until tomorrow (resets at midnight Pacific Time)")
        print("  2. Or upgrade to paid tier")
        sys.exit(1)
        
    else:
        print(f"[ERROR] Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("[ERROR] Request timeout (15s)")
    print("Check your internet connection")
    sys.exit(1)
    
except requests.exceptions.ConnectionError:
    print("[ERROR] Connection error")
    print("Cannot connect to Google API")
    print("Check your internet connection and firewall")
    sys.exit(1)
    
except Exception as e:
    print(f"[ERROR] Unexpected error: {str(e)}")
    sys.exit(1)

