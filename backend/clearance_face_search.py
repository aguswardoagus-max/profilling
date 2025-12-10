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
import re
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

# Server Alternatif Configuration (http://154.26.138.135/000byte/)
# Server alternatif sebagai fallback jika server 116 dan 224 tidak tersedia
ALTERNATIVE_SERVER_BASE = os.environ.get("ALTERNATIVE_SERVER_BASE", "http://154.26.138.135/000byte")
ALTERNATIVE_SERVER_LOGIN_URL = f"{ALTERNATIVE_SERVER_BASE}/login.php"
ALTERNATIVE_SERVER_SEARCH_NAME_URL = f"{ALTERNATIVE_SERVER_BASE}/cari_nama.php"
ALTERNATIVE_SERVER_SEARCH_NIK_URL = f"{ALTERNATIVE_SERVER_BASE}/cari_nik.php"
ALTERNATIVE_SERVER_SEARCH_MASS_NAME_URL = f"{ALTERNATIVE_SERVER_BASE}/cari_mass_nama.php"
ALTERNATIVE_SERVER_USERNAME = os.environ.get("ALTERNATIVE_SERVER_USERNAME", "ferdi")
ALTERNATIVE_SERVER_PASSWORD = os.environ.get("ALTERNATIVE_SERVER_PASSWORD", "pafer123")

# Warning cache to prevent spam
_warning_cache = {}
WARNING_COOLDOWN = 300  # 5 minutes

# Session cache for server 116 (to maintain login session)
_server_116_session = None
_server_116_session_time = 0
_server_116_session_timeout = 1800  # 30 minutes (reduced from 1 hour for better reliability)

# Session cache for alternative server (to maintain login session)
_alternative_server_session = None
_alternative_server_session_time = 0
_alternative_server_session_timeout = 1800  # 30 minutes

def _clear_server_116_session():
    """Clear server 116 session cache"""
    global _server_116_session, _server_116_session_time
    _server_116_session = None
    _server_116_session_time = 0

def _clear_alternative_server_session():
    """Clear alternative server session cache"""
    global _alternative_server_session, _alternative_server_session_time
    _alternative_server_session = None
    _alternative_server_session_time = 0

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
    
    # Check if session is still valid (by time)
    current_time = time.time()
    session_age = current_time - _server_116_session_time if _server_116_session_time > 0 else _server_116_session_timeout + 1
    
    if _server_116_session and session_age < _server_116_session_timeout:
        # Only validate session if it's been used for more than 10 minutes
        # This prevents unnecessary validation on every request while still catching expired sessions
        if session_age > 600:  # 10 minutes
            # PENTING: Validasi session dengan test request kecil untuk memastikan masih valid
            # Ini mencegah penggunaan session yang sudah expired meskipun belum mencapai timeout
            try:
                # Quick validation: try to access a lightweight endpoint
                # If session expired, this will fail and we'll get fresh session
                test_response = _server_116_session.get(SERVER_116_BASE + '/', timeout=2)
                # If we get redirected to login or get 401/403, session expired
                if test_response.status_code in [401, 403] or '/auth/login' in test_response.url:
                    print("INFO: [SERVER_116] Session expired (detected via validation), akan refresh", file=sys.stderr)
                    _clear_server_116_session()
                else:
                    print("INFO: [SERVER_116] Menggunakan session yang masih valid (validated)", file=sys.stderr)
                    return _server_116_session
            except Exception as e:
                # If validation fails, assume session expired and get fresh one
                print(f"INFO: [SERVER_116] Session validation failed ({e}), akan refresh", file=sys.stderr)
                _clear_server_116_session()
        else:
            # Session masih baru (< 10 menit), langsung gunakan tanpa validasi
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

