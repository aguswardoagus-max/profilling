from flask import Blueprint, render_template, request, session, flash, redirect, url_for
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta, timezone
import mysql.connector
from mysql.connector import Error
import logging
import json
import os
from flask_cors import CORS

# Konfigurasi logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inisialisasi blueprint
cekplat_bp = Blueprint('cekplat', __name__, template_folder='templates')
CORS(cekplat_bp, supports_credentials=True)

def get_current_time():
    return datetime.now(timezone.utc)

def fetch_data(no_polisi):
    url = f"http://www.jambisamsat.net/infopkb.php?no_polisi={no_polisi}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
    return None

def extract_data_from_comment(html_content):
    data = []
    comment_pattern = r'<!--\s*(.*?)\s*-->'
    comment_matches = re.finditer(comment_pattern, html_content, re.DOTALL)
    for comment_match in comment_matches:
        comment_content = comment_match.group(1)
        soup = BeautifulSoup(comment_content, 'html.parser')
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) >= 3:
                label = tds[0].get_text(strip=True)
                value = tds[2].get_text(strip=True)
                if label and value:
                    data.append((label, value))
    return data

def preprocess_address(address):
    address = address.strip()
    address = re.sub(r'^\s*ALAMAT\s*:\s*', '', address, flags=re.IGNORECASE)
    replacements = {
        r'\bJL\.?\b': 'Jalan',
        r'\bNO\.?\b': 'No',
        r'\bKEL\.?\b': 'Kelurahan ',
        r'\bKEC\.?\b': 'Kecamatan ',
        r'\bKOTA\b': 'Kota',
        r'(\b[Kk][Ee][Ll][Uu][Rr][Aa][Hh][Aa][Nn]\b)(\w+)': r'\1 \2',
        r'(\b[Kk][Ee][Cc][Aa][Mm][Aa][Tt][Aa][Nn]\b)(\w+)': r'\1 \2',
        r'\s+': ' ',
        r'\bRT\.?\d+\b': '',
        r'\s*-\s*': ' ',
    }
    for pattern, replacement in replacements.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    return address.strip()

def geocode_address(address):
    url = 'https://nominatim.openstreetmap.org/search'
    headers = {'User-Agent': 'cekplat-app/1.0 (drakentv8@gmail.com)'}
    processed_address = preprocess_address(address)
    road_match = re.search(r'Jalan\s+[\w\s.]+?(?=\sNo|\sKelurahan|$)', processed_address, re.IGNORECASE)
    kelurahan_match = re.search(r'Kelurahan\s+[\w\s.]+?(?=\sKecamatan|$)', processed_address, re.IGNORECASE)
    kecamatan_match = re.search(r'Kecamatan\s+[\w\s.]+?(?=\sKota|$)', processed_address, re.IGNORECASE)
    kota_match = re.search(r'Kota\s+[\w\s.]+?(?=$)', processed_address, re.IGNORECASE)
    road = road_match.group(0) if road_match else ''
    kelurahan = kelurahan_match.group(0) if kelurahan_match else ''
    kecamatan = kecamatan_match.group(0) if kecamatan_match else ''
    kota = kota_match.group(0) if kota_match else 'Kota Jambi'
    attempts = [
        f"{road}, {kelurahan}, {kecamatan}, {kota}, Indonesia" if road and kelurahan and kecamatan else "",
        f"{road}, {kecamatan}, {kota}, Indonesia" if road and kecamatan else "",
        f"{kelurahan}, {kecamatan}, {kota}, Indonesia" if kelurahan and kecamatan else "",
        f"{road}, {kelurahan}, {kota}, Indonesia" if road and kelurahan else "",
        f"{kecamatan}, {kota}, Indonesia" if kecamatan else "",
        f"{kelurahan}, {kota}, Indonesia" if kelurahan else "",
        f"{kota}, Indonesia",
        "Kota Jambi, Indonesia"
    ]
    attempts = [attempt for attempt in attempts if attempt]
    accuracy_score = 0.0
    accuracy_details = []
    lat, lon, display_name = None, None, ""
    for attempt_address in attempts:
        params = {
            'q': attempt_address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
            'countrycodes': 'ID'
        }
        try:
            time.sleep(1)
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                results = response.json()
                if results:
                    lat = float(results[0]['lat'])
                    lon = float(results[0]['lon'])
                    address_details = results[0].get('address', {})
                    display_name = results[0].get('display_name', '')
                    city = address_details.get('city', '').lower() or address_details.get('state', '').lower()
                    suburb = address_details.get('suburb', '').lower()
                    if 'jambi' in city:
                        required_fields = ['city', 'country']
                        present_fields = [field for field in required_fields if field in address_details]
                        completeness_score = len(present_fields) / len(required_fields) * 50
                        accuracy_score += completeness_score
                        accuracy_details.append(f"Kelengkapan: {completeness_score:.1f}% (Ditemukan {len(present_fields)}/{len(required_fields)} bidang)")
                        match_score = 0
                        if kelurahan and kelurahan.lower() in suburb:
                            match_score += 30
                        if kecamatan and kecamatan.lower() in suburb:
                            match_score += 30
                        if road and road.lower() in address_details.get('road', '').lower():
                            match_score += 20
                        accuracy_score += match_score
                        accuracy_details.append(f"Pencocokan Komponen: {match_score}% (Kelurahan: {kelurahan}, Kecamatan: {kecamatan}, Jalan: {road})")
                        importance = results[0].get('importance', 0.0)
                        importance_score = min(importance * 20, 20)
                        accuracy_score += importance_score
                        accuracy_details.append(f"Pentingnya Nominatim: {importance_score:.1f}% (Skor: {importance:.2f})")
                        indonesia_bounds = {'lat_min': -11.0, 'lat_max': 6.0, 'lon_min': 95.0, 'lon_max': 141.0}
                        is_plausible = (indonesia_bounds['lat_min'] <= lat <= indonesia_bounds['lat_max'] and
                                       indonesia_bounds['lon_min'] <= lon <= indonesia_bounds['lon_max'])
                        plausibility_score = 10 if is_plausible else 0
                        accuracy_score += plausibility_score
                        accuracy_details.append(f"Plausibilitas Koordinat: {plausibility_score}% ({'Valid' if is_plausible else 'Tidak valid'} untuk Indonesia)")
                        accuracy_details.append(f"Alamat yang Digunakan: {attempt_address}")
                        return lat, lon, accuracy_score, accuracy_details, display_name
                    else:
                        accuracy_details.append(f"Hasil tidak sesuai (ditemukan di {display_name}, bukan Jambi)")
                else:
                    accuracy_details.append(f"Tidak ada hasil untuk: {attempt_address}")
            else:
                accuracy_details.append(f"Kesalahan HTTP {response.status_code} untuk: {attempt_address}")
        except Exception as e:
            accuracy_details.append(f"Kesalahan geokoding untuk '{attempt_address}': {str(e)}")
    accuracy_details.append("Geokoding gagal untuk alamat spesifik. Menggunakan fallback ke Kota Jambi.")
    accuracy_score = min(accuracy_score + 10, 90)
    return lat, lon, accuracy_score, accuracy_details, display_name if display_name else "Kota Jambi, Indonesia"

