# OCR NIK Extraction Feature

## Overview
Fitur OCR (Optical Character Recognition) untuk membaca NIK dari foto yang diupload. User dapat mengupload foto KTP atau dokumen identitas lainnya, dan sistem akan secara otomatis mengekstrak NIK yang terdeteksi.

## Features
- **Multiple NIK Detection**: Jika ada beberapa NIK dalam foto, sistem akan menampilkan semua pilihan
- **Auto-fill Form**: NIK yang dipilih akan otomatis mengisi field NIK dan nama (jika terdeteksi)
- **Manual Input**: Fitur input manual tetap aktif sebagai alternatif
- **Confidence Scoring**: Setiap NIK yang terdeteksi memiliki skor kepercayaan
- **Visual Feedback**: UI yang jelas menunjukkan sumber data (OCR vs AI)

## Technical Implementation

### Backend
- **Endpoint**: `/api/ai/ocr-nik` (POST)
- **Library**: pytesseract dengan Tesseract OCR engine
- **Language Support**: Indonesian (ind) dengan fallback ke English (eng)
- **Configuration**: PSM 6, OEM 3 untuk optimasi teks

### Frontend
- **Upload Area**: Drag & drop atau click untuk upload foto
- **Results Display**: List pilihan NIK dengan confidence score
- **Auto-selection**: NIK dengan confidence tertinggi otomatis dipilih
- **Visual Indicators**: Icon dan badge untuk membedakan sumber data

## Installation

### 1. Install Python Dependencies
```bash
pip install pytesseract>=0.3.10
```

### 2. Install Tesseract OCR Engine

#### Windows
1. Download dari: https://github.com/UB-Mannheim/tesseract/wiki
2. Install executable
3. Tambahkan ke PATH atau set TESSDATA_PREFIX

#### macOS
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-ind
```

### 3. Run Installation Script
```bash
python backend/install_ocr_dependencies.py
```

## Usage

1. **Upload Foto**: Klik area upload atau drag & drop foto KTP/dokumen identitas
2. **Wait for Processing**: Sistem akan memproses foto dengan OCR
3. **Select NIK**: Pilih NIK yang benar dari daftar pilihan (jika ada multiple)
4. **Auto-fill**: Form akan otomatis terisi dengan NIK dan nama yang dipilih
5. **Manual Override**: User tetap bisa mengedit field secara manual

## API Response Format

```json
{
  "success": true,
  "data": {
    "extracted_text": "Full OCR text...",
    "nik_candidates": [
      {
        "nik": "1234567890123456",
        "name": "JOHN DOE",
        "confidence": 90,
        "source": "ocr"
      }
    ],
    "total_found": 1,
    "extracted_name": "JOHN DOE"
  },
  "message": "OCR NIK extraction completed. Found 1 NIK candidates."
}
```

## Error Handling
- **Invalid Image**: Validasi tipe file dan ukuran (max 5MB)
- **OCR Failure**: Fallback ke pesan error yang informatif
- **No NIK Found**: Menampilkan pesan "Tidak ada NIK yang ditemukan"
- **Network Error**: Retry mechanism dan error logging

## Performance Notes
- **Processing Time**: ~2-5 detik tergantung ukuran dan kualitas foto
- **Memory Usage**: Minimal impact dengan PIL dan pytesseract
- **Caching**: Tidak ada caching untuk OCR results (real-time processing)

## Future Enhancements
- [ ] Support untuk multiple bahasa OCR
- [ ] Image preprocessing untuk meningkatkan akurasi
- [ ] Batch processing untuk multiple foto
- [ ] Confidence threshold configuration
- [ ] OCR result caching untuk foto yang sama
