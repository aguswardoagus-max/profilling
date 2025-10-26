#!/usr/bin/env python3
"""
AI Features Integration Script - Simple Version
Integrates AI features with the main Clearance Face Search application
"""

import os
import sys
import shutil
from pathlib import Path

def integrate_ai_features():
    """Integrate AI features with the main application"""
    
    print("Integrating AI Features with Clearance Face Search System")
    print("=" * 60)
    
    # Check if main app.py exists
    if not os.path.exists('app.py'):
        print("Error: app.py not found. Please run this script from the project root directory.")
        return False
    
    # Backup original app.py
    if os.path.exists('app.py'):
        shutil.copy('app.py', 'app_backup.py')
        print("Backed up original app.py to app_backup.py")
    
    # Read current app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    # Check if AI endpoints are already integrated
    if 'from ai_api_endpoints import register_ai_endpoints' in app_content:
        print("AI endpoints already integrated in app.py")
    else:
        # Add AI imports
        ai_imports = """
# AI Features Integration
try:
    from ai_api_endpoints import register_ai_endpoints
    from ai_enhancements_implementation import AIEnhancements
    AI_FEATURES_ENABLED = True
    print("AI Features loaded successfully")
except ImportError as e:
    print(f"AI Features not available: {e}")
    AI_FEATURES_ENABLED = False
"""
        
        # Find the import section and add AI imports
        if 'from flask import' in app_content:
            app_content = app_content.replace(
                'from flask import',
                ai_imports + '\nfrom flask import'
            )
        else:
            # Add at the beginning if no flask import found
            app_content = ai_imports + '\n' + app_content
        
        # Add AI initialization after app creation
        if 'app = Flask(__name__)' in app_content:
            ai_init = """
# Initialize AI Features
if AI_FEATURES_ENABLED:
    try:
        ai_enhancements = AIEnhancements()
        register_ai_endpoints(app)
        print("AI Features initialized successfully")
    except Exception as e:
        print(f"Error initializing AI Features: {e}")
        AI_FEATURES_ENABLED = False
"""
            app_content = app_content.replace(
                'app = Flask(__name__)',
                'app = Flask(__name__)' + ai_init
            )
        
        # Write updated app.py
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print("AI endpoints integrated into app.py")
    
    # Create AI configuration file
    ai_config_content = """# AI Features Configuration
AI_ENABLED = True
AI_MODELS_PATH = "./ai_models"
AI_CACHE_PATH = "./ai_cache"
AI_LOG_LEVEL = "INFO"

# DeepFace Configuration
DEEPFACE_BACKEND = "tensorflow"
DEEPFACE_MODEL_NAME = "Facenet"

# Database Configuration
AI_DATABASE_PATH = "./ai_analytics.db"

# Performance Configuration
AI_MAX_WORKERS = 4
AI_CACHE_SIZE = 1000
AI_BATCH_SIZE = 32

# Feature Toggles
ENABLE_FACE_ANALYSIS = True
ENABLE_SMART_SEARCH = True
ENABLE_RISK_ASSESSMENT = True
ENABLE_IMAGE_ENHANCEMENT = True
ENABLE_CHATBOT = True
ENABLE_OCR = True
ENABLE_VOICE_SEARCH = True
"""
    
    with open('ai_config.py', 'w', encoding='utf-8') as f:
        f.write(ai_config_content)
    
    print("AI configuration file created: ai_config.py")
    
    # Create AI directories
    ai_dirs = ['ai_models', 'ai_cache', 'ai_logs', 'ai_temp']
    for dir_name in ai_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"Created directory: {dir_name}")
    
    print("\nAI Features Integration Completed!")
    print("\nNext Steps:")
    print("1. Install AI dependencies: pip install -r requirements-ai.txt")
    print("2. Start app: python app.py")
    print("3. Visit: http://localhost:5000/ai-features")
    
    return True

def main():
    """Main integration function"""
    try:
        success = integrate_ai_features()
        
        if success:
            print("\nAI Features integration completed successfully!")
        else:
            print("\nAI Features integration failed!")
            
    except Exception as e:
        print(f"\nIntegration failed with error: {e}")

if __name__ == "__main__":
    main()