def process_table_data(html):
    data = []
    data.extend(extract_data_from_comment(html))
    soup = BeautifulSoup(html, 'html.parser')
    main_div = soup.find('div', class_='main')
    if main_div:
        table = main_div.find('table')
        if table:
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 3:
                    label = tds[0].get_text(strip=True)
                    value = tds[2].get_text(strip=True)
                    if label and value:
                        data.append((label, value))
    unique_data = []
    seen_labels = set()
    for label, value in data:
        if label.lower() not in seen_labels and label.lower() not in ['', 'no', 'keterangan']:
            seen_labels.add(label.lower())
            unique_data.append((label, value))
    return unique_data

@cekplat_bp.route('/', methods=['GET', 'POST'])
def index():
    error = None
    table_data = None
    no_polisi = ''
    alamat = None
    processed_address = None
    coordinates = (None, None)
    accuracy_score = 0.0
    accuracy_details = []
    display_name = ""
    if request.method == 'POST':
        no_polisi = request.form.get('no_polisi', '').strip().upper()
        if not no_polisi:
            error = "Nomor polisi harus diisi"
        else:
            html = fetch_data(no_polisi)
            if html:
                table_data = process_table_data(html)
                if table_data:
                    for label, value in table_data:
                        if label.strip().lower() == 'alamat':
                            alamat = value
                            break
                    if alamat:
                        processed_address = preprocess_address(alamat)
                        lat, lon, acc_score, acc_details, disp_name = geocode_address(alamat)
                        coordinates = (lat, lon) if lat and lon else (None, None)
                        accuracy_score = acc_score
                        accuracy_details = acc_details
                        display_name = disp_name
                        logger.info(f"Debug - Alamat: {alamat}, Koordinat: {coordinates}, Akurasi: {accuracy_score}")
                else:
                    error = 'Data tidak ditemukan.'
            else:
                error = 'Gagal mengambil data dari server.'
    return render_template('cekplat.html',
                          table_data=table_data,
                          error=error,
                          no_polisi=no_polisi,
                          alamat=alamat,
                          processed_address=processed_address,
                          coordinates=coordinates,
                          accuracy_score=accuracy_score,
                          accuracy_details=accuracy_details,
                          display_name=display_name)

@cekplat_bp.route('/ajax', methods=['POST'])
def ajax_search():
    data = request.get_json()
    no_polisi = data.get('no_polisi', '').strip().upper()
    if not no_polisi:
        return {'error': 'Nomor polisi harus diisi'}, 400
    html = fetch_data(no_polisi)
    if not html:
        return {'error': 'Gagal mengambil data dari server.'}, 500
    table_data = process_table_data(html)
    if not table_data:
        return {'error': 'Data tidak ditemukan.'}, 404
    alamat = None
    for label, value in table_data:
        if label.strip().lower() == 'alamat':
            alamat = value
            break
    processed_address = preprocess_address(alamat) if alamat else None
    lat, lon, acc_score, acc_details, disp_name = (None, None, 0, [], "")
    coordinates = (None, None)
    accuracy_score = 0.0
    accuracy_details = []
    display_name = ""
    if alamat:
        processed_address = preprocess_address(alamat)
        lat, lon, acc_score, acc_details, disp_name = geocode_address(alamat)
        coordinates = (lat, lon) if lat and lon else (None, None)
        accuracy_score = acc_score
        accuracy_details = acc_details
        display_name = disp_name
    return {
        'error': None,
        'table_data': table_data,
        'alamat': alamat,
        'coordinates': coordinates,
        'accuracy_score': accuracy_score,
        'accuracy_details': accuracy_details,
        'display_name': display_name
    }
