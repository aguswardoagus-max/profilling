#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test Google Search Direct (Platform-specific)
"""

import requests
import urllib.parse
import re
import sys

print("=" * 60)
print("TESTING GOOGLE SEARCH DIRECT (Platform-specific)")
print("=" * 60)

test_name = "MARGUTIN"
platform = "facebook"
query = f'"{test_name}" site:facebook.com'
encoded_query = urllib.parse.quote(query)
search_url = f'https://www.google.com/search?q={encoded_query}&num=10'

print(f"Test Name: {test_name}")
print(f"Platform: {platform}")
print(f"Query: {query}")
print(f"Search URL: {search_url}")
print("-" * 60)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
}

try:
    print("\n[1/3] Fetching Google Search...")
    response = requests.get(search_url, headers=headers, timeout=15)
    
    print(f"[2/3] Response status: {response.status_code}")
    
    if response.status_code == 429:
        print("[ERROR] Rate limited (429)")
        print("Google is blocking requests")
        sys.exit(1)
    
    if response.status_code == 200:
        html_content = response.text
        print(f"HTML length: {len(html_content)} bytes")
        
        print(f"[3/3] Parsing HTML...")
        results = []
        
        patterns = [
            r'<div[^>]*class=["\'][^"\']*g[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>.*?<span[^>]*>(.*?)</span>',
            r'<div[^>]*class=["\'][^"\']*yuRUbf[^"\']*["\'][^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>.*?<h3[^>]*>(.*?)</h3>',
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            print(f"   Pattern {i+1}: Found {len(matches)} matches")
            
            for match in matches[:10]:
                url = match[0] if len(match) > 0 else ''
                title = re.sub(r'<[^>]+>', '', match[1] if len(match) > 1 else 'No Title').strip()
                snippet = re.sub(r'<[^>]+>', '', match[2] if len(match) > 2 else '').strip() if len(match) > 2 else ''
                
                # Clean URL
                if '/url?q=' in url:
                    url = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('q', [url])[0]
                
                # Filter untuk platform
                if url and url.startswith('http') and 'facebook.com' in url.lower():
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
            for i, r in enumerate(results[:5], 1):
                print(f"\n{i}. {r['title']}")
                print(f"   URL: {r['link']}")
                print(f"   Snippet: {r['snippet']}")
            
            print("\n" + "=" * 60)
            print("[OK] Google Search direct works!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("[WARNING] No results parsed")
            print("HTML snippet (first 1000 chars):")
            print(html_content[:1000])
            print("=" * 60)
            sys.exit(1)
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

