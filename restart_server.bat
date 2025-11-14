@echo off
echo ========================================
echo    RESTARTING PROFILING SERVER
echo ========================================
echo.
echo [1/3] Stopping any existing server...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 >nul

echo.
echo [2/3] Starting server with new API key...
cd backend
start "Profiling Server" cmd /k "python app.py"

echo.
echo [3/3] Done!
echo.
echo ========================================
echo Server is starting in a new window...
echo Wait for "Running on http://127.0.0.1:5000"
echo Then refresh your browser with Ctrl+F5
echo ========================================
echo.
pause



