#!/usr/bin/env python3
"""
clearance_face_search.py

Fitur tambahan:
 - --face-query / -f : path ke image file (jpg/png) untuk dijadikan query face
 - --face-threshold : threshold distance (default 0.50). Semakin kecil -> lebih ketat.
 - Skrip ambil hasil dari API (name/nik filter) dan bandingkan face encoding.
 - Butuh library: face_recognition (direkomendasikan) atau gunakan --no-face untuk non-face mode.

Contoh:
  # install dependencies (lihat README di bawah)
  python3 clearance_face_search.py --username rezarios --password 12345678 \
      --name "agus" --face-query ./query.jpg --save-face --out-dir ./matches --pretty
"""
import os
import sys
import json
import time
import base64
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

# --- Optional face libs loaded lazily ---
USE_FACE_LIB = False
try:
    import face_recognition
    USE_FACE_LIB = True
except Exception:
    USE_FACE_LIB = False

# ---------- Config ----------
BASE = os.environ.get("CLEARANCE_BASE", "http://10.1.54.224:8000")
LOGIN_PATH = "/auth/login"
SEARCH_PATH = "/clearance/ktp/search"
CACHE_PATH = Path(os.environ.get("CLEARANCE_TOKEN_CACHE", Path.home() / ".cache" / "clearance_token.json"))

# Fallback mode configuration
# PENTING: HARDCODE ke True untuk memastikan fallback selalu aktif!
FALLBACK_MODE = True  # HARDCODE - SELALU gunakan fallback mode untuk profiling
MAX_RETRY_ATTEMPTS = int(os.environ.get("CLEARANCE_MAX_RETRY", "3"))

# Server 116 fallback configuration (untuk profiling)
# PENTING: Server 116 menggunakan kredensial sendiri yang berbeda dari server 224
# - Server 224: menggunakan kredensial dari frontend (misalnya "rezarios"/"12345678")
# - Server 116: menggunakan kredensial hardcoded di bawah ini ("jambi"/"@ab526d")
# Kedua server memiliki kredensial yang berbeda dan tidak saling menggunakan!
# 
# KONFIGURASI NGROK: Jika aplikasi di-hosting di ngrok dan server 116 tidak bisa diakses,
# set environment variable SERVER_116_BASE ke URL yang bisa diakses (misalnya ngrok tunnel ke server 116)
SERVER_116_BASE = os.environ.get("SERVER_116_BASE", "http://10.1.54.116")
SERVER_116_LOGIN_URL = f"{SERVER_116_BASE}/auth/login"
SERVER_116_IDENTITY_SEARCH_URL = f"{SERVER_116_BASE}/toolkit/api/identity/search"
SERVER_116_USERNAME = os.environ.get("SERVER_116_USERNAME", "jambi")  # Kredensial khusus untuk server 116
SERVER_116_PASSWORD = os.environ.get("SERVER_116_PASSWORD", "@ab526d")  # Kredensial khusus untuk server 116

# Warning cache to prevent spam
_warning_cache = {}
WARNING_COOLDOWN = 300  # 5 minutes

# Session cache for server 116 (to maintain login session)
_server_116_session = None
_server_116_session_time = 0
_server_116_session_timeout = 3600  # 1 hour

def _clear_server_116_session():
    """Clear server 116 session cache"""
    global _server_116_session, _server_116_session_time
    _server_116_session = None
    _server_116_session_time = 0

# Server 224 availability cache (smart detection)
# PENTING: Initial state True tapi akan langsung check saat pertama kali dipanggil
_server_224_status = {
    'available': True,  # Assume available by default, but will check on first call
    'last_check': 0,  # 0 means never checked, will force check on first call
    'check_interval': 30,  # Check every 30 seconds (reduced for faster recovery detection)
    'consecutive_failures': 0,
    'max_failures': 1  # After 1 failure, mark as unavailable (more aggressive)
}
# ---------------------------

def safe_b64decode(data: str) -> bytes:
    data_bytes = data.encode("utf-8") if isinstance(data, str) else data
    rem = len(data_bytes) % 4
    if rem:
        data_bytes += b"=" * (4 - rem)
    return base64.urlsafe_b64decode(data_bytes)

def load_cached_token():
    if not CACHE_PATH.exists():
        return None
    try:
        data = json.loads(CACHE_PATH.read_text())
        return data.get("access_token")
    except Exception:
        return None

def save_cached_token(token: str):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"access_token": token, "saved_at": int(time.time())}
    CACHE_PATH.write_text(json.dumps(data))

def decode_jwt_payload(token: str):
    try:
        parts = token.split(".")
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem:
            payload_b64 += "=" * (4 - rem)
        raw = base64.urlsafe_b64decode(payload_b64)
        return json.loads(raw)
    except Exception:
        return {}

def token_valid(token: str, leeway_seconds=10) -> bool:
    if not token:
        return False
    payload = decode_jwt_payload(token)
    exp = payload.get("exp")
    if not exp:
        return True
    return (exp - leeway_seconds) > int(time.time())