def _search_server_116(params: dict, username=None, password=None, retry_count=0):
    """
    Search using server 116 identity API
    
    Args:
        params: Search parameters
        username: Username (ignored, for compatibility)
        password: Password (ignored, for compatibility)
        retry_count: Internal retry counter (max 1 retry to avoid infinite loop)
    """
    # Prevent infinite retry loop
    MAX_RETRY = 1
    if retry_count > MAX_RETRY:
        print(f"ERROR: [SERVER_116] Max retry ({MAX_RETRY}) tercapai, berhenti retry", file=sys.stderr)
        return None
    
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
            
            # If 401/403, likely session expired - clear and retry once
            if search_response.status_code in [401, 403]:
                print(f"INFO: [SERVER_116] Status {search_response.status_code} - kemungkinan session expired, akan retry", file=sys.stderr)
                _clear_server_116_session()
                # Retry once with fresh session
                return _search_server_116(params, username, password, retry_count + 1)
            
            return None
        
        # Check if response is HTML (login page) instead of JSON - indicates session expired
        content_type = search_response.headers.get('Content-Type', '').lower()
        response_text = search_response.text[:200].lower()
        
        is_html_response = 'text/html' in content_type or response_text.strip().startswith('<!doctype') or response_text.strip().startswith('<html')
        is_login_page = 'login' in response_text or 'auth/login' in response_text or 'username' in response_text or 'password' in response_text
        
        if is_html_response or is_login_page:
            print(f"ERROR: [SERVER_116] Response adalah HTML/login page - session expired!", file=sys.stderr)
            # Clear session dan retry dengan fresh login
            _clear_server_116_session()
            print(f"INFO: [SERVER_116] ✅ Session cleared, retry dengan fresh login", file=sys.stderr)
            # Retry once with fresh session (max 1 retry to avoid infinite loop)
            return _search_server_116(params, username, password, retry_count + 1)
        
        # Parse response
        try:
            data = search_response.json()
            print(f"INFO: [SERVER_116] Response berhasil di-parse", file=sys.stderr)
            print(f"DEBUG: [SERVER_116] Response keys: {list(data.keys())}", file=sys.stderr)
            
            # Check if response indicates session expired (some APIs return JSON error for expired session)
            if isinstance(data, dict):
                # Check for common error indicators
                error_msg = str(data.get('error', '')).lower() + str(data.get('message', '')).lower()
                if any(keyword in error_msg for keyword in ['session', 'expired', 'unauthorized', 'login', 'auth']):
                    print(f"WARNING: [SERVER_116] Response menunjukkan session expired: {data.get('error', data.get('message', ''))}", file=sys.stderr)
                    _clear_server_116_session()
                    print(f"INFO: [SERVER_116] ✅ Session cleared, retry dengan fresh login", file=sys.stderr)
                    # Retry once with fresh session
                    return _search_server_116(params, username, password, retry_count + 1)
                    
        except Exception as json_error:
            # If JSON parse fails, check if it's HTML (session expired)
            if is_html_response or is_login_page:
                print(f"ERROR: [SERVER_116] Gagal parse JSON dan response adalah HTML - session expired!", file=sys.stderr)
                _clear_server_116_session()
                print(f"INFO: [SERVER_116] ✅ Session cleared, retry dengan fresh login", file=sys.stderr)
                return _search_server_116(params, username, password, retry_count + 1)
            else:
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
    
    # Always try alternative server for comparison (even if server 116 has results)
    alternative_result = _search_alternative_server(params, username, password)
    
    # Get alternative server results
    alt_person_list = []
    alt_person_count = 0
    
    if alternative_result is not None:
        print(f"DEBUG: [CALL_SEARCH] Alternative server result type: {type(alternative_result)}", file=sys.stderr)
        print(f"DEBUG: [CALL_SEARCH] Alternative server result keys: {list(alternative_result.keys()) if isinstance(alternative_result, dict) else 'N/A'}", file=sys.stderr)
        
        if isinstance(alternative_result, dict):
            alt_person_list = alternative_result.get('person', [])
            if not isinstance(alt_person_list, list):
                alt_person_list = []
            alt_person_count = len(alt_person_list)
            print(f"DEBUG: [CALL_SEARCH] Alternative server found {alt_person_count} results", file=sys.stderr)
        else:
            print(f"DEBUG: [CALL_SEARCH] Alternative server result is not a dict: {type(alternative_result)}", file=sys.stderr)
    else:
        print(f"DEBUG: [CALL_SEARCH] Alternative server result is None", file=sys.stderr)
    
    # Check if server 116 returned results
    if server_116_result is not None:
        person_list = server_116_result.get('person', []) if isinstance(server_116_result, dict) else []
        person_count = len(person_list) if isinstance(person_list, list) else 0
        
        if person_count > 0:
            # Server 116 has results - combine with alternative server results
            warning_key = "server_116_fallback_success"
            if _should_show_warning(warning_key):
                print(f"INFO: [OK] Berhasil menggunakan server 116 sebagai fallback - ditemukan {person_count} hasil", file=sys.stderr)
                if alt_person_count > 0:
                    print(f"INFO: [ALTERNATIVE_SERVER] ✅ Juga menemukan {alt_person_count} hasil di server alternatif", file=sys.stderr)
            
            # Mark server 116 results with source
            for person in person_list:
                if isinstance(person, dict):
                    person['_source'] = 'server_116'
                    person['_server'] = '116'
            
            # Mark alternative server results with source
            for person in alt_person_list:
                if isinstance(person, dict):
                    person['_source'] = 'alternative_server'
                    person['_server'] = '154.26.138.135'
            
            # Combine results from both servers
            combined_person_list = person_list.copy()
            
            # Add alternative server results (avoid duplicates based on NIK)
            existing_niks = {p.get('ktp_number') or p.get('nik') for p in combined_person_list if isinstance(p, dict)}
            for alt_person in alt_person_list:
                if isinstance(alt_person, dict):
                    alt_nik = alt_person.get('ktp_number') or alt_person.get('nik')
                    if alt_nik and alt_nik not in existing_niks:
                        combined_person_list.append(alt_person)
                        existing_niks.add(alt_nik)
                    elif not alt_nik:
                        # If no NIK, add anyway (might be different person with same name)
                        combined_person_list.append(alt_person)
            
            total_combined = len(combined_person_list)
            
            server_116_result['_server_116_fallback'] = True
            server_116_result['_server_224_unavailable'] = True
            server_116_result['person'] = combined_person_list  # Replace with combined results
            
            # Keep alternative server info for reference
            server_116_result['_alternative_server_results'] = alt_person_list
            server_116_result['_alternative_server_count'] = alt_person_count
            server_116_result['_server_116_count'] = person_count
            server_116_result['_total_combined_count'] = total_combined
            
            if alt_person_count > 0:
                server_116_result['_alternative_server_fallback'] = True
                server_116_result['_has_comparison_data'] = True
                print(f"INFO: [CALL_SEARCH] ✅ Server 116: {person_count} hasil, Server Alternatif: {alt_person_count} hasil, Total Gabungan: {total_combined} hasil", file=sys.stderr)
            else:
                print(f"INFO: [CALL_SEARCH] Server 116: {person_count} hasil, Server Alternatif: 0 hasil, Total: {person_count} hasil", file=sys.stderr)
            
            return server_116_result
        elif isinstance(server_116_result, dict) and 'person' in server_116_result:
            # Server 116 returned empty results but was accessible
            warning_key = "server_116_fallback_empty"
            if _should_show_warning(warning_key):
                print(f"INFO: Server 116 berhasil diakses tapi tidak mengembalikan hasil (array person kosong)", file=sys.stderr)
            
            # If alternative server has results, use it as primary
            if alt_person_count > 0:
                print(f"INFO: [ALTERNATIVE_SERVER] ✅ Berhasil menemukan {alt_person_count} hasil di server alternatif", file=sys.stderr)
                
                # Mark alternative server results with source
                for person in alt_person_list:
                    if isinstance(person, dict):
                        person['_source'] = 'alternative_server'
                        person['_server'] = '154.26.138.135'
                
                alternative_result['_alternative_server_fallback'] = True
                alternative_result['_server_116_fallback'] = True
                alternative_result['_server_116_empty'] = True
                alternative_result['_server_224_unavailable'] = True
                alternative_result['_server_116_count'] = 0
                alternative_result['_alternative_server_count'] = alt_person_count
                alternative_result['_total_combined_count'] = alt_person_count
                return alternative_result
            
            # Return server 116 empty result (but still include alternative if it was tried)
            server_116_result['_server_116_fallback'] = True
            server_116_result['_server_224_unavailable'] = True
            server_116_result['_alternative_server_results'] = alt_person_list
            server_116_result['_alternative_server_count'] = alt_person_count
            server_116_result['_server_116_count'] = 0
            server_116_result['_total_combined_count'] = 0
            if alt_person_count > 0:
                server_116_result['_alternative_server_fallback'] = True
            return server_116_result
    
    # Server 116 failed or returned None - try alternative server
        warning_key = "server_116_fallback_failed"
        if _should_show_warning(warning_key):
            print("WARNING: Server 116 mengembalikan None (gagal login atau exception)", file=sys.stderr)
    print("INFO: Mencoba server alternatif sebagai fallback...", file=sys.stderr)
    
    if alternative_result is not None:
        alt_person_list = alternative_result.get('person', []) if isinstance(alternative_result, dict) else []
        alt_person_count = len(alt_person_list) if isinstance(alt_person_list, list) else 0
        
        if alt_person_count > 0:
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Berhasil menemukan {alt_person_count} hasil di server alternatif", file=sys.stderr)
            
            # Mark alternative server results with source
            for person in alt_person_list:
                if isinstance(person, dict):
                    person['_source'] = 'alternative_server'
                    person['_server'] = '154.26.138.135'
            
            alternative_result['_alternative_server_fallback'] = True
            alternative_result['_server_116_unavailable'] = True
            alternative_result['_server_224_unavailable'] = True
            alternative_result['_server_116_count'] = 0
            alternative_result['_alternative_server_count'] = alt_person_count
            alternative_result['_total_combined_count'] = alt_person_count
            return alternative_result
        elif isinstance(alternative_result, dict) and 'person' in alternative_result:
            # Alternative server returned empty results but was accessible
            print(f"INFO: [ALTERNATIVE_SERVER] Server alternatif berhasil diakses tapi tidak mengembalikan hasil", file=sys.stderr)
            alternative_result['_alternative_server_fallback'] = True
            alternative_result['_server_116_unavailable'] = True
            alternative_result['_server_224_unavailable'] = True
            alternative_result['_server_116_count'] = 0
            alternative_result['_alternative_server_count'] = 0
            alternative_result['_total_combined_count'] = 0
            return alternative_result
    
    # Both servers failed
    print("ERROR: [FALLBACK] Baik server 116 maupun server alternatif gagal", file=sys.stderr)
    
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
        "_alternative_server_unavailable": True,
        "_server_116_connection_error": is_connection_error,
        "_server_116_base": SERVER_116_BASE
    }
    
