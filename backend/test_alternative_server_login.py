#!/usr/bin/env python3
"""
Script untuk testing login ke server alternatif
http://154.26.138.135/000byte/
"""

import requests
import re
import sys
from urllib.parse import urlencode

# Konfigurasi server alternatif
ALTERNATIVE_SERVER_BASE = "http://154.26.138.135/000byte"
ALTERNATIVE_SERVER_LOGIN_URL = f"{ALTERNATIVE_SERVER_BASE}/login.php"
ALTERNATIVE_SERVER_SEARCH_NAME_URL = f"{ALTERNATIVE_SERVER_BASE}/cari_nama.php"
ALTERNATIVE_SERVER_USERNAME = "ferdi"
ALTERNATIVE_SERVER_PASSWORD = "pafer123"

def test_login():
    """Test login ke server alternatif"""
    print("=" * 60)
    print("TESTING LOGIN KE SERVER ALTERNATIF")
    print("=" * 60)
    print(f"URL: {ALTERNATIVE_SERVER_LOGIN_URL}")
    print(f"Username: {ALTERNATIVE_SERVER_USERNAME}")
    print(f"Password: {'*' * len(ALTERNATIVE_SERVER_PASSWORD)}")
    print()
    
    try:
        session = requests.Session()
        
        # Step 1: Get login page
        print("Step 1: Mengakses halaman login...")
        login_page = session.get(ALTERNATIVE_SERVER_LOGIN_URL, timeout=10)
        print(f"  Status Code: {login_page.status_code}")
        print(f"  URL: {login_page.url}")
        print(f"  Cookies sebelum login: {list(session.cookies.get_dict().keys())}")
        print()
        
        if login_page.status_code != 200:
            print(f"[ERROR] ERROR: Gagal mengakses halaman login: {login_page.status_code}")
            return None
        
        # Step 2: Extract form fields
        print("Step 2: Mengekstrak form fields...")
        login_html = login_page.text
        print(f"  HTML length: {len(login_html)} chars")
        print(f"  HTML preview (first 500 chars):")
        print(f"  {login_html[:500]}")
        print()
        
        # Find form action
        form_action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', login_html, re.IGNORECASE)
        form_action = form_action_match.group(1) if form_action_match else ALTERNATIVE_SERVER_LOGIN_URL
        if not form_action.startswith('http'):
            if form_action.startswith('/'):
                form_action = ALTERNATIVE_SERVER_BASE.rstrip('/') + form_action
            else:
                form_action = ALTERNATIVE_SERVER_LOGIN_URL.rsplit('/', 1)[0] + '/' + form_action
        print(f"  Form action: {form_action}")
        
        # Find input fields
        input_pattern = r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>'
        inputs = re.findall(input_pattern, login_html, re.IGNORECASE)
        print(f"  Input fields found: {inputs}")
        
        username_fields = []
        password_fields = []
        for field in inputs:
            field_lower = field.lower()
            if 'user' in field_lower or 'login' in field_lower:
                username_fields.append(field)
            elif 'pass' in field_lower:
                password_fields.append(field)
        
        username_field = username_fields[0] if username_fields else 'username'
        password_field = password_fields[0] if password_fields else 'password'
        print(f"  Using username field: {username_field}")
        print(f"  Using password field: {password_field}")
        print()
        
        # Step 3: Perform login
        print("Step 3: Melakukan login...")
        login_data = {
            username_field: ALTERNATIVE_SERVER_USERNAME,
            password_field: ALTERNATIVE_SERVER_PASSWORD
        }
        # Add common variations as backup
        if username_field != 'username':
            login_data['username'] = ALTERNATIVE_SERVER_USERNAME
        if password_field != 'password':
            login_data['password'] = ALTERNATIVE_SERVER_PASSWORD
        
        print(f"  Login data fields: {list(login_data.keys())}")
        print(f"  POST URL: {form_action}")
        
        login_response = session.post(
            form_action,
            data=login_data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': ALTERNATIVE_SERVER_LOGIN_URL,
                'Origin': ALTERNATIVE_SERVER_BASE.rstrip('/'),
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=10,
            allow_redirects=True
        )
        
        print(f"  Status Code: {login_response.status_code}")
        print(f"  Final URL: {login_response.url}")
        print(f"  Cookies setelah login: {list(session.cookies.get_dict().keys())}")
        print(f"  Cookie values: {session.cookies.get_dict()}")
        print()
        
        # Step 4: Check login result
        print("Step 4: Memeriksa hasil login...")
        final_url = login_response.url
        response_text = login_response.text.lower()
        
        is_still_on_login = (
            'login.php' in final_url.lower() and 
            ('username' in response_text or 'password' in response_text or 'login' in response_text)
        )
        
        if is_still_on_login:
            print("[ERROR] LOGIN GAGAL - Masih di halaman login")
            print(f"  Response URL: {final_url}")
            print(f"  Response preview (first 1000 chars):")
            print(f"  {login_response.text[:1000]}")
            return None
        
        if 'login.php' not in final_url.lower():
            print("[OK] LOGIN BERHASIL - Redirected away from login page")
            print(f"  Redirected to: {final_url}")
        elif len(session.cookies.get_dict()) > 0:
            print("[OK] LOGIN BERHASIL - Session cookie ditemukan")
        else:
            print("[WARNING]  LOGIN MUNGKIN BERHASIL - Tidak ada indikator jelas")
        
        print()
        
        # Step 5: Verify session by accessing search page
        print("Step 5: Memverifikasi session dengan mengakses halaman pencarian...")
        test_params = {'nama_lengkap': 'TEST'}
        verify_response = session.get(
            ALTERNATIVE_SERVER_SEARCH_NAME_URL,
            params=test_params,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': ALTERNATIVE_SERVER_BASE.rstrip('/'),
                'Accept': 'application/json, text/html, */*',
            },
            timeout=10,
            allow_redirects=True
        )
        
        verify_url_final = verify_response.url
        verify_text = verify_response.text.lower()[:200]
        
        print(f"  Status Code: {verify_response.status_code}")
        print(f"  Final URL: {verify_url_final}")
        print(f"  Response preview (first 500 chars):")
        print(f"  {verify_response.text[:500]}")
        print()
        
        if 'login.php' in verify_url_final.lower() or ('login' in verify_text and 'username' in verify_text):
            print("[ERROR] SESSION TIDAK VALID - Di-redirect ke login")
            return None
        
        print("[OK] SESSION VALID - Dapat mengakses halaman pencarian")
        print()
        
        return session
        
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] ERROR: Tidak dapat terhubung ke server: {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"[ERROR] ERROR: Timeout: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] ERROR: Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_search(session, nama_lengkap="IRWAN FERRY SUHARYONO"):
    """Test pencarian dengan session yang sudah login"""
    print("=" * 60)
    print("TESTING PENCARIAN")
    print("=" * 60)
    print(f"Nama: {nama_lengkap}")
    print()
    
    if not session:
        print("[ERROR] ERROR: Session tidak valid, tidak dapat melakukan pencarian")
        return
    
    try:
        search_params = {'nama_lengkap': nama_lengkap}
        search_url = f"{ALTERNATIVE_SERVER_SEARCH_NAME_URL}?{urlencode(search_params)}"
        
        print(f"URL Pencarian: {search_url}")
        print()
        
        search_response = session.get(
            ALTERNATIVE_SERVER_SEARCH_NAME_URL,
            params=search_params,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': ALTERNATIVE_SERVER_BASE.rstrip('/'),
                'Accept': 'application/json, text/html, */*',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            timeout=15,
            allow_redirects=True
        )
        
        print(f"Status Code: {search_response.status_code}")
        print(f"Final URL: {search_response.url}")
        print(f"Content-Type: {search_response.headers.get('Content-Type', 'N/A')}")
        print(f"Response Length: {len(search_response.text)} chars")
        print()
        
        if search_response.status_code != 200:
            print(f"[ERROR] ERROR: Status code {search_response.status_code}")
            print(f"Response text (first 500 chars):")
            print(search_response.text[:500])
            return
        
        # Check if redirected to login
        if 'login.php' in search_response.url.lower():
            print("[ERROR] ERROR: Di-redirect ke halaman login - session expired")
            return
        
        # Try to parse as JSON
        try:
            data = search_response.json()
            print("[OK] Response berhasil di-parse sebagai JSON")
            print(f"JSON Data:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print("[WARNING]  Response bukan JSON, mencoba parse sebagai HTML...")
            print()
            
            # Save full response to file for inspection
            with open('test_search_response.html', 'w', encoding='utf-8') as f:
                f.write(search_response.text)
            print(f"[OK] Full response disimpan ke: test_search_response.html")
            print()
            
            # Try to find JSON in script tags
            json_patterns = [
                r'<script[^>]*>.*?(\{.*?\}).*?</script>',
                r'var\s+data\s*=\s*(\{.*?\});',
                r'const\s+data\s*=\s*(\{.*?\});',
            ]
            found_json = False
            for pattern in json_patterns:
                json_match = re.search(pattern, search_response.text, re.DOTALL | re.IGNORECASE)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        data = json.loads(json_str)
                        print("[OK] Berhasil mengekstrak JSON dari HTML")
                        print(f"JSON Data:")
                        import json
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                        found_json = True
                        break
                    except:
                        continue
            
            if not found_json:
                # Try to extract from HTML table
                print("Mencoba mengekstrak data dari HTML table...")
                table_pattern = r'<table[^>]*>(.*?)</table>'
                table_match = re.search(table_pattern, search_response.text, re.DOTALL | re.IGNORECASE)
                if table_match:
                    print("[OK] Table ditemukan dalam HTML")
                    table_content = table_match.group(1)
                    # Extract rows
                    row_pattern = r'<tr[^>]*>(.*?)</tr>'
                    rows = re.findall(row_pattern, table_content, re.DOTALL | re.IGNORECASE)
                    print(f"  Jumlah rows: {len(rows)}")
                    for i, row in enumerate(rows[:5]):  # Show first 5 rows
                        print(f"  Row {i+1}: {row[:200]}...")
                
                # Show key parts of HTML
                print()
                print("Response HTML preview (key sections):")
                # Find result sections
                if 'result' in search_response.text.lower():
                    result_sections = re.findall(r'<[^>]*result[^>]*>.*?</[^>]*>', search_response.text, re.DOTALL | re.IGNORECASE)
                    for i, section in enumerate(result_sections[:3]):
                        print(f"  Result section {i+1}: {section[:300]}...")
                
                # Show full response (last 1000 chars if too long)
                print()
                print("Full response text:")
                if len(search_response.text) > 3000:
                    print(search_response.text[:1500])
                    print("...")
                    print(search_response.text[-1500:])
                else:
                    print(search_response.text)
        
    except Exception as e:
        print(f"[ERROR] ERROR: Exception saat pencarian: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print()
    print("MULAI TESTING SERVER ALTERNATIF")
    print()
    
    # Test login
    session = test_login()
    
    if session:
        print("[OK] LOGIN BERHASIL!")
        print()
        
        # Test search
        test_search(session, "IRWAN FERRY SUHARYONO")
    else:
        print("[ERROR] LOGIN GAGAL - Tidak dapat melanjutkan ke testing pencarian")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("TESTING SELESAI")
    print("=" * 60)