def _check_server_224_availability(quick_check=False, force_check=False):
    """Quick check if server 224 is available - returns False immediately if server is marked unavailable"""
    global _server_224_status
    
    current_time = time.time()
    
    # PENTING: Jika server sudah ditandai tidak tersedia, langsung return False TANPA melakukan request apapun
    # Ini untuk menghindari delay yang tidak perlu
    if not _server_224_status['available'] and not force_check:
        # Only re-check after check_interval to allow recovery (server mungkin sudah hidup kembali)
        time_since_check = current_time - _server_224_status['last_check']
        if time_since_check < _server_224_status['check_interval']:
            # Server masih ditandai tidak tersedia dan belum cukup waktu untuk re-check
            # Langsung return False tanpa melakukan request - INI YANG MEMBUAT FLEKSIBEL!
            return False
        # Jika sudah cukup waktu (30 detik), coba check lagi untuk recovery detection
        # Fall through to check below
    
    # If we recently checked and server is available, trust the cache (no need to check again)
    if _server_224_status['available'] and not force_check:
        time_since_check = current_time - _server_224_status['last_check']
        if time_since_check < _server_224_status['check_interval']:
            return True
    
    # Perform quick availability check (only if we need to check)
    try:
        # Use very short timeout for quick check (0.5 second for quick_check, 2 for normal)
        # Semakin pendek timeout, semakin cepat deteksi kegagalan
        timeout = 0.5 if quick_check else 2
        url = BASE.rstrip("/") + LOGIN_PATH
        # Just try to connect, don't actually login
        response = requests.get(url, timeout=timeout)
        # If we get any response (even 404/405), server is up
        _server_224_status['available'] = True
        _server_224_status['last_check'] = current_time
        _server_224_status['consecutive_failures'] = 0
        return True
    except (requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout, 
            requests.exceptions.ConnectTimeout) as e:
        # Server is not available - mark immediately
        _server_224_status['consecutive_failures'] += 1
        _server_224_status['last_check'] = current_time
        _server_224_status['available'] = False  # Mark immediately, don't wait
        
        warning_key = "server_224_marked_unavailable"
        if _should_show_warning(warning_key):
            print(f"INFO: Server 224 ditandai sebagai tidak tersedia (quick check)", file=sys.stderr)
        
        return False
    except Exception:
        # Other errors - assume server might be available but having issues
        # But if we have consecutive failures, mark as unavailable
        if _server_224_status['consecutive_failures'] >= _server_224_status['max_failures']:
            _server_224_status['available'] = False
            return False
        return True  # Give benefit of the doubt

