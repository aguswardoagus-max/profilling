#!/usr/bin/env python3
"""
Script to run the application with ngrok configuration
"""
import os
import sys
import subprocess

def run_with_ngrok(ngrok_url=None, port=5000):
    """Run the application with ngrok configuration"""
    
    # Set environment variables for ngrok
    env = os.environ.copy()
    
    if ngrok_url:
        env['BASE_URL'] = ngrok_url
        env['HTTPS'] = 'true' if ngrok_url.startswith('https') else 'false'
        
        # Add ngrok domain to allowed origins
        allowed_origins = [
            ngrok_url,
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "https://localhost:5000",
            "https://127.0.0.1:5000",
            "*"  # Allow all for ngrok
        ]
        env['ALLOWED_ORIGINS'] = ','.join(allowed_origins)
        
        print(f"Running with ngrok URL: {ngrok_url}")
        print(f"Allowed origins: {allowed_origins}")
    else:
        print("Running with ngrok auto-detection")
        env['ALLOWED_ORIGINS'] = "*,http://localhost:5000,http://127.0.0.1:5000"
    
    # Set Flask environment
    env['FLASK_ENV'] = 'development'
    env['NGROK_MODE'] = 'true'
    
    print("=" * 60)
    print("🚀 Starting Clearance Face Search with NGROK Support")
    print("=" * 60)
    print(f"📡 Port: {port}")
    print(f"🌐 NGROK URL: {ngrok_url or 'Auto-detect'}")
    print(f"🔒 HTTPS: {env.get('HTTPS', 'false')}")
    print(f"🌍 CORS: Enabled for all domains")
    print("=" * 60)
    
    # Run the application
    try:
        subprocess.run([sys.executable, 'run.py'], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Clearance Face Search with ngrok configuration')
    parser.add_argument('--ngrok-url', '-n', help='NGROK URL (e.g., https://abc123.ngrok-free.dev)')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port number (default: 5000)')
    
    args = parser.parse_args()
    
    run_with_ngrok(args.ngrok_url, args.port)
