@echo off
REM 🚀 Clearance Face Search - Run Application

echo 🚀 Starting Clearance Face Search Application...

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run install.bat first to set up the environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️ .env file not found!
    echo Please create .env file from config_example.env
    echo and configure your database settings
    pause
    exit /b 1
)

REM Start the application
echo 🚀 Starting Flask application...
echo 🌐 Application will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

python app.py

pause