def do_login(username: str, password: str, retry_count=0):
    """
    Login ke server 224 menggunakan kredensial yang diberikan.
    Catatan: Kredensial ini khusus untuk server 224, tidak digunakan untuk server 116.
    Server 116 menggunakan kredensial hardcoded (SERVER_116_USERNAME/SERVER_116_PASSWORD).
    
    PENTING: Fungsi ini TIDAK akan dipanggil jika server 224 tidak tersedia karena
    ensure_token() sudah skip sebelumnya. Tapi tetap ada check di sini untuk safety.
    """
    print(f"DEBUG: do_login dipanggil - FALLBACK_MODE={FALLBACK_MODE}, retry_count={retry_count}", file=sys.stderr)
    
    # Smart check: if server 224 is marked unavailable, skip immediately
    # PENTING: JANGAN PERNAH mencoba login jika server tidak tersedia!
    if FALLBACK_MODE:
        server_available = _check_server_224_availability(quick_check=True)
        print(f"DEBUG: server_available={server_available}", file=sys.stderr)
        if not server_available:
            print(f"INFO: [FLEKSIBEL] Server 224 tidak tersedia, SKIP login dengan kredensial {username}", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] TIDAK akan mencoba login ke server 224 karena server tidak tersedia", file=sys.stderr)
            return None
    
    # Hanya sampai di sini jika server 224 tersedia
    print(f"DEBUG: Mencoba login ke server 224 (server tersedia atau FALLBACK_MODE=False)", file=sys.stderr)
    url = BASE.rstrip("/") + LOGIN_PATH
    
    # Try form data first (application/x-www-form-urlencoded)
    data = {
        "username": username,
        "password": password,
    }
    
    try:
        # Use shorter timeout for faster failure detection
        timeout = 5 if FALLBACK_MODE else 15
        r = requests.post(url, data=data, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        
        # Check for error response first
        if j.get("status") == "error":
            error_msg = j.get("message", "Unknown error")
            warning_key = f"login_error_{error_msg.replace(' ', '_')}"
            if _should_show_warning(warning_key):
                print(f"ERROR: Login gagal - {error_msg}", file=sys.stderr)
                print(f"Response: {j}", file=sys.stderr)
            
            # If fallback mode is enabled, don't exit
            if FALLBACK_MODE:
                if _should_show_warning("fallback_mode_enabled"):
                    print("INFO: Fallback mode enabled, tidak akan exit", file=sys.stderr)
                return None
            else:
                sys.exit(4)
        
        # Try to get token from various possible fields
        token = j.get("access_token") or j.get("token") or (j.get("data") or {}).get("token")
        if not token:
            warning_key = "no_access_token"
            if _should_show_warning(warning_key):
                print("ERROR: tidak menemukan access_token di response login:", j, file=sys.stderr)
            if FALLBACK_MODE:
                if _should_show_warning("fallback_mode_enabled"):
                    print("INFO: Fallback mode enabled, tidak akan exit", file=sys.stderr)
                return None
            else:
                if _should_show_warning("retry_login"):
                    print("INFO: Mencoba login ulang dengan kredensial yang berbeda...", file=sys.stderr)
                return None
        
        save_cached_token(token)
        # Mark server as available on successful login
        _server_224_status['available'] = True
        _server_224_status['consecutive_failures'] = 0
        return token
        
    except (requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout, 
            requests.exceptions.ConnectTimeout) as e:
        # Connection/timeout errors - mark server as unavailable IMMEDIATELY
        _server_224_status['consecutive_failures'] += 1
        _server_224_status['last_check'] = time.time()
        _server_224_status['available'] = False
        
        error_type = type(e).__name__
        
        # PENTING: Jika FALLBACK_MODE aktif, LANGSUNG return None TANPA RETRY!
        # Check ini HARUS di awal sebelum ada kode lain!
        if FALLBACK_MODE:
            print(f"INFO: [FLEKSIBEL] ❌ Server 224 MATI ({error_type}), LANGSUNG ke server 116 TANPA RETRY", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] ✅ Kredensial dari frontend AKAN digunakan untuk server 116", file=sys.stderr)
            return None  # LANGSUNG return, TIDAK ada retry!
        
        # Kode di bawah ini HANYA dijalankan jika FALLBACK_MODE = False
        print(f"INFO: Server 224 tidak dapat diakses ({error_type})", file=sys.stderr)
        
        if retry_count < MAX_RETRY_ATTEMPTS:
            print(f"INFO: Mencoba lagi ({retry_count + 1}/{MAX_RETRY_ATTEMPTS})...", file=sys.stderr)
            time.sleep(1)
            return do_login(username, password, retry_count + 1)
        else:
            print("ERROR: Maksimal percobaan login tercapai", file=sys.stderr)
            sys.exit(4)
    
    except requests.exceptions.RequestException as e:
        # Other request errors (not connection/timeout)
        error_type = type(e).__name__
        status_code = 'unknown'
        if hasattr(e, 'response') and e.response is not None:
            status_code = getattr(e.response, 'status_code', 'unknown')
        
        # PENTING: Jika FALLBACK_MODE aktif, LANGSUNG return None TANPA RETRY!
        if FALLBACK_MODE:
            print(f"ERROR: Gagal login ke server 224: {e}", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] SKIP retry, langsung menggunakan server 116", file=sys.stderr)
            return None  # LANGSUNG return, TIDAK ada retry!
        
        # Kode di bawah ini HANYA dijalankan jika FALLBACK_MODE = False
        print(f"ERROR: Gagal login ke server 224: {e}", file=sys.stderr)
        
        if retry_count < MAX_RETRY_ATTEMPTS:
            print(f"INFO: Mencoba lagi ({retry_count + 1}/{MAX_RETRY_ATTEMPTS})...", file=sys.stderr)
            time.sleep(2)
            return do_login(username, password, retry_count + 1)
        else:
            print("ERROR: Maksimal percobaan login tercapai", file=sys.stderr)
            sys.exit(4)

def ensure_token(username: str, password: str, force_refresh=False):
    """
    Mendapatkan token untuk server 224 menggunakan kredensial yang diberikan.
    Catatan: 
    - Kredensial ini (username/password) khusus untuk server 224
    - Jika server 224 tidak tersedia, akan mengembalikan fallback_token
    - Server 116 menggunakan kredensial sendiri yang hardcoded (tidak menggunakan kredensial ini)
    - PENTING: Kredensial dari frontend (username/password) TIDAK digunakan untuk server 116!
    """
    # PENTING: Check server 224 availability FIRST - jika tidak tersedia, langsung skip
    # Ini membuat sistem fleksibel: tidak mencoba login ke server 224 jika sudah mati
    # PENTING: JANGAN PERNAH mencoba login ke server 224 dengan kredensial dari frontend jika server tidak tersedia!
    if FALLBACK_MODE:
        server_available = _check_server_224_availability(quick_check=True)
        if not server_available:
            print("INFO: [FLEKSIBEL] Server 224 tidak tersedia, langsung skip ke server 116", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] ⚠️ Kredensial {username} TIDAK digunakan untuk server 116", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] ✅ Server 116 akan menggunakan kredensial hardcoded: {SERVER_116_USERNAME}/@ab526d", file=sys.stderr)
            # Return fallback token immediately - NO DELAY, NO RETRY, NO LOGIN ATTEMPT
            # Kredensial dari frontend (username/password) TIDAK digunakan sama sekali untuk server 116!
            return "fallback_token_" + str(int(time.time()))
    
    # If server 224 is available, try to use cached token first
    if not force_refresh:
        token = load_cached_token()
        if token and token_valid(token):
            # Verify server is still available before using cached token
            if FALLBACK_MODE:
                server_available = _check_server_224_availability(quick_check=True)
                if not server_available:
                    # Server became unavailable, use fallback
                    print("INFO: [FLEKSIBEL] Server 224 menjadi tidak tersedia saat menggunakan cached token, switch ke server 116", file=sys.stderr)
                    return "fallback_token_" + str(int(time.time()))
            return token
    
    # Try to login ke server 224 dengan kredensial yang diberikan (hanya jika server tersedia)
    # PENTING: Kredensial ini (username/password) HANYA untuk server 224, BUKAN untuk server 116!
    token = do_login(username, password)
    if token is None:
        warning_key = "ensure_token_fallback"
        if _should_show_warning(warning_key):
            print("INFO: [FLEKSIBEL] Login ke server 224 gagal, menggunakan server 116 sebagai fallback", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] Kredensial dari frontend ({username}) TIDAK digunakan untuk server 116", file=sys.stderr)
            print(f"INFO: [FLEKSIBEL] Server 116 akan menggunakan kredensial sendiri: {SERVER_116_USERNAME}", file=sys.stderr)
        # Return a dummy token for fallback mode
        return "fallback_token_" + str(int(time.time()))
    
    # Save the new token to cache
    if token and not token.startswith("fallback_token_"):
        save_cached_token(token)
        # Mark server as available on successful login
        _server_224_status['available'] = True
        _server_224_status['consecutive_failures'] = 0
    
    return token

