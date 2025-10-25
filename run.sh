#!/bin/bash

# 🚀 Clearance Face Search - Run Application (Linux/Mac)

echo "🚀 Starting Clearance Face Search Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run install.sh first to set up the environment"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found!"
    echo "Please create .env file from config_example.env"
    echo "and configure your database settings"
    exit 1
fi

# Start the application
echo "🚀 Starting Flask application..."
echo "🌐 Application will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

python app.py


