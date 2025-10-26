#!/usr/bin/env python3
"""
Entry point untuk Clearance Face Search Application
Menjalankan aplikasi Flask dari struktur folder yang terorganisir
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the Flask app
from app import app



if __name__ == '__main__':
    print("Starting Clearance Face Search Application...")
    print("Backend: ./backend/")
    print("Frontend: ./frontend/")
    print("Config: ./config/")
    print("Server: http://127.0.0.1:5000")
    print("Authentication: Enabled")
    print("AI Features: Ready")
    print("Reports: Available")
    print("-" * 50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
