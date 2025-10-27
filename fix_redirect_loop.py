#!/usr/bin/env python3
"""
Script to fix redirect loop issues
"""
import requests
import time
import subprocess
import sys
import os

def clear_session_via_api(base_url):
    """Clear session via API"""
    try:
        response = requests.post(f"{base_url}/api/clear-session", timeout=5)
        if response.status_code == 200:
            print("✅ Session cleared via API")
            return True
        else:
            print(f"❌ API clear failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API clear error: {e}")
        return False

def clear_session_via_web(base_url):
    """Clear session via web endpoint"""
    try:
        response = requests.get(f"{base_url}/clear-redirect-loop", timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Session cleared via web")
            return True
        else:
            print(f"❌ Web clear failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web clear error: {e}")
        return False

def restart_application():
    """Restart the Flask application"""
    print("🔄 Restarting application...")
    
    # Kill existing Python processes
    try:
        subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                      capture_output=True, check=False)
        print("✅ Killed existing Python processes")
    except:
        pass
    
    time.sleep(2)
    
    # Start the application
    try:
        subprocess.Popen([sys.executable, 'run.py'], 
                        cwd=os.getcwd())
        print("✅ Application restarted successfully!")
        return True
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False

def main():
    print("🔧 Fixing Redirect Loop Issues")
    print("=" * 50)
    
    # Get base URL
    base_url = input("Enter your application URL (e.g., http://localhost:5000 or https://your-ngrok-url.ngrok-free.dev): ").strip()
    if not base_url:
        base_url = "http://localhost:5000"
    
    print(f"🌐 Using URL: {base_url}")
    
    # Try to clear session via API
    print("\n1. Clearing session via API...")
    api_success = clear_session_via_api(base_url)
    
    # Try to clear session via web
    print("\n2. Clearing session via web...")
    web_success = clear_session_via_web(base_url)
    
    # Restart application
    print("\n3. Restarting application...")
    restart_success = restart_application()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"API Clear: {'✅ Success' if api_success else '❌ Failed'}")
    print(f"Web Clear: {'✅ Success' if web_success else '❌ Failed'}")
    print(f"Restart: {'✅ Success' if restart_success else '❌ Failed'}")
    
    if restart_success:
        print("\n🎉 Application should now work properly!")
        print("📝 Instructions:")
        print("1. Clear your browser data (localStorage, sessionStorage, cookies)")
        print("2. Refresh the page")
        print("3. Try logging in again")
    else:
        print("\n❌ Some issues occurred. Please try manual restart.")

if __name__ == '__main__':
    main()
