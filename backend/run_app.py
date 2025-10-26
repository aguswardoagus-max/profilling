#!/usr/bin/env python3
"""
Run Clearance Face Search Application with MySQL Database
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import mysql.connector
        import flask
        import requests
        import numpy
        from PIL import Image
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        from database import UserDatabase
        db = UserDatabase()
        conn = db.get_connection()
        if conn and conn.is_connected():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    # Set default database configuration if not set
    if not os.getenv('DB_HOST'):
        os.environ['DB_HOST'] = 'localhost'
    if not os.getenv('DB_PORT'):
        os.environ['DB_PORT'] = '3306'
    if not os.getenv('DB_USER'):
        os.environ['DB_USER'] = 'root'
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = ''
    if not os.getenv('DB_NAME'):
        os.environ['DB_NAME'] = 'clearance_facesearch'
    
    print("✅ Environment variables configured")

def main():
    """Main function to run the application"""
    print("🚀 Starting Clearance Face Search Application...")
    print("=" * 50)
    
    # Check dependencies
    print("\n1. Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    print("\n2. Setting up environment...")
    setup_environment()
    
    # Check database connection
    print("\n3. Checking database connection...")
    if not check_database_connection():
        print("\n❌ Database connection failed!")
        print("Please make sure:")
        print("  1. MySQL server is running")
        print("  2. Database 'clearance_facesearch' exists")
        print("  3. User has proper permissions")
        print("  4. Environment variables are set correctly")
        print("\nRun 'python setup_database.py' to setup the database")
        sys.exit(1)
    
    # Import and run the Flask app
    print("\n4. Starting Flask application...")
    try:
        from app import app
        print("✅ Flask application loaded successfully")
        print("\n🌐 Application is running at: http://localhost:5000")
        print("📝 Default login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\nPress Ctrl+C to stop the application")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
