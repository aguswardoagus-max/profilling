# 📦 Package Information

## 🎯 Overview
This package contains all necessary files for deploying the Clearance Face Search application to a new server.

## 📁 File Structure

### 🔧 Core Application Files
```
app.py                          # Main Flask application
database.py                     # Database connection and authentication
cekplat.py                      # Vehicle plate checking functionality
clearance_face_search.py        # Face search functionality
run_app.py                      # Application runner
```

### ⚙️ Configuration Files
```
requirements.txt                # Complete Python dependencies (RECOMMENDED)
requirements-minimal.txt        # Minimal dependencies (core only)
requirements-full.txt           # Full dependencies (all features)
requirements-dev.txt            # Development dependencies
config_example.env              # Environment configuration template
database_setup.sql              # Database schema
setup_database.py               # Database setup script
```

### 🚀 Installation Scripts
```
install.sh                      # Linux/Mac auto-installation script
install.bat                     # Windows auto-installation script
run.sh                          # Linux/Mac run script
run.bat                         # Windows run script
```

### 📚 Documentation
```
SETUP_SERVER.md                 # Detailed server setup guide
DEPLOYMENT_CHECKLIST.md         # Complete deployment checklist
README_DEPLOYMENT.md            # Quick deployment guide
PACKAGE_INFO.md                 # This file
```

### 📂 Required Directories (Created by scripts)
```
uploads/                        # File uploads directory
static/clean_photos/            # Clean photos storage
faces/                          # Face images storage
logs/                           # Application logs
```

## 🎯 Quick Start Options

### Option 1: Automated Installation (Recommended)
```bash
# Linux/Mac
chmod +x install.sh run.sh
./install.sh

# Windows
install.bat
```

### Option 2: Manual Installation
```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
mysql -u root -p -e "CREATE DATABASE clearance_face_search;"
mysql -u root -p clearance_face_search < database_setup.sql

# 4. Configure environment
cp config_example.env .env
# Edit .env with your settings

# 5. Run application
python app.py
```

## 📋 Dependencies Overview

### Core Dependencies (Always Required)
- **Flask 2.3.3** - Web framework
- **MySQL Connector 8.2.0** - Database connectivity
- **OpenCV 4.8.1.78** - Image processing
- **Pillow 10.0.1** - Image manipulation
- **NumPy <2.0.0** - Numerical computing
- **Requests 2.31.0** - HTTP requests
- **BeautifulSoup4 4.12.2** - HTML parsing
- **ReportLab 4.0.4** - PDF generation
- **python-docx 0.8.11** - Word document generation
- **python-dotenv 1.0.0** - Environment variables

### AI/ML Dependencies (Optional)
- **face_recognition 1.3.0** - Face recognition
- **torch >=2.2.0** - PyTorch framework
- **torchvision >=0.17.0** - Computer vision for PyTorch

### Production Dependencies (Optional)
- **gunicorn 21.2.0** - Production WSGI server

## 🔧 Installation Scripts Details

### install.sh (Linux/Mac)
- Updates system packages
- Installs Python, MySQL, and system dependencies
- Creates virtual environment
- Installs Python dependencies
- Sets up MySQL database
- Creates required directories
- Configures systemd service
- Optionally installs Nginx

### install.bat (Windows)
- Checks Python installation
- Creates virtual environment
- Installs Python dependencies
- Creates required directories
- Creates run scripts
- Provides setup instructions

### run.sh / run.bat
- Activates virtual environment
- Checks configuration
- Starts Flask application

## 🌐 Application Features

### Web Interface
- **Login System** - User authentication
- **Profiling** - Person search and profiling
- **Data Profiling** - Data management interface
- **Cek Plat** - Vehicle plate checking
- **User Management** - User administration
- **Responsive Design** - Mobile-friendly interface

### Backend Features
- **Database Integration** - MySQL connectivity
- **Image Processing** - OpenCV-based image manipulation
- **Watermark Removal** - AI-powered watermark cleaning
- **Document Generation** - PDF and Word export
- **API Integration** - External API connectivity
- **File Management** - Upload and storage system

### Security Features
- **Session Management** - Secure user sessions
- **Authentication** - User login system
- **Authorization** - Role-based access control
- **Input Validation** - Data sanitization
- **File Upload Security** - Secure file handling

## 📊 System Requirements

### Minimum Requirements
- **Python 3.8+** (Recommended: 3.9 or 3.10)
- **MySQL 5.7+** or **MySQL 8.0+**
- **RAM**: 1GB minimum, 2GB recommended
- **Storage**: 2GB free space minimum
- **OS**: Linux, macOS, or Windows

### Recommended Requirements
- **Python 3.10**
- **MySQL 8.0**
- **RAM**: 4GB or more
- **Storage**: 10GB free space
- **OS**: Ubuntu 20.04+ or CentOS 8+

## 🔍 Troubleshooting

### Common Issues
1. **MySQL Connection Error** - Check database credentials in .env
2. **Permission Issues** - Run with proper file permissions
3. **Missing Dependencies** - Reinstall requirements.txt
4. **Port Conflicts** - Check if port 5000 is available

### Support Files
- **SETUP_SERVER.md** - Detailed troubleshooting guide
- **DEPLOYMENT_CHECKLIST.md** - Complete deployment checklist
- **Application logs** - Check app.log for errors

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using systemd (Linux)
```bash
sudo systemctl enable clearance-app
sudo systemctl start clearance-app
```

### Using Nginx (Optional)
- Reverse proxy configuration included
- Static file serving configured
- SSL termination support

## 📞 Support

For detailed setup instructions, see:
- **SETUP_SERVER.md** - Complete server setup guide
- **DEPLOYMENT_CHECKLIST.md** - Deployment checklist
- **README_DEPLOYMENT.md** - Quick deployment guide

---

**🎉 Your Clearance Face Search application is ready for deployment!**


