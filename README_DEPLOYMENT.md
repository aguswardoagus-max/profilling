# 🚀 Quick Deployment Guide

## 📦 Files Included for Deployment

### Core Application Files
- `app.py` - Main Flask application
- `database.py` - Database connection and authentication
- `cekplat.py` - Vehicle plate checking functionality
- `clearance_face_search.py` - Face search functionality

### Configuration Files
- `requirements.txt` - **Complete Python dependencies**
- `config_example.env` - Environment configuration template
- `database_setup.sql` - Database schema
- `setup_database.py` - Database setup script

### Installation Scripts
- `install.sh` - **Linux/Mac auto-installation script**
- `install.bat` - **Windows auto-installation script**
- `run.sh` - **Linux/Mac run script**
- `run.bat` - **Windows run script**

### Documentation
- `SETUP_SERVER.md` - **Detailed server setup guide**
- `DEPLOYMENT_CHECKLIST.md` - **Complete deployment checklist**
- `README_DEPLOYMENT.md` - This file

## 🚀 Quick Start

### For Linux/Mac:
```bash
# 1. Make scripts executable
chmod +x install.sh run.sh

# 2. Run installation
./install.sh

# 3. Start application
./run.sh
```

### For Windows:
```cmd
# 1. Run installation
install.bat

# 2. Start application
run.bat
```

## 📋 Manual Installation

### 1. Install Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE clearance_face_search;"

# Import schema
mysql -u root -p clearance_face_search < database_setup.sql
```

### 3. Configure Environment
```bash
# Copy configuration template
cp config_example.env .env

# Edit configuration
nano .env  # or use your preferred editor
```

### 4. Run Application
```bash
python app.py
```

## 🔧 Production Deployment

### Using Gunicorn (Linux/Mac):
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using systemd service:
```bash
# Copy service file (created by install.sh)
sudo systemctl enable clearance-app
sudo systemctl start clearance-app
```

## 📊 Dependencies Included

### Core Framework
- `flask==2.3.3` - Web framework
- `flask-cors==4.0.0` - CORS support

### Database
- `mysql-connector-python==8.2.0` - MySQL connector

### Image Processing
- `opencv-python==4.8.1.78` - Computer vision
- `pillow==10.0.1` - Image processing
- `numpy<2.0.0` - Numerical computing
- `face_recognition==1.3.0` - Face recognition

### AI/ML
- `torch>=2.2.0` - PyTorch
- `torchvision>=0.17.0` - Computer vision for PyTorch

### Web & HTTP
- `requests==2.31.0` - HTTP requests
- `beautifulsoup4==4.12.2` - HTML parsing

### Document Generation
- `reportlab==4.0.4` - PDF generation
- `python-docx==0.8.11` - Word document generation

### Configuration
- `python-dotenv==1.0.0` - Environment variables

## 🌐 Access URLs

- **Application**: http://localhost:5000
- **Login**: http://localhost:5000/login
- **Profiling**: http://localhost:5000/profiling
- **Data Profiling**: http://localhost:5000/data-profiling
- **Cek Plat**: http://localhost:5000/cekplat
- **User Management**: http://localhost:5000/user-management

## 🔍 Troubleshooting

### Common Issues:

1. **MySQL Connection Error**
   ```bash
   # Check MySQL status
   sudo systemctl status mysql
   ```

2. **Permission Issues**
   ```bash
   # Fix permissions
   chmod 755 uploads static faces logs
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

4. **Port Already in Use**
   ```bash
   # Check what's using port 5000
   sudo netstat -tlnp | grep :5000
   ```

## 📞 Support

- Check `SETUP_SERVER.md` for detailed setup instructions
- Check `DEPLOYMENT_CHECKLIST.md` for complete deployment checklist
- Check application logs in `app.log`
- Check system logs: `sudo journalctl -u clearance-app -f`

---

**🎉 Your Clearance Face Search application is ready to deploy!**


