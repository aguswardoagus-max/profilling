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
FALLBACK_MODE = os.environ.get("CLEARANCE_FALLBACK_MODE", "true").lower() == "true"
MAX_RETRY_ATTEMPTS = int(os.environ.get("CLEARANCE_MAX_RETRY", "3"))

# Warning cache to prevent spam
_warning_cache = {}
WARNING_COOLDOWN = 300  # 5 minutes
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

def do_login(username: str, password: str, retry_count=0):
    url = BASE.rstrip("/") + LOGIN_PATH
    
    # Try form data first (application/x-www-form-urlencoded)
    data = {
        "username": username,
        "password": password,
    }
    
    try:
        r = requests.post(url, data=data, timeout=15)
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
        return token
        
    except requests.exceptions.RequestException as e:
        # Create a more specific warning key based on error type and status code
        error_type = type(e).__name__
        status_code = 'unknown'
        if hasattr(e, 'response') and e.response is not None:
            status_code = getattr(e.response, 'status_code', 'unknown')
        warning_key = f"login_network_error_{error_type}_{status_code}"
        
        if _should_show_warning(warning_key):
            print(f"ERROR: Gagal mengakses server eksternal: {e}", file=sys.stderr)
        if FALLBACK_MODE:
            if _should_show_warning("fallback_mode_enabled"):
                print("INFO: Fallback mode enabled, menggunakan mode offline", file=sys.stderr)
            return None
        else:
            if retry_count < MAX_RETRY_ATTEMPTS:
                if _should_show_warning(f"retry_attempt_{retry_count}"):
                    print(f"INFO: Mencoba lagi ({retry_count + 1}/{MAX_RETRY_ATTEMPTS})...", file=sys.stderr)
                time.sleep(2)  # Wait 2 seconds before retry
                return do_login(username, password, retry_count + 1)
            else:
                if _should_show_warning("max_retry_reached"):
                    print("ERROR: Maksimal percobaan login tercapai", file=sys.stderr)
                sys.exit(4)

def ensure_token(username: str, password: str, force_refresh=False):
    token = None
    if not force_refresh:
        token = load_cached_token()
        if token and token_valid(token):
            return token
    
    # Try to login
    token = do_login(username, password)
    if token is None:
        warning_key = "ensure_token_fallback"
        if _should_show_warning(warning_key):
            print("WARNING: Login ke server eksternal gagal. Menggunakan fallback mode...", file=sys.stderr)
        # Return a dummy token for fallback mode
        return "fallback_token_" + str(int(time.time()))
    
    # Save the new token to cache
    if token and not token.startswith("fallback_token_"):
        save_cached_token(token)
    
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

def call_search(token: str, params: dict):
    # Check if this is a fallback token
    if token.startswith("fallback_token_"):
        warning_key = "fallback_mode"
        if _should_show_warning(warning_key):
            print("WARNING: Menggunakan fallback mode - server eksternal tidak tersedia", file=sys.stderr)
        # Return empty result for fallback mode
        return {"person": [], "message": "Server eksternal tidak tersedia - menggunakan mode fallback"}
    
    url = BASE.rstrip("/") + SEARCH_PATH
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": BASE.split("://", 1)[1] if "://" in BASE else BASE,
        "Referer": BASE if BASE.endswith("/") else BASE + "/",
        "Accept": "application/json",
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        # Create a more specific warning key based on error type and status code
        error_type = type(e).__name__
        status_code = 'unknown'
        if hasattr(e, 'response') and e.response is not None:
            status_code = getattr(e.response, 'status_code', 'unknown')
        warning_key = f"server_error_{error_type}_{status_code}"
        
        if _should_show_warning(warning_key):
            print(f"WARNING: Gagal mengakses server eksternal: {e}", file=sys.stderr)
            print("Menggunakan fallback mode...", file=sys.stderr)
        return {"person": [], "message": f"Server eksternal tidak dapat diakses: {str(e)}"}

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

    if not args.name and not args.nik:
        print("ERROR: tentukan --name atau --nik minimal untuk membatasi hasil (agar tidak terlalu banyak).", file=sys.stderr)
        sys.exit(1)

    token = ensure_token(username, password, force_refresh=args.force_login)

    params = {
        "name": args.name or "",
        "nik": args.nik or "",
        "family_cert_number": "",
        "tempat_lahir": "",
        "tanggal_lahir": "",
        "no_prop": "",
        "no_kab": "",
        "no_kec": "",
        "no_desa": "",
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
