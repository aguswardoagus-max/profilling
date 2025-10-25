@echo off
REM 🚀 Clearance Face Search - Windows Installation Script

echo 🚀 Starting Clearance Face Search Installation for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed
    echo Please install pip or reinstall Python with pip
    pause
    exit /b 1
)

echo ✅ pip found

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment created

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✅ Virtual environment activated

REM Upgrade pip
echo 📈 Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ❌ Failed to upgrade pip
    pause
    exit /b 1
)

echo ✅ pip upgraded

REM Install dependencies
echo 📚 Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    echo This might be due to missing Visual C++ Build Tools
    echo Please install Visual Studio Build Tools from:
    echo https://visualstudio.microsoft.com/visual-cpp-build-tools/
    pause
    exit /b 1
)

echo ✅ Dependencies installed

REM Create required directories
echo 📁 Creating required directories...
if not exist "uploads" mkdir uploads
if not exist "static\clean_photos" mkdir static\clean_photos
if not exist "faces" mkdir faces
if not exist "logs" mkdir logs

echo ✅ Directories created

REM Create .env file
echo ⚙️ Creating environment configuration...
if not exist ".env" (
    if exist "config_example.env" (
        copy config_example.env .env
        echo ✅ .env file created from template
        echo ⚠️ Please edit .env file to configure your settings
    ) else (
        echo ❌ config_example.env not found
    )
) else (
    echo ✅ .env file already exists
)

REM Database setup reminder
echo.
echo 📊 Database Setup Required:
echo Please ensure you have MySQL installed and configured
echo Then run: python setup_database.py
echo.

REM Create run script
echo 📝 Creating run script...
echo @echo off > run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python app.py >> run.bat
echo pause >> run.bat

echo ✅ run.bat created

REM Create service script (for Windows Service)
echo 📝 Creating service script...
echo @echo off > start_service.bat
echo call venv\Scripts\activate.bat >> start_service.bat
echo python app.py >> start_service.bat

echo ✅ start_service.bat created

echo.
echo 🎉 Installation completed!
echo.
echo 📋 Next Steps:
echo 1. Install MySQL Server if not already installed
echo 2. Edit .env file with your database credentials
echo 3. Run: python setup_database.py
echo 4. Start the application: run.bat
echo.
echo 🌐 Access the application at: http://localhost:5000
echo.
echo 📁 Important Files:
echo   • Configuration: .env
echo   • Run Application: run.bat
echo   • Service Start: start_service.bat
echo.
echo 🔧 Troubleshooting:
echo   • If OpenCV fails to install, install Visual C++ Build Tools
echo   • If MySQL connection fails, check .env database settings
echo   • Check app.log for detailed error messages
echo.
pause