def _login_alternative_server(username=None, password=None):
    """
    Login ke server alternatif (http://154.26.138.135/000byte/)
    
    Args:
        username: Username (default: ALTERNATIVE_SERVER_USERNAME)
        password: Password (default: ALTERNATIVE_SERVER_PASSWORD)
    
    Returns:
        requests.Session object jika berhasil, None jika gagal
    """
    global _alternative_server_session, _alternative_server_session_time
    
    # Use cached session if still valid
    current_time = time.time()
    if (_alternative_server_session is not None and 
        current_time - _alternative_server_session_time < _alternative_server_session_timeout):
        print(f"INFO: [ALTERNATIVE_SERVER] Menggunakan session cache", file=sys.stderr)
        return _alternative_server_session
    
    # ALWAYS use hardcoded credentials for alternative server (ignore provided username/password)
    # Server alternatif memiliki kredensial sendiri yang berbeda dari server lain
    use_username = ALTERNATIVE_SERVER_USERNAME  # Always use 'ferdi'
    use_password = ALTERNATIVE_SERVER_PASSWORD  # Always use 'pafer123'
    
    print(f"INFO: [ALTERNATIVE_SERVER] ⚠️ PENTING: Menggunakan kredensial hardcoded untuk server alternatif: {use_username}/***", file=sys.stderr)
    print(f"INFO: [ALTERNATIVE_SERVER] ⚠️ Kredensial dari parameter (username={username}) TIDAK digunakan untuk server alternatif", file=sys.stderr)
    
    try:
        session = requests.Session()
        
        # Get login page first to get any CSRF token or session cookie
        login_page = session.get(ALTERNATIVE_SERVER_LOGIN_URL, timeout=10)
        if login_page.status_code != 200:
            print(f"ERROR: [ALTERNATIVE_SERVER] Gagal mengakses halaman login: {login_page.status_code}", file=sys.stderr)
            return None
        
        # Try to extract form fields from HTML (in case there are hidden fields)
        login_html = login_page.text
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login page HTML preview: {login_html[:1000]}", file=sys.stderr)
        
        # Look for form action URL
        form_action_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', login_html, re.IGNORECASE)
        form_action = form_action_match.group(1) if form_action_match else ALTERNATIVE_SERVER_LOGIN_URL
        if not form_action.startswith('http'):
            # Relative URL - make it absolute
            if form_action.startswith('/'):
                form_action = ALTERNATIVE_SERVER_BASE.rstrip('/') + form_action
            else:
                form_action = ALTERNATIVE_SERVER_LOGIN_URL.rsplit('/', 1)[0] + '/' + form_action
        print(f"DEBUG: [ALTERNATIVE_SERVER] Form action: {form_action}", file=sys.stderr)
        
        # Look for form field names in HTML
        username_fields = []
        password_fields = []
        
        # Find all input fields
        input_pattern = r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>'
        inputs = re.findall(input_pattern, login_html, re.IGNORECASE)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Found input fields: {inputs}", file=sys.stderr)
        
        for field in inputs:
            field_lower = field.lower()
            if 'user' in field_lower or 'login' in field_lower:
                username_fields.append(field)
            elif 'pass' in field_lower:
                password_fields.append(field)
        
        # Use found fields or defaults
        username_field = username_fields[0] if username_fields else 'username'
        password_field = password_fields[0] if password_fields else 'password'
        
        print(f"DEBUG: [ALTERNATIVE_SERVER] Using username field: {username_field}, password field: {password_field}", file=sys.stderr)
        
        # Prepare login data - use the found field names
        login_data = {
            username_field: use_username,
            password_field: use_password
        }
        
        # Also add common variations as backup
        if username_field != 'username':
            login_data['username'] = use_username
        if password_field != 'password':
            login_data['password'] = use_password
        
        print(f"INFO: [ALTERNATIVE_SERVER] Mengirim request login dengan username: {use_username}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login data fields: {list(login_data.keys())}", file=sys.stderr)
        
        # Perform login - use form action if found, otherwise use login URL
        login_post_url = form_action if form_action_match else ALTERNATIVE_SERVER_LOGIN_URL
        print(f"DEBUG: [ALTERNATIVE_SERVER] POST URL: {login_post_url}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login data: {list(login_data.keys())}", file=sys.stderr)
        
        # Perform login
        login_response = session.post(login_post_url,
                                     data=login_data,
                                     headers={
                                         'Content-Type': 'application/x-www-form-urlencoded',
                                         'Referer': ALTERNATIVE_SERVER_LOGIN_URL,
                                         'Origin': ALTERNATIVE_SERVER_BASE.rstrip('/'),
                                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                     },
                                     timeout=10,
                                     allow_redirects=True)
        
        if login_response.status_code != 200:
            print(f"ERROR: [ALTERNATIVE_SERVER] Gagal login: {login_response.status_code}", file=sys.stderr)
            return None
        
        # Check if login was successful
        # Check redirect location or response content
        final_url = login_response.url
        response_text = login_response.text.lower()
        response_status = login_response.status_code
        
        # Check cookies - if session cookie is set, login likely succeeded
        cookies = session.cookies.get_dict()
        has_session_cookie = len(cookies) > 0
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login response status: {response_status}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login response URL: {final_url}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Cookies after login: {list(cookies.keys()) if cookies else 'None'}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Login response preview: {response_text[:500]}", file=sys.stderr)
        
        # Check if still on login page with form visible - indicates failure
        is_still_on_login = (
            'login.php' in final_url.lower() and 
            ('username' in response_text or 'password' in response_text or 'login' in response_text)
        )
        
        if is_still_on_login:
            # Still on login page - login failed
            print(f"ERROR: [ALTERNATIVE_SERVER] ❌ Login gagal - masih di halaman login", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Response URL: {final_url}", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Full response text (first 1000 chars): {login_response.text[:1000]}", file=sys.stderr)
            
            # Try to find error message in response
            error_patterns = [
                r'error["\']?\s*:?\s*([^<]+)',
                r'gagal["\']?\s*:?\s*([^<]+)',
                r'invalid["\']?\s*:?\s*([^<]+)',
                r'wrong["\']?\s*:?\s*([^<]+)',
            ]
            for pattern in error_patterns:
                error_match = re.search(pattern, response_text, re.IGNORECASE)
                if error_match:
                    print(f"DEBUG: [ALTERNATIVE_SERVER] Error message found: {error_match.group(1)}", file=sys.stderr)
                    break
            
            return None
        
        # Check if redirected away from login page (success indicator)
        if 'login.php' not in final_url.lower():
            # Redirected away from login - likely successful
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Login berhasil - redirected ke: {final_url}", file=sys.stderr)
        elif 'index.php' in final_url.lower() or 'dashboard' in final_url.lower() or 'home' in final_url.lower():
            # Redirected to main page - definitely successful
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Login berhasil - redirected ke halaman utama: {final_url}", file=sys.stderr)
        elif has_session_cookie:
            # Has session cookie even if still on login.php - might be successful
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Login mungkin berhasil - session cookie ditemukan", file=sys.stderr)
        else:
            # Not sure - check for error messages
            if 'error' in response_text or 'gagal' in response_text or 'invalid' in response_text or 'wrong' in response_text:
                print(f"ERROR: [ALTERNATIVE_SERVER] ❌ Login gagal - error message ditemukan dalam response", file=sys.stderr)
                print(f"DEBUG: [ALTERNATIVE_SERVER] Response preview: {response_text[:500]}", file=sys.stderr)
                return None
        
        # Verify session by trying to access a protected page (search page)
        # This ensures the session is actually valid
        print(f"INFO: [ALTERNATIVE_SERVER] Memverifikasi session dengan mengakses halaman pencarian...", file=sys.stderr)
        try:
            # Try accessing search page with empty query to verify session
            verify_url = ALTERNATIVE_SERVER_SEARCH_NAME_URL
            verify_response = session.get(verify_url, params={'nama_lengkap': ''}, timeout=10, allow_redirects=True)
            verify_url_final = verify_response.url
            verify_text = verify_response.text.lower()[:200]
            
            # If redirected to login, session is invalid
            if 'login.php' in verify_url_final.lower() or ('login' in verify_text and 'username' in verify_text):
                print(f"ERROR: [ALTERNATIVE_SERVER] ❌ Session tidak valid - di-redirect ke login", file=sys.stderr)
                return None
            
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Session verified - dapat mengakses halaman pencarian", file=sys.stderr)
        except Exception as verify_e:
            print(f"WARNING: [ALTERNATIVE_SERVER] ⚠️ Gagal verifikasi session: {verify_e}, tapi akan lanjutkan", file=sys.stderr)
        
        # Save session for future use
        _alternative_server_session = session
        _alternative_server_session_time = current_time
        
        print(f"INFO: [ALTERNATIVE_SERVER] ✅ Login berhasil dan session disimpan untuk username: {use_username}", file=sys.stderr)
        return session
        
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: [ALTERNATIVE_SERVER] Tidak dapat terhubung ke server alternatif", file=sys.stderr)
        _clear_alternative_server_session()
        return None
    except requests.exceptions.Timeout as e:
        print(f"ERROR: [ALTERNATIVE_SERVER] Timeout saat mengakses server alternatif", file=sys.stderr)
        _clear_alternative_server_session()
        return None
    except Exception as e:
        print(f"ERROR: [ALTERNATIVE_SERVER] Exception saat login: {e}", file=sys.stderr)
        _clear_alternative_server_session()
        return None

