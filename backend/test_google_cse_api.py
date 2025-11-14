#!/usr/bin/env python3
"""
Test script untuk memverifikasi Google CSE API
Jalankan: python test_google_cse_api.py
"""
import requests
import json
import sys

def test_google_cse_api(base_url='http://localhost:5000', query='test'):
    """Test Google CSE API endpoint"""
    print("=" * 60)
    print("🧪 Testing Google CSE API")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Query: {query}")
    print("-" * 60)
    
    try:
        # Test endpoint
        url = f"{base_url}/api/test-google-cse"
        params = {'q': query}
        
        print(f"[1/3] Sending request to: {url}")
        print(f"      Query: {query}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"[2/3] Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[3/3] Response received")
            print("\n" + "=" * 60)
            print("RESULT:")
            print("=" * 60)
            print(json.dumps(data, indent=2))
            print("=" * 60)
            
            if data.get('success'):
                print("\n✅ Google CSE API is WORKING!")
                print(f"   API Key Status: {data.get('api_key_status', 'unknown')}")
                print(f"   CSE ID Status: {data.get('cse_id_status', 'unknown')}")
                print(f"   Total Results: {data.get('total_results', 'N/A')}")
                print(f"   Items Found: {data.get('items_found', 0)}")
                return 0
            else:
                print("\n❌ Google CSE API Test FAILED!")
                print(f"   Error: {data.get('error_message', 'Unknown error')}")
                print(f"   Status Code: {data.get('status_code', 'N/A')}")
                print(f"   Error Code: {data.get('error_code', 'N/A')}")
                print(f"   API Key Status: {data.get('api_key_status', 'unknown')}")
                print(f"   CSE ID Status: {data.get('cse_id_status', 'unknown')}")
                if data.get('quota_exceeded'):
                    print("\n⚠️  QUOTA EXCEEDED - Daily limit reached!")
                    print("   Wait until tomorrow or upgrade to paid tier")
                return 1
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Cannot connect to server.")
        print("   Make sure the Flask server is running:")
        print("   python app.py")
        return 1
    except requests.exceptions.Timeout:
        print("\n❌ Request Timeout!")
        print("   Server took too long to respond")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else 'test'
    base_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'
    
    exit_code = test_google_cse_api(base_url, query)
    sys.exit(exit_code)