def _should_show_warning(warning_key: str) -> bool:
    """Check if warning should be shown based on cooldown"""
    current_time = time.time()
    if warning_key not in _warning_cache:
        _warning_cache[warning_key] = current_time
        return True
    
    last_shown = _warning_cache[warning_key]
    if current_time - last_shown > WARNING_COOLDOWN:
        _warning_cache[warning_key] = current_time
        return True
    
    return False

def _login_server_116(username=None, password=None):
    """
    Login ke server 116 SELALU menggunakan kredensial hardcoded (jambi/@ab526d).
    PENTING: Server 116 dan server 224 memiliki kredensial yang BERBEDA!
    - Server 224: rezarios/12345678
    - Server 116: jambi/@ab526d
    
    Parameter username/password diabaikan - hanya untuk kompatibilitas API.
    """
    global _server_116_session, _server_116_session_time
    
    # PENTING: SELALU gunakan kredensial hardcoded untuk server 116!
    # JANGAN PERNAH gunakan kredensial dari frontend (rezarios) untuk server 116!
    use_username = SERVER_116_USERNAME  # SELALU jambi
    use_password = SERVER_116_PASSWORD  # SELALU @ab526d
    
    # Check if session is still valid
    current_time = time.time()
    if _server_116_session and (current_time - _server_116_session_time) < _server_116_session_timeout:
        print("INFO: [SERVER_116] Menggunakan session yang masih valid", file=sys.stderr)
        return _server_116_session
    
    # Create new session
    session = requests.Session()
    
    try:
        print(f"INFO: [SERVER_116] Mencoba login dengan kredensial hardcoded: {use_username}", file=sys.stderr)
        print(f"INFO: [SERVER_116] PENTING: Server 116 SELALU menggunakan kredensial jambi/@ab526d (BUKAN rezarios!)", file=sys.stderr)
        
        # Get login page to extract CSRF token
        login_page_response = session.get(SERVER_116_LOGIN_URL, timeout=5)
        if login_page_response.status_code != 200:
            print(f"ERROR: [SERVER_116] Gagal mengakses halaman login: {login_page_response.status_code}", file=sys.stderr)
            return None
        
        # Extract CSRF token
        import re
        csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', login_page_response.text)
        csrf_token = csrf_match.group(1) if csrf_match else 'jbHXcAQGRIgskYpnCBIVo43cTQg='
        
        # Login dengan kredensial yang dipilih
        login_data = {
            'username': use_username,
            'password': use_password,
            '_csrf': csrf_token
        }
        
        print(f"INFO: [SERVER_116] Mengirim request login dengan username: {use_username}", file=sys.stderr)
        
        login_response = session.post(SERVER_116_LOGIN_URL,
                                     data=login_data,
                                     headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                     timeout=10)
        
        if login_response.status_code != 200:
            print(f"ERROR: [SERVER_116] Gagal login dengan {use_username}: {login_response.status_code}", file=sys.stderr)
            return None
        
        # Save session
        _server_116_session = session
        _server_116_session_time = current_time
        
        print(f"INFO: [SERVER_116] ✅ Login berhasil dengan username: {use_username}", file=sys.stderr)
        
        return session
        
    except requests.exceptions.ConnectionError as e:
        warning_key = "server_116_connection_error"
        if _should_show_warning(warning_key):
            print(f"ERROR: [SERVER_116] Tidak dapat terhubung ke server 116", file=sys.stderr)
            print(f"ERROR: [SERVER_116] URL: {SERVER_116_BASE}", file=sys.stderr)
            print(f"ERROR: [SERVER_116] Kemungkinan masalah:", file=sys.stderr)
            print(f"ERROR: [SERVER_116]   1. Server 116 tidak dapat diakses dari jaringan ini", file=sys.stderr)
            if "10.1.54.116" in SERVER_116_BASE:
                print(f"ERROR: [SERVER_116]   2. IP {SERVER_116_BASE} adalah IP private dan tidak bisa diakses dari ngrok", file=sys.stderr)
                print(f"ERROR: [SERVER_116]   3. Set environment variable SERVER_116_BASE ke URL yang bisa diakses", file=sys.stderr)
                print(f"ERROR: [SERVER_116]   Contoh: export SERVER_116_BASE=http://your-ngrok-url.ngrok.io", file=sys.stderr)
        _clear_server_116_session()
        return None
    except requests.exceptions.Timeout as e:
        warning_key = "server_116_timeout"
        if _should_show_warning(warning_key):
            print(f"ERROR: [SERVER_116] Timeout saat mengakses server 116: {SERVER_116_BASE}", file=sys.stderr)
        _clear_server_116_session()
        return None
    except Exception as e:
        warning_key = "server_116_login_exception"
        if _should_show_warning(warning_key):
            print(f"ERROR: [SERVER_116] Exception saat login: {str(e)}", file=sys.stderr)
            print(f"ERROR: [SERVER_116] Tipe error: {type(e).__name__}", file=sys.stderr)
            print(f"ERROR: [SERVER_116] URL yang dicoba: {SERVER_116_BASE}", file=sys.stderr)
        _clear_server_116_session()
        return None

