#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Social Searcher Style Endpoint - FAST VERSION (1 platform only)
"""

import requests
import json
import sys
import urllib.parse
import re

print("=" * 60)
print("TESTING SOCIAL SEARCHER STYLE - FAST TEST (1 Platform)")
print("=" * 60)

# Test dengan 1 platform saja untuk speed
test_name = "MARGUTIN"
CSE_ID = '7693f5093e95e4c28'

# Test Facebook saja
platform = 'facebook'
query = f'"{test_name}" site:facebook.com'
encoded_query = urllib.parse.quote(query)
widget_url = f'https://cse.google.com/cse?cx={CSE_ID}&q={encoded_query}'

print(f"Test Name: {test_name}")
print(f"Platform: {platform}")
print(f"Query: {query}")
print(f"Widget URL: {widget_url}")
print("-" * 60)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://cse.google.com/',
}

try:
    print("\n[1/3] Fetching Google CSE Widget HTML...")
    response = requests.get(widget_url, headers=headers, timeout=15)
    
    print(f"[2/3] Response status: {response.status_code}")
    print(f"HTML length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        html_content = response.text
        
        # Check if HTML contains widget structure
        has_widget = 'gsc-webResult' in html_content.lower() or 'gsc-result' in html_content.lower()
        print(f"Contains widget structure: {has_widget}")
        
        # Try parsing
        results = []
        patterns = [
            r'<div[^>]*class=["\'][^"\']*gsc-webResult[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?<div[^>]*class=["\'][^"\']*gs-title[^"\']*["\'][^>]*>(.*?)</div>.*?<div[^>]*class=["\'][^"\']*gs-snippet[^"\']*["\'][^>]*>(.*?)</div>',
            r'<div[^>]*class=["\'][^"\']*g[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*>(.*?)</span>',
        ]
        
        print(f"[3/3] Parsing HTML...")
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            print(f"   Pattern {i+1}: Found {len(matches)} matches")
            
            for match in matches[:5]:
                url = match[0] if len(match) > 0 else ''
                title = re.sub(r'<[^>]+>', '', match[1] if len(match) > 1 else 'No Title').strip()
                snippet = re.sub(r'<[^>]+>', '', match[2] if len(match) > 2 else '').strip()
                
                if url and url.startswith('http'):
                    results.append({
                        'title': title[:60],
                        'link': url[:80],
                        'snippet': snippet[:60] if snippet else 'No snippet'
                    })
            
            if results:
                break
        
        print("\n" + "=" * 60)
        print("RESULTS:")
        print("=" * 60)
        print(f"Found: {len(results)} results")
        
        if results:
            print("\nSample Results:")
            for i, r in enumerate(results[:3], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['link']}")
                print(f"   Snippet: {r['snippet']}")
            
            print("\n" + "=" * 60)
            print("[OK] Widget HTML parsing works!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("[WARNING] No results parsed from HTML")
            print("Possible reasons:")
            print("  1. Widget HTML structure different")
            print("  2. Widget needs JavaScript to render")
            print("  3. No results for this query")
            print("\nHTML snippet (first 500 chars):")
            print(html_content[:500])
            print("=" * 60)
            sys.exit(1)
            
    elif response.status_code == 429:
        print("[ERROR] Rate limited (429)")
        print("Google is blocking requests")
        sys.exit(1)
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("[ERROR] Request timeout")
    sys.exit(1)
    
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