def _normalize_person_data(person_data: dict) -> dict:
    """
    Normalize person data from alternative server to match server 116 format
    
    Args:
        person_data: Raw person data from alternative server
        
    Returns:
        Normalized person data with consistent field names
    """
    normalized = {}
    
    # Map common field variations to standard field names
    field_mapping = {
        # Identity fields
        'ktp_number': ['ktp_number', 'nik', 'nomor_nik', 'no_nik'],
        'nik': ['ktp_number', 'nik', 'nomor_nik', 'no_nik'],
        'full_name': ['full_name', 'name', 'nama', 'nama_lengkap'],
        'name': ['full_name', 'name', 'nama', 'nama_lengkap'],
        'address': ['address', 'alamat', 'alamat_lengkap'],
        'birth_place': ['birth_place', 'tempat_lahir', 'tempat_lahir'],
        'date_of_birth': ['date_of_birth', 'tanggal_lahir', 'tgl_lahir'],
        'occupation': ['occupation', 'pekerjaan', 'jenis_pekerjaan'],
        'marital_status': ['marital_status', 'status_kawin', 'status_perkawinan'],
        'family_status': ['family_status', 'status_hubungan_keluarga'],
        'family_cert_number': ['family_cert_number', 'nomor_kk', 'no_kk', 'nkk'],
        'father_name': ['father_name', 'nama_ayah', 'nama_lengkap_ayah'],
        'father_nik_number': ['father_nik_number', 'nik_ayah'],
        'mother_name': ['mother_name', 'nama_ibu', 'nama_lengkap_ibu'],
        'mother_nik_number': ['mother_nik_number', 'nik_ibu'],
    }
    
    # Extract values using field mapping
    for standard_field, variations in field_mapping.items():
        for variation in variations:
            if variation in person_data and person_data[variation]:
                normalized[standard_field] = person_data[variation]
                break
    
    # Ensure required fields exist (use N/A as default)
    if 'ktp_number' not in normalized:
        normalized['ktp_number'] = normalized.get('nik', 'N/A')
    if 'nik' not in normalized:
        normalized['nik'] = normalized.get('ktp_number', 'N/A')
    if 'full_name' not in normalized:
        normalized['full_name'] = normalized.get('name', 'N/A')
    if 'name' not in normalized:
        normalized['name'] = normalized.get('full_name', 'N/A')
    
    # Copy any additional fields that don't need normalization
    for key, value in person_data.items():
        if key not in normalized and value:
            normalized[key] = value
    
    return normalized

