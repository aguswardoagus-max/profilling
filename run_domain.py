#!/usr/bin/env python3
"""
Script to run the application with domain configuration
"""
import os
import sys
import subprocess

def run_with_domain(domain=None, port=5000, https=False):
    """Run the application with specific domain configuration"""
    
    # Set environment variables
    env = os.environ.copy()
    
    if domain:
        if https:
            base_url = f"https://{domain}:{port}"
        else:
            base_url = f"http://{domain}:{port}"
        
        env['BASE_URL'] = base_url
        env['HTTPS'] = 'true' if https else 'false'
        
        # Add domain to allowed origins
        allowed_origins = [
            f"http://{domain}:{port}",
            f"https://{domain}:{port}",
            "http://localhost:5000",
            "http://127.0.0.1:5000"
        ]
        env['ALLOWED_ORIGINS'] = ','.join(allowed_origins)
        
        print(f"Running with domain: {base_url}")
        print(f"Allowed origins: {allowed_origins}")
    else:
        print("Running with default localhost configuration")
    
    # Set Flask environment
    env['FLASK_ENV'] = 'development'
    
    # Run the application
    try:
        subprocess.run([sys.executable, 'run.py'], env=env)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Clearance Face Search with domain configuration')
    parser.add_argument('--domain', '-d', help='Domain name (e.g., yourdomain.com)')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--https', action='store_true', help='Use HTTPS')
    
    args = parser.parse_args()
    
    run_with_domain(args.domain, args.port, args.https)
