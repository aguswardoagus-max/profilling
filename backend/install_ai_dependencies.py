#!/usr/bin/env python3
"""
Script untuk menginstall dependencies AI inpainting
"""

import subprocess
import sys
import os

def install_package(package):
    """Install package menggunakan pip"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[OK] {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install {package}: {e}")
        return False

def main():
    """Main installation function"""
    print("=== AI Inpainting Dependencies Installation ===")
    print()
    
    # Dependencies yang diperlukan
    dependencies = [
        "opencv-python==4.8.1.78",
        "lama-cleaner==1.2.0", 
        "torch==2.0.1",
        "torchvision==0.15.2"
    ]
    
    # Install dependencies
    success_count = 0
    for dep in dependencies:
        if install_package(dep):
            success_count += 1
        print()
    
    # Summary
    print("=== Installation Summary ===")
    print(f"Successfully installed: {success_count}/{len(dependencies)} packages")
    
    if success_count == len(dependencies):
        print("[OK] All dependencies installed successfully!")
        print("[OK] AI inpainting feature is ready to use")
    else:
        print("[ERROR] Some dependencies failed to install")
        print("Please check the error messages above and try again")
    
    print()
    print("Next steps:")
    print("1. Restart your Flask application")
    print("2. Test the AI inpainting feature with a search request")
    print("3. Check app.log for processing logs")

if __name__ == "__main__":
    main()
