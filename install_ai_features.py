#!/usr/bin/env python3
"""
AI Features Installation Script for Clearance Face Search System
Installs and configures advanced AI features
"""

import subprocess
import sys
import os
import platform
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIInstaller:
    """AI Features Installer"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = sys.version_info
        self.install_log = []
        
    def log_install(self, package: str, status: str, message: str = ""):
        """Log installation status"""
        log_entry = f"{package}: {status}"
        if message:
            log_entry += f" - {message}"
        self.install_log.append(log_entry)
        logger.info(log_entry)
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        if self.python_version < (3, 8):
            logger.error("Python 3.8 or higher is required for AI features")
            return False
        
        logger.info(f"Python version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        return True
    
    def install_system_dependencies(self):
        """Install system-level dependencies"""
        logger.info("Installing system dependencies...")
        
        if self.system == "windows":
            self._install_windows_dependencies()
        elif self.system == "linux":
            self._install_linux_dependencies()
        elif self.system == "darwin":  # macOS
            self._install_macos_dependencies()
        else:
            logger.warning(f"Unsupported system: {self.system}")
    
    def _install_windows_dependencies(self):
        """Install Windows dependencies"""
        try:
            # Install Visual C++ Build Tools if needed
            logger.info("Windows detected - ensure Visual C++ Build Tools are installed")
            logger.info("Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            
            # Install CMake
            try:
                subprocess.run(["cmake", "--version"], check=True, capture_output=True)
                self.log_install("CMake", "Already installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("CMake not found - please install CMake for Windows")
                self.log_install("CMake", "Not found", "Please install manually")
            
        except Exception as e:
            logger.error(f"Error installing Windows dependencies: {e}")
    
    def _install_linux_dependencies(self):
        """Install Linux dependencies"""
        try:
            # Update package list
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            
            # Install essential packages
            packages = [
                "build-essential",
                "cmake",
                "libopencv-dev",
                "python3-opencv",
                "libgl1-mesa-glx",
                "libglib2.0-0",
                "libsm6",
                "libxext6",
                "libxrender-dev",
                "libgomp1",
                "libgcc-s1"
            ]
            
            for package in packages:
                try:
                    subprocess.run(["sudo", "apt-get", "install", "-y", package], check=True)
                    self.log_install(package, "Installed")
                except subprocess.CalledProcessError:
                    self.log_install(package, "Failed", "Manual installation required")
            
        except Exception as e:
            logger.error(f"Error installing Linux dependencies: {e}")
    
    def _install_macos_dependencies(self):
        """Install macOS dependencies"""
        try:
            # Check if Homebrew is installed
            try:
                subprocess.run(["brew", "--version"], check=True, capture_output=True)
                self.log_install("Homebrew", "Already installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("Installing Homebrew...")
                subprocess.run([
                    '/bin/bash', '-c', 
                    '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'
                ], check=True)
                self.log_install("Homebrew", "Installed")
            
            # Install packages via Homebrew
            packages = ["cmake", "opencv", "tesseract"]
            
            for package in packages:
                try:
                    subprocess.run(["brew", "install", package], check=True)
                    self.log_install(package, "Installed")
                except subprocess.CalledProcessError:
                    self.log_install(package, "Failed", "Manual installation required")
            
        except Exception as e:
            logger.error(f"Error installing macOS dependencies: {e}")
    
    def install_python_packages(self):
        """Install Python packages for AI features"""
        logger.info("Installing Python AI packages...")
        
        # Core packages (install first)
        core_packages = [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scikit-learn>=1.3.0",
            "opencv-python>=4.8.0",
            "Pillow>=10.0.0"
        ]
        
        # Advanced AI packages
        ai_packages = [
            "deepface>=0.0.79",
            "insightface>=0.7.3",
            "facenet-pytorch>=2.5.3",
            "face-recognition>=1.3.0",
            "spacy>=3.6.1",
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "torchvision>=0.15.0"
        ]
        
        # Utility packages
        utility_packages = [
            "pytesseract>=0.3.10",
            "speechrecognition>=3.10.0",
            "redis>=4.6.0",
            "plotly>=5.15.0",
            "matplotlib>=3.7.0"
        ]
        
        # Install packages in groups
        package_groups = [
            ("Core Packages", core_packages),
            ("AI Packages", ai_packages),
            ("Utility Packages", utility_packages)
        ]
        
        for group_name, packages in package_groups:
            logger.info(f"Installing {group_name}...")
            for package in packages:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                 check=True, capture_output=True)
                    self.log_install(package.split(">=")[0], "Installed")
                except subprocess.CalledProcessError as e:
                    self.log_install(package.split(">=")[0], "Failed", str(e))
    
    def download_spacy_models(self):
        """Download spaCy language models"""
        logger.info("Downloading spaCy language models...")
        
        models = [
            "en_core_web_sm",
            "id_core_news_sm"  # Indonesian model if available
        ]
        
        for model in models:
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", model], 
                             check=True, capture_output=True)
                self.log_install(f"spaCy {model}", "Downloaded")
            except subprocess.CalledProcessError:
                self.log_install(f"spaCy {model}", "Failed", "Manual download required")
    
    def setup_database(self):
        """Setup AI analytics database"""
        logger.info("Setting up AI analytics database...")
        
        try:
            from ai_enhancements_implementation import AIEnhancements
            ai = AIEnhancements()
            self.log_install("AI Database", "Initialized")
        except Exception as e:
            self.log_install("AI Database", "Failed", str(e))
    
    def create_directories(self):
        """Create necessary directories"""
        logger.info("Creating AI directories...")
        
        directories = [
            "ai_models",
            "ai_cache",
            "ai_logs",
            "ai_temp"
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(exist_ok=True)
                self.log_install(f"Directory {directory}", "Created")
            except Exception as e:
                self.log_install(f"Directory {directory}", "Failed", str(e))
    
    def test_installation(self):
        """Test AI installation"""
        logger.info("Testing AI installation...")
        
        tests = [
            ("NumPy", "import numpy as np"),
            ("OpenCV", "import cv2"),
            ("PIL", "from PIL import Image"),
            ("scikit-learn", "from sklearn.cluster import KMeans"),
            ("DeepFace", "from deepface import DeepFace"),
            ("spaCy", "import spacy")
        ]
        
        for test_name, import_statement in tests:
            try:
                exec(import_statement)
                self.log_install(test_name, "Test passed")
            except ImportError:
                self.log_install(test_name, "Test failed", "Import error")
            except Exception as e:
                self.log_install(test_name, "Test failed", str(e))
    
    def generate_install_report(self):
        """Generate installation report"""
        logger.info("Generating installation report...")
        
        report_path = "ai_installation_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("AI Features Installation Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"System: {self.system}\n")
            f.write(f"Python Version: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}\n")
            f.write(f"Installation Date: {__import__('datetime').datetime.now()}\n\n")
            
            f.write("Installation Log:\n")
            f.write("-" * 30 + "\n")
            for entry in self.install_log:
                f.write(f"{entry}\n")
        
        logger.info(f"Installation report saved to: {report_path}")
        return report_path
    
    def install_all(self):
        """Install all AI features"""
        logger.info("Starting AI features installation...")
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Install system dependencies
        self.install_system_dependencies()
        
        # Create directories
        self.create_directories()
        
        # Install Python packages
        self.install_python_packages()
        
        # Download spaCy models
        self.download_spacy_models()
        
        # Setup database
        self.setup_database()
        
        # Test installation
        self.test_installation()
        
        # Generate report
        report_path = self.generate_install_report()
        
        logger.info("AI features installation completed!")
        logger.info(f"Check {report_path} for detailed installation log")
        
        return True

def main():
    """Main installation function"""
    print("🚀 AI Features Installation for Clearance Face Search System")
    print("=" * 60)
    
    installer = AIInstaller()
    
    try:
        success = installer.install_all()
        
        if success:
            print("\n✅ AI features installation completed successfully!")
            print("\nNext steps:")
            print("1. Restart your application")
            print("2. Test AI features using the API endpoints")
            print("3. Check the installation report for any issues")
        else:
            print("\n❌ AI features installation failed!")
            print("Please check the installation log for details")
            
    except KeyboardInterrupt:
        print("\n⚠️ Installation cancelled by user")
    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        logger.error(f"Installation failed: {e}")

if __name__ == "__main__":
    main()