def _search_server_116(params: dict, username=None, password=None):
    """Search using server 116 identity API"""
    session = _login_server_116(username, password)
    if not session:
        print("ERROR: [SERVER_116] Tidak dapat login ke server 116", file=sys.stderr)
        return None
    
    try:
        # Build search URL based on params
        search_params = {}
        
        print(f"DEBUG: [SERVER_116] Parameter yang diterima: {params}", file=sys.stderr)
        
        # Priority: name > family_cert_number > nik
        if params.get('name'):
            search_params['full_name'] = params['name']
            search_params['limit'] = params.get('limit', '25')
            print(f"INFO: [SERVER_116] Mencari dengan nama: {params['name']}", file=sys.stderr)
        elif params.get('family_cert_number'):
            search_params['family_cert_number'] = params['family_cert_number']
            print(f"INFO: [SERVER_116] Mencari dengan KK: {params['family_cert_number']}", file=sys.stderr)
        elif params.get('nik'):
            # Server 116 uses ktp_number parameter for NIK search
            nik_value = params['nik'].strip()
            if nik_value:
                search_params['ktp_number'] = nik_value
                print(f"INFO: [SERVER_116] Mencari dengan NIK: {nik_value} (parameter: ktp_number)", file=sys.stderr)
            else:
                print(f"ERROR: [SERVER_116] NIK kosong", file=sys.stderr)
                return None
        else:
            print("ERROR: [SERVER_116] Tidak ada parameter pencarian yang valid", file=sys.stderr)
            return None
        
        # Perform search
        from urllib.parse import urlencode
        full_url = f"{SERVER_116_IDENTITY_SEARCH_URL}?{urlencode(search_params)}"
        print(f"INFO: [SERVER_116] URL pencarian: {full_url}", file=sys.stderr)
        
        search_response = session.get(SERVER_116_IDENTITY_SEARCH_URL, params=search_params, timeout=15)
        
        print(f"INFO: [SERVER_116] Response status: {search_response.status_code}", file=sys.stderr)
        
        if search_response.status_code != 200:
            print(f"ERROR: [SERVER_116] Gagal melakukan pencarian: {search_response.status_code}", file=sys.stderr)
            print(f"ERROR: [SERVER_116] Response text: {search_response.text[:500]}", file=sys.stderr)
            return None
        
        # Check if response is HTML (login page) instead of JSON
        content_type = search_response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            print(f"ERROR: [SERVER_116] Response adalah HTML (bukan JSON) - session expired!", file=sys.stderr)
            # Clear session dan retry dengan hardcoded
            _clear_server_116_session()
            print(f"INFO: [SERVER_116] ✅ Session cleared, retry dengan kredensial hardcoded", file=sys.stderr)
            return _search_server_116(params)  # Recursive call
            return None
        
        # Parse response
        try:
            data = search_response.json()
            print(f"INFO: [SERVER_116] Response berhasil di-parse", file=sys.stderr)
            print(f"DEBUG: [SERVER_116] Response keys: {list(data.keys())}", file=sys.stderr)
        except Exception as json_error:
            print(f"ERROR: [SERVER_116] Gagal parse JSON response: {json_error}", file=sys.stderr)
            print(f"ERROR: [SERVER_116] Response text: {search_response.text[:500]}", file=sys.stderr)
            return None
        
        # Convert server 116 response format to server 224 format
        # Server 116 format: {"error":"","person":[...],"success":true}
        # Server 224 format: {"person":[...]}
        if 'person' in data:
            person_list = data['person']
            if isinstance(person_list, list):
                person_count = len(person_list)
                print(f"INFO: [SERVER_116] Ditemukan {person_count} hasil", file=sys.stderr)
                if person_count > 0:
                    first_person = person_list[0]
                    print(f"INFO: [SERVER_116] Contoh hasil pertama - NIK: {first_person.get('ktp_number', 'N/A')}, Nama: {first_person.get('full_name', 'N/A')}", file=sys.stderr)
                else:
                    print(f"WARNING: [SERVER_116] Array person kosong - tidak ada hasil untuk NIK ini", file=sys.stderr)
                # Always return person array (even if empty) - this indicates server 116 was accessed
                return {"person": person_list}
            else:
                print(f"ERROR: [SERVER_116] Field 'person' bukan list, type: {type(person_list)}", file=sys.stderr)
                return {"person": []}
        else:
            print(f"ERROR: [SERVER_116] Field 'person' tidak ditemukan dalam response", file=sys.stderr)
            print(f"DEBUG: [SERVER_116] Full response: {data}", file=sys.stderr)
            return {"person": []}
            
    except Exception as e:
        warning_key = "server_116_search_exception"
        if _should_show_warning(warning_key):
            print(f"WARNING: Server 116 - Exception saat pencarian: {e}", file=sys.stderr)
        return None

