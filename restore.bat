@echo off
REM 🔄 Restore Original Folder Structure (Windows)

echo 🔄 Mengembalikan struktur folder ke semula...
echo ================================================

set SECURE_FOLDER=.clearance_app

if not exist "%SECURE_FOLDER%" (
    echo ❌ Folder %SECURE_FOLDER% tidak ditemukan
    echo Jalankan secure_folder_setup.bat terlebih dahulu
    pause
    exit /b 1
)

echo 📁 Mengembalikan file dari %SECURE_FOLDER%...

REM Pindahkan file kembali ke root
for %%f in (app.py database.py cekplat.py clearance_face_search.py run_app.py requirements.txt config_example.env database_setup.sql setup_database.py) do (
    if exist "%SECURE_FOLDER%\%%f" (
        copy "%SECURE_FOLDER%\%%f" "%%f" >nul
        echo 📁 %%f dikembalikan ke root
    )
)

REM Pindahkan folder kembali
if exist "%SECURE_FOLDER%\static" (
    xcopy "%SECURE_FOLDER%\static" "static" /E /I /Q >nul
    echo 📁 static dikembalikan ke root
)

if exist "%SECURE_FOLDER%\uploads" (
    xcopy "%SECURE_FOLDER%\uploads" "uploads" /E /I /Q >nul
    echo 📁 uploads dikembalikan ke root
)

if exist "%SECURE_FOLDER%\faces" (
    xcopy "%SECURE_FOLDER%\faces" "faces" /E /I /Q >nul
    echo 📁 faces dikembalikan ke root
)

if exist "%SECURE_FOLDER%\logs" (
    xcopy "%SECURE_FOLDER%\logs" "logs" /E /I /Q >nul
    echo 📁 logs dikembalikan ke root
)

REM Hapus folder aman
rmdir /s /q "%SECURE_FOLDER%"
echo 🗑️ Folder %SECURE_FOLDER% dihapus

REM Hapus file launcher dan config
if exist "launcher.bat" (
    del "launcher.bat"
    echo 🗑️ launcher.bat dihapus
)

if exist ".app_config" (
    del ".app_config"
    echo 🗑️ .app_config dihapus
)

echo.
echo ✅ Struktur folder berhasil dikembalikan ke semula
echo 🚀 Sekarang bisa menjalankan: python app.py
echo.
pause


