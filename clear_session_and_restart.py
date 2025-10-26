#!/usr/bin/env python3
"""
Script to clear all session data and restart the application
"""
import os
import sys
import subprocess
import time

def clear_session_data():
    """Clear all session-related data"""
    print("Clearing session data...")
    
    # Clear browser data instructions
    print("""
    ========================================
    SESSION DATA CLEARING INSTRUCTIONS
    ========================================
    
    1. Open your browser (Chrome, Firefox, etc.)
    2. Press F12 to open Developer Tools
    3. Go to Application/Storage tab
    4. Clear the following:
       - Local Storage (all items)
       - Session Storage (all items)
       - Cookies (all items)
    5. Or use Ctrl+Shift+Delete to clear browsing data
    
    Alternative: Use Incognito/Private mode
    ========================================
    """)

def restart_application():
    """Restart the Flask application"""
    print("Restarting application...")
    
    # Kill existing Python processes
    try:
        subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                      capture_output=True, check=False)
        print("Killed existing Python processes")
    except:
        pass
    
    time.sleep(2)
    
    # Start the application
    try:
        subprocess.Popen([sys.executable, 'run.py'], 
                        cwd=os.getcwd())
        print("Application restarted successfully!")
        print("Server should be running at: http://127.0.0.1:5000")
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == '__main__':
    clear_session_data()
    restart_application()