def call_search(token: str, params: dict, username=None, password=None):
    # Check if this is a fallback token - if so, skip server 224 and go directly to server 116
    is_fallback_token = token.startswith("fallback_token_")
    
    # Smart check: if server 224 is marked unavailable, skip directly to server 116 IMMEDIATELY
    # This avoids any delay or retry attempts to server 224
    if not is_fallback_token and FALLBACK_MODE:
        if not _check_server_224_availability(quick_check=True):
            warning_key = "call_search_skip_224"
            if _should_show_warning(warning_key):
                print("INFO: Server 224 tidak tersedia, langsung menggunakan server 116 untuk pencarian", file=sys.stderr)
            is_fallback_token = True  # Treat as fallback to use server 116
    
    # Only try server 224 if it's available AND we have a valid token (not fallback token)
    if not is_fallback_token:
        # Try server 224 first
        url = BASE.rstrip("/") + SEARCH_PATH
        headers = {
            "Authorization": f"Bearer {token}",
            "Origin": BASE.split("://", 1)[1] if "://" in BASE else BASE,
            "Referer": BASE if BASE.endswith("/") else BASE + "/",
            "Accept": "application/json",
        }
        
        try:
            # Use shorter timeout for faster failure detection (5 seconds in fallback mode)
            timeout = 5 if FALLBACK_MODE else 30
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            result = r.json()
            # Mark server as available on successful search
            _server_224_status['available'] = True
            _server_224_status['consecutive_failures'] = 0
            return result
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout, 
                requests.exceptions.ConnectTimeout) as e:
            # Connection/timeout errors - mark server as unavailable IMMEDIATELY
            _server_224_status['consecutive_failures'] += 1
            _server_224_status['last_check'] = time.time()
            _server_224_status['available'] = False  # Mark immediately
            
            error_type = type(e).__name__
            warning_key = f"server_224_search_failed_{error_type}"
            
            if _should_show_warning(warning_key):
                print(f"INFO: Server 224 tidak dapat diakses untuk pencarian ({error_type}), menggunakan server 116", file=sys.stderr)
        except requests.exceptions.RequestException as e:
            # Other request errors
            error_type = type(e).__name__
            status_code = 'unknown'
            if hasattr(e, 'response') and e.response is not None:
                status_code = getattr(e.response, 'status_code', 'unknown')
            warning_key = f"server_error_{error_type}_{status_code}"
            
            if _should_show_warning(warning_key):
                print(f"WARNING: Gagal mengakses server 224: {e}", file=sys.stderr)
                print("Mencoba fallback ke server 116...", file=sys.stderr)
    
    # If we reach here, either server 224 failed or we have a fallback token
    # Try server 116 fallback for profiling
    # PENTING: Server 116 menggunakan kredensial sendiri (hardcoded), bukan kredensial dari server 224
    warning_key = "server_116_fallback_attempt"
    if _should_show_warning(warning_key):
        if is_fallback_token:
            print("INFO: [FLEKSIBEL] ❌ Server 224 MATI - Menggunakan server 116", file=sys.stderr)
        else:
            print("INFO: [FLEKSIBEL] ❌ Server 224 GAGAL - Menggunakan server 116", file=sys.stderr)
        print(f"INFO: [FLEKSIBEL] ✅ Menggunakan server 116 dengan kredensial hardcoded: {SERVER_116_USERNAME}/@ab526d", file=sys.stderr)
        print(f"INFO: [FLEKSIBEL] ⚠️ PENTING: Server 116 dan 224 memiliki kredensial BERBEDA!", file=sys.stderr)
    
    server_116_result = _search_server_116(params, username, password)
    
    if server_116_result is None:
        warning_key = "server_116_fallback_failed"
        if _should_show_warning(warning_key):
            print("WARNING: Server 116 mengembalikan None (gagal login atau exception)", file=sys.stderr)
        
        # Check if this is a connection error (likely ngrok issue)
        is_connection_error = False
        if "10.1.54.116" in SERVER_116_BASE:
            is_connection_error = True
        
        error_message = "Server eksternal tidak dapat diakses."
        if is_connection_error:
            error_message += " Kemungkinan masalah: Server 116 menggunakan IP private yang tidak bisa diakses dari ngrok. "
            error_message += "Solusi: Setup ngrok tunnel untuk server 116 dan set environment variable SERVER_116_BASE."
        else:
            error_message += " Silakan coba lagi nanti atau hubungi administrator."
        
        return {
            "person": [], 
            "message": error_message,
            "_server_116_unavailable": True,
            "_server_116_connection_error": is_connection_error,
            "_server_116_base": SERVER_116_BASE
        }
    
    # Check if we have person field (even if empty)
    if isinstance(server_116_result, dict) and 'person' in server_116_result:
        person_list = server_116_result.get('person', [])
        person_count = len(person_list) if isinstance(person_list, list) else 0
        
        # Always return server 116 result (even if empty) to indicate server 116 was used
        warning_key = "server_116_fallback_success" if person_count > 0 else "server_116_fallback_empty"
        if _should_show_warning(warning_key):
            if person_count > 0:
                print(f"INFO: [OK] Berhasil menggunakan server 116 sebagai fallback - ditemukan {person_count} hasil", file=sys.stderr)
            else:
                print(f"INFO: Server 116 berhasil diakses tapi tidak mengembalikan hasil (array person kosong)", file=sys.stderr)
        
        # Add flag to indicate server 116 was used (even if empty)
        server_116_result['_server_116_fallback'] = True
        server_116_result['_server_224_unavailable'] = True
        return server_116_result
    
    # If server 116 result doesn't have person field
    warning_key = "server_116_fallback_no_person_field"
    if _should_show_warning(warning_key):
        print("WARNING: Server 116 result tidak memiliki field 'person'", file=sys.stderr)
    
    return {"person": [], "message": "Tidak ada hasil ditemukan di server alternatif."}

