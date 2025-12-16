#!/usr/bin/env python3
"""
Entry point untuk Clearance Face Search Application
Menjalankan aplikasi Flask dari struktur folder yang terorganisir
"""
import sys
import os
import threading

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the Flask app
from app import app

# Import Telegram bot
try:
    from telegram_bot import run_bot
    TELEGRAM_BOT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Telegram bot tidak dapat diimport: {e}")
    print("   Bot Telegram akan dinonaktifkan")
    TELEGRAM_BOT_AVAILABLE = False


def start_telegram_bot():
    """Start Telegram bot in separate thread"""
    if TELEGRAM_BOT_AVAILABLE:
        try:
            import time
            time.sleep(2)  # Tunggu sebentar agar Flask app sudah siap
            print("🤖 Starting Telegram bot...")
            run_bot()
        except Exception as e:
            print(f"❌ Error starting Telegram bot: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    print("Starting Clearance Face Search Application...")
    print("Backend: ./backend/")
    print("Frontend: ./frontend/")
    print("Config: ./config/")
    print("Server: http://127.0.0.1:5000")
    print("Authentication: Enabled")
    print("AI Features: Ready")
    print("Reports: Available")
    
    # Start Telegram bot in background thread
    if TELEGRAM_BOT_AVAILABLE:
        bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
        bot_thread.start()
        print("Telegram Bot: ✅ Enabled")
    else:
        print("Telegram Bot: ❌ Disabled")
    
    print("-" * 50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
