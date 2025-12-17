#!/usr/bin/env python3
"""Test script untuk Phone API endpoint"""
import requests
import json
import sys

def test_phone_api():
    """Test phone search API"""
    phone_number = '085218341136'
    url = 'http://localhost:5000/api/phone/search'
    
    print(f"Testing Phone API endpoint...")
    print(f"URL: {url}")
    print(f"Phone: {phone_number}")
    print("-" * 50)
    
    try:
        response = requests.get(url, params={'phone': phone_number}, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        try:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print("Response Text:")
            print(response.text[:1000])
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask app")
        print("💡 Make sure Flask app is running on http://localhost:5000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    test_phone_api()