# ---- face utilities (face_recognition) ----
def load_image_file_to_encoding(path: Path):
    """Return first face encoding from image file or None."""
    if not USE_FACE_LIB:
        raise RuntimeError("Library face_recognition tidak ditemukan. Install terlebih dahulu.")
    img = face_recognition.load_image_file(str(path))
    encs = face_recognition.face_encodings(img)
    if not encs:
        return None
    return encs[0]

def get_encoding_from_base64_face(base64_str: str):
    """Decode base64 image (face), save to temp, and return encoding or None."""
    if not base64_str:
        return None
    if not USE_FACE_LIB:
        raise RuntimeError("Library face_recognition tidak ditemukan. Install terlebih dahulu.")
    # strip data: prefix bila ada
    raw = base64_str
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    b = safe_b64decode(raw)
    # write to temp file then load
    import io
    import numpy as np
    from PIL import Image
    img = Image.open(io.BytesIO(b)).convert("RGB")
    arr = np.array(img)
    encs = face_recognition.face_encodings(arr)
    if not encs:
        return None
    return encs[0]

def face_distance(a, b):
    """wrapper to compute euclidean distance"""
    import numpy as np
    return float(((a - b) ** 2).sum() ** 0.5)

# --------------------------------------------

def save_face_image(base64_str: str, out_dir: Path, filename_prefix: str = "face"):
    if not base64_str:
        return None
    try:
        raw = base64_str
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        img_bytes = safe_b64decode(raw)
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{filename_prefix}_{int(time.time()*1000)}.jpg"
        out_path = out_dir / fname
        out_path.write_bytes(img_bytes)
        return out_path
    except Exception as e:
        print("ERROR saat menyimpan face image:", e, file=sys.stderr)
        return None

def parse_people_from_response(j):
    people = j.get("person") or j.get("data") or []
    if isinstance(people, dict):
        return [people]
    if isinstance(people, list):
        return people
    return []