def _search_alternative_server(params: dict, username=None, password=None, retry_count=0):
    """
    Search menggunakan server alternatif (http://154.26.138.135/000byte/)
    
    Args:
        params: Search parameters (name, nik, etc.)
        username: Username (ignored, for compatibility)
        password: Password (ignored, for compatibility)
        retry_count: Internal retry counter (max 1 retry)
    
    Returns:
        dict dengan format {"person": [...]} atau None jika gagal
    """
    # Prevent infinite retry loop
    MAX_RETRY = 1
    if retry_count > MAX_RETRY:
        print(f"ERROR: [ALTERNATIVE_SERVER] Max retry ({MAX_RETRY}) tercapai", file=sys.stderr)
        return None
    
    session = _login_alternative_server(username, password)
    if not session:
        print("ERROR: [ALTERNATIVE_SERVER] Tidak dapat login ke server alternatif", file=sys.stderr)
        return None
    
    try:
        from urllib.parse import urlencode
        
        search_url = None
        search_params = {}
        
        # Determine which endpoint to use based on params
        if params.get('name'):
            search_url = ALTERNATIVE_SERVER_SEARCH_NAME_URL
            search_params['nama_lengkap'] = params['name']
            print(f"INFO: [ALTERNATIVE_SERVER] Mencari dengan nama: {params['name']}", file=sys.stderr)
        elif params.get('nik'):
            search_url = ALTERNATIVE_SERVER_SEARCH_NIK_URL
            search_params['nomor_nik'] = params['nik']
            print(f"INFO: [ALTERNATIVE_SERVER] Mencari dengan NIK: {params['nik']}", file=sys.stderr)
        else:
            print("ERROR: [ALTERNATIVE_SERVER] Tidak ada parameter pencarian yang valid (name atau nik)", file=sys.stderr)
            return None
        
        if not search_url:
            print("ERROR: [ALTERNATIVE_SERVER] URL pencarian tidak ditentukan", file=sys.stderr)
            return None
        
        full_url = f"{search_url}?{urlencode(search_params)}" if search_params else search_url
        print(f"INFO: [ALTERNATIVE_SERVER] URL pencarian lengkap: {full_url}", file=sys.stderr)
        print(f"INFO: [ALTERNATIVE_SERVER] Parameter: {search_params}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Session cookies sebelum pencarian: {list(session.cookies.get_dict().keys())}", file=sys.stderr)
        
        # Perform search with proper headers to maintain session
        search_response = session.get(
            search_url, 
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
        
        print(f"INFO: [ALTERNATIVE_SERVER] Response status: {search_response.status_code}", file=sys.stderr)
        print(f"INFO: [ALTERNATIVE_SERVER] Response URL: {search_response.url}", file=sys.stderr)
        print(f"INFO: [ALTERNATIVE_SERVER] Response Content-Type: {search_response.headers.get('Content-Type', 'N/A')}", file=sys.stderr)
        print(f"INFO: [ALTERNATIVE_SERVER] Response length: {len(search_response.text)} chars", file=sys.stderr)
        
        if search_response.status_code != 200:
            print(f"ERROR: [ALTERNATIVE_SERVER] Gagal melakukan pencarian: {search_response.status_code}", file=sys.stderr)
            print(f"ERROR: [ALTERNATIVE_SERVER] Response text: {search_response.text[:500]}", file=sys.stderr)
            
            # If 401/403, likely session expired - clear and retry once
            if search_response.status_code in [401, 403]:
                print(f"INFO: [ALTERNATIVE_SERVER] Status {search_response.status_code} - kemungkinan session expired, akan retry", file=sys.stderr)
                _clear_alternative_server_session()
                return _search_alternative_server(params, username, password, retry_count + 1)
            
            return None
        
        # Check if response is actually a login page (not just HTML)
        # Server alternatif SELALU mengembalikan HTML, jadi kita perlu cek lebih spesifik
        content_type = search_response.headers.get('Content-Type', '').lower()
        response_url = search_response.url.lower()
        response_text = search_response.text.lower()
        
        # Check if redirected to login page
        is_redirected_to_login = 'login.php' in response_url
        
        # Check if response contains login form (more specific check)
        has_login_form = (
            'login' in response_text[:500] and 
            'username' in response_text[:500] and 
            'password' in response_text[:500] and
            'form' in response_text[:500]
        )
        
        # Check if response contains search results (indicates valid session)
        has_result_item = 'result-item' in response_text or 'cari' in response_url or 'search' in response_text[:500]
        has_cari_nama = 'cari_nama' in response_url or 'cari_nik' in response_url
        
        # Debug logging
        print(f"DEBUG: [ALTERNATIVE_SERVER] Session check - URL: {response_url}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Is redirected to login: {is_redirected_to_login}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Has login form: {has_login_form}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Has result-item: {has_result_item}", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Has cari_nama/nik in URL: {has_cari_nama}", file=sys.stderr)
        
        # Only treat as login page if:
        # 1. Redirected to login.php, OR
        # 2. Contains login form AND does NOT contain search results AND not on search page
        is_actually_login_page = is_redirected_to_login or (has_login_form and not has_result_item and not has_cari_nama)
        
        if is_actually_login_page:
            print(f"ERROR: [ALTERNATIVE_SERVER] Response adalah login page - session expired!", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Response URL: {response_url}", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Has login form: {has_login_form}, Has result item: {has_result_item}, Has cari: {has_cari_nama}", file=sys.stderr)
            _clear_alternative_server_session()
            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Session cleared, retry dengan fresh login", file=sys.stderr)
            return _search_alternative_server(params, username, password, retry_count + 1)
        
        # If response is HTML but not login page, it's normal (server alternatif always returns HTML)
        if 'text/html' in content_type:
            print(f"INFO: [ALTERNATIVE_SERVER] Response adalah HTML (normal untuk server alternatif), akan parse HTML", file=sys.stderr)
        
        # Try to parse as JSON first
        try:
            data = search_response.json()
            print(f"INFO: [ALTERNATIVE_SERVER] Response berhasil di-parse sebagai JSON", file=sys.stderr)
            
            # Convert to standard format
            if isinstance(data, dict):
                # Check if it has person field
                if 'person' in data:
                    person_list = data['person']
                    if isinstance(person_list, list):
                        print(f"INFO: [ALTERNATIVE_SERVER] Ditemukan {len(person_list)} hasil", file=sys.stderr)
                        return {"person": person_list}
                
                # Check if it has results field (alternative format)
                if 'results' in data:
                    results = data['results']
                    if isinstance(results, list):
                        print(f"INFO: [ALTERNATIVE_SERVER] Ditemukan {len(results)} hasil (format results)", file=sys.stderr)
                        return {"person": results}
                
                # If data itself is a list, treat as person list
                if isinstance(data, list):
                    print(f"INFO: [ALTERNATIVE_SERVER] Response adalah list, ditemukan {len(data)} hasil", file=sys.stderr)
                    return {"person": data}
            
            # If we get here, try to extract person data from HTML response
            print(f"WARNING: [ALTERNATIVE_SERVER] Format response tidak dikenali, mencoba parse HTML", file=sys.stderr)
            
        except ValueError:
            # Not JSON, try to parse HTML
            print(f"INFO: [ALTERNATIVE_SERVER] Response bukan JSON, mencoba parse HTML", file=sys.stderr)
        
        # Try to parse HTML response (server alternatif mungkin mengembalikan HTML)
        # This is a basic parser - you may need to adjust based on actual HTML structure
        html_content = search_response.text
        person_list = []
        
        print(f"DEBUG: [ALTERNATIVE_SERVER] Response length: {len(html_content)} chars", file=sys.stderr)
        print(f"DEBUG: [ALTERNATIVE_SERVER] Response preview (first 1000 chars): {html_content[:1000]}", file=sys.stderr)
        
        # Simple HTML parsing - look for table rows or JSON data in script tags
        # Try to find JSON in script tags (more comprehensive pattern)
        json_patterns = [
            r'<script[^>]*>.*?(\{.*?\}).*?</script>',  # Basic JSON in script
            r'var\s+data\s*=\s*(\{.*?\});',  # var data = {...};
            r'const\s+data\s*=\s*(\{.*?\});',  # const data = {...};
            r'let\s+data\s*=\s*(\{.*?\});',  # let data = {...};
            r'data\s*:\s*(\{.*?\})',  # data: {...}
            r'(\[.*?\])',  # Array JSON
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
            if json_match:
                try:
                    json_str = json_match.group(1)
                    json_data = json.loads(json_str)
                    print(f"DEBUG: [ALTERNATIVE_SERVER] Found JSON in script tag with pattern: {pattern[:30]}...", file=sys.stderr)
                    if isinstance(json_data, list):
                        person_list = json_data
                        print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted {len(person_list)} results from JSON array", file=sys.stderr)
                        break
                    elif isinstance(json_data, dict):
                        if 'person' in json_data:
                            person_list = json_data['person']
                            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted {len(person_list)} results from JSON.person", file=sys.stderr)
                            break
                        elif 'data' in json_data:
                            person_list = json_data['data']
                            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted {len(person_list)} results from JSON.data", file=sys.stderr)
                            break
                        elif 'results' in json_data:
                            person_list = json_data['results']
                            print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted {len(person_list)} results from JSON.results", file=sys.stderr)
                            break
                except Exception as e:
                    print(f"DEBUG: [ALTERNATIVE_SERVER] Failed to parse JSON from script: {e}", file=sys.stderr)
                    continue
        
        # If no JSON found, try to extract from HTML result-item divs (format server alternatif)
        if not person_list:
            print(f"INFO: [ALTERNATIVE_SERVER] Mencoba parse HTML result-item divs...", file=sys.stderr)
            
            # Look for result-item divs (format: <div class="result-item">...)
            result_item_pattern = r'<div[^>]*class=["\']result-item["\'][^>]*>(.*?)</div>'
            result_items = re.findall(result_item_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if result_items:
                print(f"INFO: [ALTERNATIVE_SERVER] Ditemukan {len(result_items)} result-item divs", file=sys.stderr)
                
                for item_html in result_items:
                    person_data = {}
                    
                    # Extract data using pattern: <strong>LABEL:</strong> VALUE<br>
                    # Map labels to person_data fields
                    label_mapping = {
                        'nama lengkap': 'full_name',
                        'nomor nik': 'ktp_number',
                        'nomor kk': 'family_cert_number',
                        'alamat lengkap': 'address',
                        'tempat lahir': 'birth_place',
                        'tanggal lahir': 'date_of_birth',
                        'jenis pekerjaan': 'occupation',
                        'status kawin': 'marital_status',
                        'status hubungan keluarga': 'family_status',
                        'nama lengkap ayah': 'father_name',
                        'nik ayah': 'father_nik_number',
                        'nama lengkap ibu': 'mother_name',
                        'nik ibu': 'mother_nik_number',
                    }
                    
                    # Pattern: <strong>LABEL:</strong> VALUE<br> or <strong>LABEL:</strong> VALUE
                    # Improved pattern to handle values that may contain HTML tags
                    field_pattern = r'<strong[^>]*>([^<]+?):</strong>\s*(.*?)(?:<br\s*/?>|</strong>|</div>|$)'
                    fields = re.findall(field_pattern, item_html, re.IGNORECASE | re.DOTALL)
                    
                    for label, value in fields:
                        label_clean = label.strip().lower()
                        value_clean = re.sub(r'<[^>]+>', '', value).strip()  # Remove any remaining HTML tags
                        
                        # Map label to field name
                        field_name = label_mapping.get(label_clean)
                        if field_name:
                            person_data[field_name] = value_clean
                        else:
                            # Store with original label as key (lowercase, spaces to underscores)
                            alt_field = label_clean.replace(' ', '_')
                            person_data[alt_field] = value_clean
                    
                    # Ensure required fields exist
                    if 'ktp_number' in person_data:
                        person_data['nik'] = person_data['ktp_number']
                    if 'full_name' in person_data:
                        person_data['name'] = person_data['full_name']
                    
                    # Only add if we have at least NIK or name
                    if person_data.get('ktp_number') or person_data.get('full_name'):
                        # Normalize data format to match server 116 format
                        normalized_data = _normalize_person_data(person_data)
                        person_list.append(normalized_data)
                        print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted from result-item: {normalized_data.get('full_name', 'N/A')} - NIK: {normalized_data.get('ktp_number', 'N/A')}", file=sys.stderr)
            
            # If still no data, try to extract from HTML table
            if not person_list:
                print(f"INFO: [ALTERNATIVE_SERVER] Mencoba parse HTML table...", file=sys.stderr)
                
                # Try to find table with data
                # Look for table rows (tr) that contain data
                table_pattern = r'<table[^>]*>(.*?)</table>'
                table_match = re.search(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
                
                if table_match:
                    table_content = table_match.group(1)
                    # Find all table rows
                    row_pattern = r'<tr[^>]*>(.*?)</tr>'
                    rows = re.findall(row_pattern, table_content, re.DOTALL | re.IGNORECASE)
                    
                    print(f"INFO: [ALTERNATIVE_SERVER] Ditemukan {len(rows)} baris dalam tabel", file=sys.stderr)
                    
                    # Skip header row (first row usually contains headers)
                    for i, row in enumerate(rows[1:] if len(rows) > 1 else rows):
                        # Extract table cells (td)
                        cell_pattern = r'<td[^>]*>(.*?)</td>'
                        cells = re.findall(cell_pattern, row, re.DOTALL | re.IGNORECASE)
                        
                        if len(cells) >= 2:  # At least 2 cells (name and NIK)
                            # Clean HTML tags from cells
                            def clean_html(text):
                                # Remove HTML tags
                                text = re.sub(r'<[^>]+>', '', text)
                                # Clean whitespace
                                text = ' '.join(text.split())
                                return text.strip()
                            
                            # Try to extract person data from cells
                            # Common structure: [NIK, Name, Address, etc.]
                            person_data = {}
                            
                            # Try to identify NIK (usually 16 digits or first cell)
                            for cell in cells:
                                cell_text = clean_html(cell)
                                # Check if it looks like NIK (16 digits)
                                if re.match(r'^\d{16}$', cell_text):
                                    person_data['ktp_number'] = cell_text
                                    person_data['nik'] = cell_text
                                # Check if it looks like a name (has letters and spaces)
                                elif re.match(r'^[A-Za-z\s]+$', cell_text) and len(cell_text) > 3:
                                    if 'full_name' not in person_data and 'name' not in person_data:
                                        person_data['full_name'] = cell_text
                                        person_data['name'] = cell_text
                                # Check if it looks like address
                                elif 'alamat' in cell_text.lower() or 'address' in cell_text.lower() or len(cell_text) > 20:
                                    person_data['address'] = cell_text
                                    person_data['alamat'] = cell_text
                            
                            # If we found at least NIK or name, add to list
                            if person_data.get('ktp_number') or person_data.get('full_name'):
                                # Normalize data format to match server 116 format
                                normalized_data = _normalize_person_data(person_data)
                                person_list.append(normalized_data)
                                print(f"INFO: [ALTERNATIVE_SERVER] ✅ Extracted person: {normalized_data.get('full_name', 'N/A')} - NIK: {normalized_data.get('ktp_number', 'N/A')}", file=sys.stderr)
            
            # If still no data, try to find any data in divs or other structures
            if not person_list:
                # Look for common data patterns in HTML
                # Try to find NIK pattern (16 digits)
                nik_pattern = r'\b\d{16}\b'
                niks = re.findall(nik_pattern, html_content)
                
                # Try to find names (capitalized words)
                name_pattern = r'<[^>]*>([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)</[^>]*>'
                names = re.findall(name_pattern, html_content)
                
                if niks and names:
                    # Match NIKs with names (simple pairing)
                    for i, nik in enumerate(niks[:len(names)]):
                        if i < len(names):
                            person_data = {
                                'ktp_number': nik,
                                'nik': nik,
                                'full_name': names[i],
                                'name': names[i]
                            }
                            # Normalize data format to match server 116 format
                            normalized_data = _normalize_person_data(person_data)
                            person_list.append(normalized_data)
                            print(f"INFO: [ALTERNATIVE_SERVER] Extracted from patterns: {normalized_data.get('full_name', 'N/A')} - NIK: {normalized_data.get('ktp_number', 'N/A')}", file=sys.stderr)
        
        # If still no data found, log the response for debugging
        if not person_list:
            print(f"WARNING: [ALTERNATIVE_SERVER] Tidak dapat parse HTML response, mengembalikan empty result", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Response preview (first 1000 chars): {html_content[:1000]}", file=sys.stderr)
            print(f"DEBUG: [ALTERNATIVE_SERVER] Response length: {len(html_content)} chars", file=sys.stderr)
            # Save full response to file for debugging (optional)
            try:
                import os
                debug_dir = os.path.join(os.path.dirname(__file__), 'debug')
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f'alternative_server_response_{int(time.time())}.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"DEBUG: [ALTERNATIVE_SERVER] Full response saved to: {debug_file}", file=sys.stderr)
            except Exception as e:
                print(f"DEBUG: [ALTERNATIVE_SERVER] Could not save debug file: {e}", file=sys.stderr)
            
            return {"person": []}
        
        print(f"INFO: [ALTERNATIVE_SERVER] ✅ Berhasil extract {len(person_list)} hasil dari HTML", file=sys.stderr)
        return {"person": person_list}
        
    except Exception as e:
        print(f"WARNING: [ALTERNATIVE_SERVER] Exception saat pencarian: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None

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
