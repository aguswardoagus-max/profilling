#!/usr/bin/env python3
"""
AI Features Integration Script
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
        print("✅ AI endpoints already integrated in app.py")
    else:
        # Add AI imports
        ai_imports = """
# AI Features Integration
try:
    from ai_api_endpoints import register_ai_endpoints
    from ai_enhancements_implementation import AIEnhancements
    AI_FEATURES_ENABLED = True
    print("✅ AI Features loaded successfully")
except ImportError as e:
    print(f"⚠️ AI Features not available: {e}")
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
        print("✅ AI Features initialized successfully")
    except Exception as e:
        print(f"⚠️ Error initializing AI Features: {e}")
        AI_FEATURES_ENABLED = False
"""
            app_content = app_content.replace(
                'app = Flask(__name__)',
                'app = Flask(__name__)' + ai_init
            )
        
        # Write updated app.py
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print("✅ AI endpoints integrated into app.py")
    
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
    
    print("✅ AI configuration file created: ai_config.py")
    
    # Create AI directories
    ai_dirs = ['ai_models', 'ai_cache', 'ai_logs', 'ai_temp']
    for dir_name in ai_dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}")
    
    # Create AI status check script
    status_check_script = """#!/usr/bin/env python3
\"\"\"
AI Features Status Check
Checks the status of AI features integration
\"\"\"

import sys
import os
from pathlib import Path

def check_ai_status():
    print("🔍 Checking AI Features Status")
    print("=" * 40)
    
    # Check files
    required_files = [
        'ai_enhancements_implementation.py',
        'ai_api_endpoints.py',
        'ai_config.py',
        'requirements-ai.txt'
    ]
    
    print("📁 Required Files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing")
    
    # Check directories
    required_dirs = ['ai_models', 'ai_cache', 'ai_logs', 'ai_temp']
    
    print("\\n📂 Required Directories:")
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}")
        else:
            print(f"  ❌ {dir_name} - Missing")
    
    # Check Python packages
    print("\\n📦 Python Packages:")
    packages = [
        'numpy', 'opencv-python', 'PIL', 'sklearn',
        'deepface', 'spacy', 'transformers'
    ]
    
    for package in packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - Not installed")
    
    # Check app.py integration
    print("\\n🔗 App Integration:")
    if os.path.exists('app.py'):
        with open('app.py', 'r') as f:
            content = f.read()
        
        if 'ai_api_endpoints' in content:
            print("  ✅ AI endpoints integrated")
        else:
            print("  ❌ AI endpoints not integrated")
        
        if 'AI_FEATURES_ENABLED' in content:
            print("  ✅ AI features flag present")
        else:
            print("  ❌ AI features flag missing")
    else:
        print("  ❌ app.py not found")
    
    print("\\n🎯 Next Steps:")
    print("1. Install AI dependencies: pip install -r requirements-ai.txt")
    print("2. Download spaCy models: python -m spacy download en_core_web_sm")
    print("3. Test AI features: python -c \"from ai_enhancements_implementation import AIEnhancements; AIEnhancements()\"")
    print("4. Start the application: python app.py")
    print("5. Visit: http://localhost:5000/ai-features")

if __name__ == "__main__":
    check_ai_status()
"""
    
    with open('check_ai_status.py', 'w', encoding='utf-8') as f:
        f.write(status_check_script)
    
    print("✅ AI status check script created: check_ai_status.py")
    
    # Create quick start guide
    quick_start_guide = """# 🚀 AI Features Quick Start Guide

## 1. Install Dependencies
```bash
pip install -r requirements-ai.txt
```

## 2. Download Language Models
```bash
python -m spacy download en_core_web_sm
```

## 3. Check AI Status
```bash
python check_ai_status.py
```

## 4. Start Application
```bash
python app.py
```

## 5. Access AI Features
- Main App: http://localhost:5000
- AI Features: http://localhost:5000/ai-features
- AI API Status: http://localhost:5000/api/ai/status

## 6. Test AI Features
- Face Analysis: Upload image and analyze
- Smart Search: Get AI-powered suggestions
- Risk Assessment: Assess person risk score
- Chatbot: Chat with AI assistant

## Troubleshooting
- If AI features don't load, check: python check_ai_status.py
- For installation issues, run: python install_ai_features.py
- Check logs in ai_logs/ directory

## Support
- Documentation: AI_IMPLEMENTATION_GUIDE.md
- Requirements: requirements-ai.txt
- Configuration: ai_config.py
"""
    
    with open('AI_QUICK_START.md', 'w', encoding='utf-8') as f:
        f.write(quick_start_guide)
    
    print("✅ Quick start guide created: AI_QUICK_START.md")
    
    print("\n🎉 AI Features Integration Completed!")
    print("\nNext Steps:")
    print("1. Install AI dependencies: pip install -r requirements-ai.txt")
    print("2. Check status: python check_ai_status.py")
    print("3. Start app: python app.py")
    print("4. Visit: http://localhost:5000/ai-features")
    
    return True

def main():
    """Main integration function"""
    try:
        success = integrate_ai_features()
        
        if success:
            print("\n✅ AI Features integration completed successfully!")
        else:
            print("\n❌ AI Features integration failed!")
            
    except Exception as e:
        print(f"\n❌ Integration failed with error: {e}")

if __name__ == "__main__":
    main()
