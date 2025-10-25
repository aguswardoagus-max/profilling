@echo off
REM 🔒 Clearance Face Search - Secure Folder Setup (Windows)

echo 🔒 Clearance Face Search - Secure Folder Setup
echo ================================================

REM Buat folder tersembunyi
set SECURE_FOLDER=.clearance_app

if not exist "%SECURE_FOLDER%" (
    mkdir "%SECURE_FOLDER%"
    echo ✅ Folder %SECURE_FOLDER% berhasil dibuat
) else (
    echo ✅ Folder %SECURE_FOLDER% sudah ada
)

REM Daftar file yang perlu dipindahkan
set FILES_TO_MOVE=app.py database.py cekplat.py clearance_face_search.py run_app.py requirements.txt config_example.env database_setup.sql setup_database.py

REM Pindahkan file ke folder aman
echo 📁 Memindahkan file ke folder aman...
for %%f in (%FILES_TO_MOVE%) do (
    if exist "%%f" (
        copy "%%f" "%SECURE_FOLDER%\%%f" >nul
        echo 📁 %%f dipindahkan ke %SECURE_FOLDER%/
    )
)

REM Pindahkan folder
if exist "static" (
    xcopy "static" "%SECURE_FOLDER%\static" /E /I /Q >nul
    echo 📁 static dipindahkan ke %SECURE_FOLDER%/
)

if exist "uploads" (
    xcopy "uploads" "%SECURE_FOLDER%\uploads" /E /I /Q >nul
    echo 📁 uploads dipindahkan ke %SECURE_FOLDER%/
)

if exist "faces" (
    xcopy "faces" "%SECURE_FOLDER%\faces" /E /I /Q >nul
    echo 📁 faces dipindahkan ke %SECURE_FOLDER%/
)

if exist "logs" (
    xcopy "logs" "%SECURE_FOLDER%\logs" /E /I /Q >nul
    echo 📁 logs dipindahkan ke %SECURE_FOLDER%/
)

REM Buat script launcher
echo 📝 Membuat script launcher...

(
echo @echo off
echo REM 🚀 Clearance Face Search Launcher
echo echo 🚀 Menjalankan Clearance Face Search...
echo cd /d "%SECURE_FOLDER%"
echo python app.py
echo pause
) > launcher.bat

echo ✅ Script launcher.bat berhasil dibuat

REM Buat file konfigurasi
(
echo # Konfigurasi Path Aplikasi
echo APP_FOLDER=%SECURE_FOLDER%
echo APP_NAME=Clearance Face Search
echo APP_VERSION=1.0.0
) > .app_config

echo ✅ File konfigurasi .app_config berhasil dibuat

echo.
echo 🎉 Setup selesai!
echo 📁 Aplikasi sekarang ada di folder: %SECURE_FOLDER%
echo 🚀 Jalankan dengan: launcher.bat
echo.
echo 🔒 Folder tersembunyi dan aman dari akses sembarangan
echo 💡 Untuk mengembalikan struktur semula, jalankan: restore.bat
echo.
pause


