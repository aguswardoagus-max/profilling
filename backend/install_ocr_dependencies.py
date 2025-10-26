#!/usr/bin/env python3
"""
Script to install OCR dependencies for NIK extraction
"""

import subprocess
import sys
import os
import platform

def install_pytesseract():
    """Install pytesseract package"""
    try:
        print("Installing pytesseract...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytesseract>=0.3.10"], check=True)
        print("✓ pytesseract installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install pytesseract: {e}")
        return False

def install_tesseract_ocr():
    """Install Tesseract OCR engine based on OS"""
    system = platform.system().lower()
    
    if system == "windows":
        print("Windows detected. Please install Tesseract OCR manually:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Install the executable")
        print("3. Add Tesseract to your PATH or set TESSDATA_PREFIX environment variable")
        print("4. Restart your terminal/IDE")
        return True
    elif system == "darwin":  # macOS
        try:
            print("Installing Tesseract OCR via Homebrew...")
            subprocess.run(["brew", "install", "tesseract"], check=True)
            print("✓ Tesseract OCR installed successfully")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ Homebrew not found. Please install Tesseract manually:")
            print("brew install tesseract")
            return False
    elif system == "linux":
        try:
            print("Installing Tesseract OCR via apt...")
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr", "tesseract-ocr-ind"], check=True)
            print("✓ Tesseract OCR installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install via apt. Please install manually:")
            print("sudo apt-get install tesseract-ocr tesseract-ocr-ind")
            return False
    else:
        print(f"Unsupported OS: {system}")
        return False

def test_ocr_installation():
    """Test if OCR is working properly"""
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Create a simple test image with text
        from PIL import ImageDraw, ImageFont
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 15), "1234567890123456", fill='black', font=font)
        
        # Test OCR
        text = pytesseract.image_to_string(img, config='--psm 6 --oem 3')
        print(f"✓ OCR test successful. Extracted text: '{text.strip()}'")
        return True
        
    except Exception as e:
        print(f"✗ OCR test failed: {e}")
        return False

def main():
    """Main installation function"""
    print("=== OCR Dependencies Installation ===")
    print()
    
    # Install Python packages
    if not install_pytesseract():
        print("Failed to install pytesseract. Exiting.")
        return False
    
    # Install Tesseract OCR engine
    if not install_tesseract_ocr():
        print("Failed to install Tesseract OCR engine. Please install manually.")
        return False
    
    # Test installation
    print("\nTesting OCR installation...")
    if test_ocr_installation():
        print("\n✓ OCR installation completed successfully!")
        print("You can now use the OCR NIK extraction feature.")
        return True
    else:
        print("\n✗ OCR installation test failed.")
        print("Please check your Tesseract installation and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
