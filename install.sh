#!/bin/bash

# 🚀 Clearance Face Search - Auto Installation Script
# Untuk Ubuntu/Debian Linux

set -e  # Exit on any error

echo "🚀 Starting Clearance Face Search Installation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
print_status "Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install MySQL
print_status "Installing MySQL Server..."
sudo apt install -y mysql-server

# Install system dependencies for OpenCV and other packages
print_status "Installing system dependencies..."
sudo apt install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    libc6-dev \
    build-essential \
    pkg-config \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    git

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Setup MySQL
print_status "Setting up MySQL database..."
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure MySQL installation
print_warning "Please set MySQL root password when prompted:"
sudo mysql_secure_installation

# Create database and user
print_status "Creating database and user..."
read -p "Enter MySQL root password: " -s mysql_root_password
echo

# Create database
mysql -u root -p$mysql_root_password -e "CREATE DATABASE IF NOT EXISTS clearance_face_search;"

# Create user
read -p "Enter database username (default: clearance_user): " db_user
db_user=${db_user:-clearance_user}

read -p "Enter database password: " -s db_password
echo

mysql -u root -p$mysql_root_password -e "CREATE USER IF NOT EXISTS '$db_user'@'localhost' IDENTIFIED BY '$db_password';"
mysql -u root -p$mysql_root_password -e "GRANT ALL PRIVILEGES ON clearance_face_search.* TO '$db_user'@'localhost';"
mysql -u root -p$mysql_root_password -e "FLUSH PRIVILEGES;"

# Create required directories
print_status "Creating required directories..."
mkdir -p uploads
mkdir -p static/clean_photos
mkdir -p faces
mkdir -p logs

# Set permissions
print_status "Setting permissions..."
chmod 755 uploads
chmod 755 static
chmod 755 static/clean_photos
chmod 755 faces
chmod 755 logs

# Create .env file
print_status "Creating environment configuration..."
if [ ! -f .env ]; then
    cp config_example.env .env
    
    # Update .env with database credentials
    sed -i "s/DB_USER=.*/DB_USER=$db_user/" .env
    sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$db_password/" .env
    sed -i "s/DB_NAME=.*/DB_NAME=clearance_face_search/" .env
    
    print_warning "Please edit .env file to configure other settings:"
    print_warning "nano .env"
fi

# Setup database schema
print_status "Setting up database schema..."
if [ -f setup_database.py ]; then
    python setup_database.py
elif [ -f database_setup.sql ]; then
    mysql -u $db_user -p$db_password clearance_face_search < database_setup.sql
else
    print_warning "No database setup script found. Please run database setup manually."
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/clearance-app.service > /dev/null <<EOF
[Unit]
Description=Clearance Face Search App
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Install Gunicorn if not already installed
pip install gunicorn

# Enable and start service
print_status "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable clearance-app
sudo systemctl start clearance-app

# Check service status
print_status "Checking service status..."
sleep 3
if sudo systemctl is-active --quiet clearance-app; then
    print_success "Service is running successfully!"
else
    print_error "Service failed to start. Check logs with: sudo journalctl -u clearance-app -f"
fi

# Install Nginx (optional)
read -p "Do you want to install Nginx as reverse proxy? (y/n): " install_nginx
if [[ $install_nginx =~ ^[Yy]$ ]]; then
    print_status "Installing Nginx..."
    sudo apt install -y nginx
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/clearance-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias $(pwd)/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads {
        alias $(pwd)/uploads;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/clearance-app /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    print_success "Nginx installed and configured!"
fi

# Final status check
print_status "Performing final checks..."

# Check if app is accessible
if curl -s http://localhost:5000 > /dev/null; then
    print_success "Application is accessible on http://localhost:5000"
else
    print_warning "Application might not be accessible yet. Check service status."
fi

# Display useful information
echo
print_success "🎉 Installation completed!"
echo
echo "📋 Useful Commands:"
echo "  • Check service status: sudo systemctl status clearance-app"
echo "  • View logs: sudo journalctl -u clearance-app -f"
echo "  • Restart service: sudo systemctl restart clearance-app"
echo "  • Stop service: sudo systemctl stop clearance-app"
echo
echo "🌐 Access URLs:"
echo "  • Direct: http://localhost:5000"
if [[ $install_nginx =~ ^[Yy]$ ]]; then
    echo "  • Via Nginx: http://localhost"
fi
echo
echo "📁 Important Files:"
echo "  • Configuration: $(pwd)/.env"
echo "  • Logs: $(pwd)/app.log"
echo "  • Service: /etc/systemd/system/clearance-app.service"
echo
echo "🔧 Next Steps:"
echo "  1. Edit .env file to configure API settings"
echo "  2. Test the application"
echo "  3. Configure firewall if needed"
echo "  4. Set up SSL certificate for production"
echo
print_success "Happy coding! 🚀"

