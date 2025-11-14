#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Social Searcher Style Endpoint
"""

import requests
import json
import sys

print("=" * 60)
print("TESTING SOCIAL SEARCHER STYLE ENDPOINT")
print("=" * 60)

# Test data
test_name = "MARGUTIN"
api_url = "http://127.0.0.1:5000/api/social-searcher-style"

print(f"Test Name: {test_name}")
print(f"API URL: {api_url}")
print("-" * 60)

try:
    print("\n[1/3] Sending POST request...")
    response = requests.post(
        api_url,
        json={"name": test_name},
        headers={"Content-Type": "application/json"},
        timeout=90  # 90 seconds timeout karena ada delays (6 platforms × ~10s each)
    )
    
    print(f"[2/3] Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"[3/3] SUCCESS!")
        print("\n" + "=" * 60)
        print("RESPONSE DATA:")
        print("=" * 60)
        print(f"Success: {data.get('success', False)}")
        print(f"Source: {data.get('source', 'N/A')}")
        print(f"Message: {data.get('message', 'N/A')}")
        
        if data.get('data'):
            web_results = data['data'].get('web', [])
            by_platform = data['data'].get('by_platform', {})
            
            print(f"\nTotal Results: {len(web_results)}")
            print(f"Platforms: {len(by_platform)}")
            
            print("\n" + "-" * 60)
            print("RESULTS BY PLATFORM:")
            print("-" * 60)
            for platform, results in by_platform.items():
                count = len(results) if results else 0
                status = "[OK]" if count > 0 else "[NO]"
                print(f"{status} {platform}: {count} results")
                if count > 0:
                    for i, r in enumerate(results[:3], 1):
                        print(f"   {i}. {r.get('title', 'No Title')[:60]}...")
                        print(f"      URL: {r.get('link', 'No URL')[:80]}...")
                        print(f"      Platform: {r.get('platform', 'N/A')}")
                        print(f"      Source: {r.get('source', 'N/A')}")
            
            print("\n" + "-" * 60)
            print("SAMPLE WEB RESULTS:")
            print("-" * 60)
            for i, result in enumerate(web_results[:5], 1):
                print(f"\n{i}. {result.get('title', 'No Title')}")
                print(f"   URL: {result.get('link', 'No URL')}")
                print(f"   Platform: {result.get('platform', 'N/A')}")
                print(f"   Source: {result.get('source', 'N/A')}")
                print(f"   Snippet: {result.get('snippet', 'No snippet')[:80]}...")
        
        if data.get('error'):
            print(f"\n⚠️ ERROR: {data.get('error')}")
        
        print("\n" + "=" * 60)
        if len(web_results) > 0:
            print("[OK] Social Searcher Style endpoint is working!")
            print(f"[OK] Found {len(web_results)} results from {len([r for r in by_platform.values() if r])} platforms")
        else:
            print("[WARNING] Endpoint working but no results found")
            print("Possible reasons:")
            print("  1. Rate limiting from Google")
            print("  2. Widget HTML parsing failed")
            print("  3. No results for this query")
        print("=" * 60)
        sys.exit(0 if len(web_results) > 0 else 1)
        
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data.get('error', 'Unknown error')}")
        except:
            print(f"Response: {response.text[:500]}")
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("[ERROR] Request timeout (30s)")
    print("Endpoint mungkin masih processing (normal untuk 6 platforms)")
    sys.exit(1)
    
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server")
    print("Make sure backend server is running on http://127.0.0.1:5000")
    sys.exit(1)
    
except Exception as e:
    print(f"[ERROR] Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