def run_face_search_loop(token, params, query_image_path: Path, threshold: float, out_dir: Path, pretty=False):
    # 1) compute query encoding
    if not USE_FACE_LIB:
        print("ERROR: face_recognition library tidak terpasang. Install: pip install face_recognition (butuh dlib).", file=sys.stderr)
        sys.exit(2)

    print("Menghitung encoding untuk query image:", query_image_path)
    q_enc = load_image_file_to_encoding(query_image_path)
    if q_enc is None:
        print("Tidak menemukan wajah pada query image.", file=sys.stderr)
        sys.exit(3)

    # 2) ambil search results (satu page dulu)
    print("Mengambil hasil dari API...")
    j = call_search(token, params)
    people = parse_people_from_response(j)
    if not people:
        print("Tidak ada person yang dikembalikan oleh API.")
        return

    matches = []
    tmp_dir = Path(".") / "tmp_clearance_faces"
    tmp_dir.mkdir(exist_ok=True)
    for p in people:
        face_b64 = p.get("face") or ""
        if not face_b64:
            continue
        # get encoding
        try:
            enc = get_encoding_from_base64_face(face_b64)
        except Exception as e:
            # skip if face lib error
            print("Warning: gagal decode face untuk", p.get("ktp_number") or p.get("full_name"), "-", e)
            continue
        if enc is None:
            # no face detected in candidate image
            continue
        # compute distance (euclidean)
        import numpy as np
        dist = np.linalg.norm(np.array(q_enc) - np.array(enc))
        # lower distance == more similar. face_recognition uses 0.6 threshold commonly.
        if dist <= threshold:
            matches.append((dist, p, enc, face_b64))
    # sort by distance asc
    matches.sort(key=lambda x: x[0])
    if not matches:
        print("Tidak ditemukan match di halaman ini dengan threshold", threshold)
        return
    print(f"Ditemukan {len(matches)} kandidat match (threshold={threshold}):")
    for dist, p, enc, face_b64 in matches:
        print("-"*30)
        print("NIK:", p.get("ktp_number"))
        print("Nama:", p.get("full_name"))
        print("Tanggal Lahir:", p.get("date_of_birth"))
        print("Score (distance):", dist)
        if pretty:
            print("Full JSON:")
            print(json.dumps(p, indent=2, ensure_ascii=False))
        if out_dir:
            saved = save_face_image(face_b64, out_dir, filename_prefix=str(p.get("ktp_number") or p.get("full_name") or "face"))
            if saved:
                print("Face disimpan ke:", saved)
    print("Selesai.")

def main():
    parser = argparse.ArgumentParser(description="Clearance face search")
    parser.add_argument("--username", "-u", help="username (atau set env MY_USERNAME)")
    parser.add_argument("--password", "-p", help="password (atau set env MY_PASSWORD)")
    parser.add_argument("--name", help="filter name")
    parser.add_argument("--nik", help="filter nik")
    parser.add_argument("--family_cert_number", help="filter family certificate number")
    parser.add_argument("--tempat_lahir", help="filter birth place")
    parser.add_argument("--tanggal_lahir", help="filter birth date")
    parser.add_argument("--no_prop", help="filter province code")
    parser.add_argument("--no_kab", help="filter city/regency code")
    parser.add_argument("--no_kec", help="filter district code")
    parser.add_argument("--no_desa", help="filter village code")
    parser.add_argument("--page", default="1")
    parser.add_argument("--face-query", "-f", help="path to query face image (jpg/png)")
    parser.add_argument("--face-threshold", type=float, default=0.50, help="threshold distance (lower stricter). default 0.50")
    parser.add_argument("--save-face", action="store_true", help="save faces from results")
    parser.add_argument("--out-dir", default="./faces", help="output directory")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--force-login", action="store_true")
    args = parser.parse_args()

    username = args.username or os.environ.get("MY_USERNAME")
    password = args.password or os.environ.get("MY_PASSWORD")
    if not username or not password:
        print("ERROR: butuh username & password.", file=sys.stderr)
        sys.exit(1)

    if not args.name and not args.nik and not args.family_cert_number and not args.tempat_lahir and not args.tanggal_lahir and not args.no_prop and not args.no_kab and not args.no_kec and not args.no_desa:
        print("ERROR: tentukan minimal satu parameter untuk membatasi hasil (--name, --nik, --family_cert_number, --tempat_lahir, --tanggal_lahir, --no_prop, --no_kab, --no_kec, atau --no_desa).", file=sys.stderr)
        sys.exit(1)

    token = ensure_token(username, password, force_refresh=args.force_login)

    params = {
        "name": args.name or "",
        "nik": args.nik or "",
        "family_cert_number": args.family_cert_number or "",
        "tempat_lahir": args.tempat_lahir or "",
        "tanggal_lahir": args.tanggal_lahir or "",
        "no_prop": args.no_prop or "",
        "no_kab": args.no_kab or "",
        "no_kec": args.no_kec or "",
        "no_desa": args.no_desa or "",
        "page": args.page
    }

    out_dir = Path(args.out_dir)
    # If user provided face-query -> run face search
    if args.face_query:
        qpath = Path(args.face_query)
        if not qpath.exists():
            print("ERROR: file query tidak ditemukan:", qpath, file=sys.stderr)
            sys.exit(1)
        run_face_search_loop(token, params, qpath, threshold=args.face_threshold, out_dir=out_dir, pretty=args.pretty)
        return

    # fallback: non-face mode -> just print results and optionally save face images
    j = call_search(token, params)
    people = parse_people_from_response(j)
    if not people:
        print("Tidak ada hasil.")
        return
    for i, p in enumerate(people, start=1):
        print("="*30)
        print(f"Result #{i}")
        print("Nama:", p.get("full_name"))
        print("NIK:", p.get("ktp_number"))
        print("TTL:", p.get("birth_place"), p.get("date_of_birth"))
        if args.save_face and p.get("face"):
            saved = save_face_image(p.get("face"), out_dir, filename_prefix=str(p.get("ktp_number") or p.get("full_name") or "face"))
            if saved:
                print("Face saved to:", saved)
        if args.pretty:
            print(json.dumps(p, indent=2, ensure_ascii=False))
    print("Selesai.")

if __name__ == "__main__":
    main()
