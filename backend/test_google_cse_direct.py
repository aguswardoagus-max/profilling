#!/usr/bin/env python3
"""
Test langsung Google CSE API tanpa perlu server running
Jalankan: python test_google_cse_direct.py
"""
import os
import sys
import requests
import json

def test_google_cse_direct():
    """Test Google CSE API secara langsung"""
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 60)
    print("[TEST] Testing Google CSE API (Direct Test)")
    print("=" * 60)
    
    # Konfigurasi
    CSE_ID = '7693f5093e95e4c28'
    API_KEY = os.getenv('GOOGLE_CSE_API_KEY') or 'AIzaSyAsTbHbPeyyiMvl7jTAGLlg6ooCESSTgMc'
    test_query = 'test'
    query = f'"{test_query}"'
    
    search_url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'key': API_KEY,
        'cx': CSE_ID,
        'q': query,
        'num': 1,  # Just 1 result for testing
        'safe': 'active',
    }
    
    print(f"CSE ID: {CSE_ID}")
    print(f"API Key: {API_KEY[:20]}... (truncated)")
    print(f"Query: {query}")
    print(f"URL: {search_url}")
    print("-" * 60)
    
    try:
        print("[1/3] Sending request to Google CSE API...")
        response = requests.get(search_url, params=params, timeout=10)
        
        print(f"[2/3] Response status: {response.status_code}")
        print(f"      Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            search_info = data.get('searchInformation', {})
            
            print(f"[3/3] [SUCCESS]")
            print("\n" + "=" * 60)
            print("RESULT:")
            print("=" * 60)
            print(f"Total Results: {search_info.get('totalResults', 'N/A')}")
            print(f"Search Time:   {search_info.get('searchTime', 'N/A')}s")
            print(f"Items Found:   {len(items)}")
            print("-" * 60)
            
            if items:
                print("\nSample Result:")
                item = items[0]
                print(f"  Title: {item.get('title', 'No Title')}")
                print(f"  URL: {item.get('link', 'No URL')}")
                print(f"  Snippet: {item.get('snippet', 'No snippet')[:100]}...")
            
            print("\n" + "=" * 60)
            print("[OK] Google CSE API is WORKING CORRECTLY!")
            print("=" * 60)
            return 0
            
        else:
            print(f"[3/3] [FAILED]")
            print("\n" + "=" * 60)
            print("ERROR DETAILS:")
            print("=" * 60)
            print(f"Status Code: {response.status_code}")
            
            # Try to parse error JSON
            try:
                error_json = response.json()
                error = error_json.get('error', {})
                error_message = error.get('message', 'Unknown error')
                error_code = error.get('code', response.status_code)
                errors = error.get('errors', [])
                
                print(f"Error Code: {error_code}")
                print(f"Error Message: {error_message}")
                
                if errors:
                    print("\nError Details:")
                    for err in errors:
                        print(f"  - Domain: {err.get('domain', 'N/A')}")
                        print(f"    Reason: {err.get('reason', 'N/A')}")
                        print(f"    Message: {err.get('message', 'N/A')}")
                
                print("\n" + "=" * 60)
                print("DIAGNOSIS:")
                print("=" * 60)
                
                if error_code == 400:
                    print("[ERROR] Bad Request (400)")
                    print("   Possible issues:")
                    print("   1. API Key is invalid")
                    print("   2. CSE ID is incorrect")
                    print("   3. API Key restrictions (IP/domain)")
                    print("\n   Fix:")
                    print("   - Check API Key in Google Cloud Console")
                    print("   - Verify CSE ID is correct")
                    print("   - Check API Key restrictions")
                    
                elif error_code == 403:
                    print("[ERROR] Forbidden (403)")
                    print("   Possible issues:")
                    print("   1. Custom Search API not enabled")
                    print("   2. API Key has domain/IP restrictions")
                    print("   3. API Key is invalid")
                    print("\n   Fix:")
                    print("   1. Go to: https://console.cloud.google.com/apis/library/customsearch.googleapis.com")
                    print("   2. Enable 'Custom Search API'")
                    print("   3. Check API Key restrictions in Credentials page")
                    
                elif error_code == 429:
                    print("[ERROR] Quota Exceeded (429)")
                    print("   Daily quota limit reached (100 requests/day for free tier)")
                    print("\n   Fix:")
                    print("   - Wait until tomorrow (resets at midnight Pacific Time)")
                    print("   - Or upgrade to paid tier")
                    
                else:
                    print(f"[ERROR] Unexpected Error Code: {error_code}")
                    print(f"   Message: {error_message}")
                
                print("\n" + "=" * 60)
                print("Full Error JSON:")
                print("=" * 60)
                print(json.dumps(error_json, indent=2))
                
            except json.JSONDecodeError:
                print(f"Response Text: {response.text[:500]}")
            
            return 1
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request Timeout!")
        print("   Google CSE API tidak merespons dalam 10 detik")
        print("   Check your internet connection")
        return 1
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Connection Error!")
        print("   Cannot connect to Google API")
        print("   Check your internet connection and firewall")
        return 1
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = test_google_cse_direct()
    sys.exit(exit_code)

