# 🚀 Panduan Setup Server Baru

## 📋 Prerequisites

### 1. Python Environment
```bash
# Install Python 3.8+ (recommended: Python 3.9 atau 3.10)
python --version

# Install pip (jika belum ada)
python -m ensurepip --upgrade
```

### 2. MySQL Database
```bash
# Install MySQL Server
# Ubuntu/Debian:
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL:
sudo yum install mysql-server

# Windows: Download dari https://dev.mysql.com/downloads/mysql/
```

## 🔧 Installation Steps

### 1. Clone/Upload Project
```bash
# Upload semua file project ke server
# Pastikan struktur folder sama seperti di development
```

### 2. Setup Virtual Environment (Recommended)
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install semua dependencies
pip install -r requirements.txt

# Atau untuk development (jika diperlukan):
pip install -r requirements-dev.txt
```

### 4. Database Setup
```bash
# Login ke MySQL
mysql -u root -p

# Buat database
CREATE DATABASE clearance_face_search;

# Buat user (opsional, untuk keamanan)
CREATE USER 'clearance_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON clearance_face_search.* TO 'clearance_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Environment Configuration
```bash
# Copy dan edit file environment
cp config_example.env .env

# Edit file .env dengan konfigurasi server
nano .env
```

**Contoh isi file .env:**
```env
# Database Configuration
DB_HOST=localhost
DB_USER=clearance_user
DB_PASSWORD=your_password
DB_NAME=clearance_face_search
DB_PORT=3306

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_secret_key_here

# API Configuration
API_BASE_URL=your_api_url_here
API_TOKEN=your_api_token_here

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### 6. Database Migration
```bash
# Jalankan script setup database
python setup_database.py

# Atau manual:
python database_setup.sql
```

### 7. Create Required Directories
```bash
# Buat folder yang diperlukan
mkdir -p uploads
mkdir -p static/clean_photos
mkdir -p faces
mkdir -p logs
```

### 8. Set Permissions (Linux/Mac)
```bash
# Set permissions untuk folder uploads dan static
chmod 755 uploads
chmod 755 static
chmod 755 static/clean_photos
chmod 755 faces
chmod 755 logs
```

## 🚀 Running the Application

### Development Mode
```bash
# Aktifkan virtual environment
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Jalankan aplikasi
python app.py
# atau
python run_app.py
```

### Production Mode (Recommended)

#### Option 1: Using Gunicorn
```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Option 2: Using uWSGI
```bash
# Install uWSGI
pip install uwsgi

# Run with uWSGI
uwsgi --http :5000 --module app:app --processes 4 --threads 2
```

#### Option 3: Using systemd service (Linux)
```bash
# Buat file service
sudo nano /etc/systemd/system/clearance-app.service
```

**Isi file service:**
```ini
[Unit]
Description=Clearance Face Search App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/app/venv/bin
ExecStart=/path/to/your/app/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable dan start service
sudo systemctl enable clearance-app
sudo systemctl start clearance-app
sudo systemctl status clearance-app
```

## 🔧 Nginx Configuration (Optional)

```bash
# Install Nginx
sudo apt install nginx  # Ubuntu/Debian

# Buat konfigurasi
sudo nano /etc/nginx/sites-available/clearance-app
```

**Isi file konfigurasi Nginx:**
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads {
        alias /path/to/your/app/uploads;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/clearance-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔍 Troubleshooting

### Common Issues:

1. **MySQL Connection Error**
   ```bash
   # Check MySQL status
   sudo systemctl status mysql
   
   # Check connection
   mysql -u root -p -e "SHOW DATABASES;"
   ```

2. **Permission Issues**
   ```bash
   # Fix permissions
   sudo chown -R www-data:www-data /path/to/your/app
   sudo chmod -R 755 /path/to/your/app
   ```

3. **Port Already in Use**
   ```bash
   # Check what's using port 5000
   sudo netstat -tlnp | grep :5000
   
   # Kill process if needed
   sudo kill -9 PID
   ```

4. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt --force-reinstall
   ```

## 📊 Monitoring

### Log Files
```bash
# Application logs
tail -f app.log

# System logs
sudo journalctl -u clearance-app -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check
```bash
# Test application
curl http://localhost:5000/health

# Test database connection
python -c "from database import db; print('DB OK' if db.test_connection() else 'DB Error')"
```

## 🔐 Security Checklist

- [ ] Change default MySQL root password
- [ ] Use strong SECRET_KEY in .env
- [ ] Set proper file permissions
- [ ] Configure firewall (iptables/ufw)
- [ ] Use HTTPS in production
- [ ] Regular database backups
- [ ] Monitor log files
- [ ] Keep dependencies updated

## 📞 Support

Jika mengalami masalah, cek:
1. Log files untuk error messages
2. Database connection status
3. Port availability
4. File permissions
5. Environment variables

---

**Selamat! Aplikasi Clearance Face Search siap berjalan di server baru! 🎉**

