#!/usr/bin/env python3
"""
Telegram Bot untuk fitur Profiling
Menggunakan API endpoints yang sudah ada tanpa mengubah logic web
"""
import os
import sys
import json
import requests
import logging
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
try:
    from database import authenticate_user, validate_session_token, UserDatabase
    db = UserDatabase()
except ImportError:
    # Fallback jika import gagal
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from database import authenticate_user, validate_session_token, UserDatabase
        db = UserDatabase()
    except ImportError:
        db = None
        logger.warning("Database tidak tersedia, fitur whitelist tidak akan berfungsi")

# Import clearance_face_search untuk login otomatis
try:
    from clearance_face_search import ensure_token, call_search, parse_people_from_response
    CLEARANCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"clearance_face_search tidak tersedia: {e}")
    CLEARANCE_AVAILABLE = False

# Import cekplat untuk cek kendaraan tanpa login
try:
    from cekplat import fetch_data, process_table_data, preprocess_address, geocode_address
    CEKPLAT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"cekplat tidak tersedia: {e}")
    CEKPLAT_AVAILABLE = False

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot API Key
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7348743638:AAFfeaHBvnCpLbZ2JnKng0iwq2FG6oF7eTw')

# Telegram Bot Owner ID (untuk akses admin)
TELEGRAM_OWNER_ID = os.getenv('TELEGRAM_OWNER_ID', '6743614528')  # Default owner ID

# Base URL untuk API (default localhost, bisa diubah via env)
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')

# Base URL untuk database khusus cek HP (jika menggunakan HTTP API)
PHONE_DB_BASE_URL = os.getenv('PHONE_DB_BASE_URL', 'http://10.1.90.243:8080')

# Konfigurasi database MySQL khusus untuk cek HP (jika menggunakan koneksi langsung)
# Default menggunakan localhost karena Flask app akan berjalan di server yang sama dengan database
PHONE_DB_HOST = os.getenv('PHONE_DB_HOST', 'localhost')
PHONE_DB_PORT = int(os.getenv('PHONE_DB_PORT', 3306))
PHONE_DB_USER = os.getenv('PHONE_DB_USER', 'root')
PHONE_DB_PASSWORD = os.getenv('PHONE_DB_PASSWORD', '')
PHONE_DB_NAME = os.getenv('PHONE_DB_NAME', 'sipudat1')

# Dictionary untuk menyimpan state user
user_states = {}
user_credentials = {}  # Untuk menyimpan username/password user
user_search_state = {}  # Untuk menyimpan state pencarian user (nama/nik/phone)
user_admin_state = {}  # Untuk menyimpan state admin (input ID, dll) - 'waiting_add_id', 'waiting_remove_id'

# Kredensial default untuk login otomatis (sama seperti clearance_face_search.py)
# Server 116 menggunakan kredensial hardcoded
DEFAULT_USERNAME = os.getenv('SERVER_116_USERNAME', 'jambi')
DEFAULT_PASSWORD = os.getenv('SERVER_116_PASSWORD', '@ab526d')

# Global token untuk login otomatis
_auto_token = None
_token_time = 0
_token_timeout = 1800  # 30 minutes


def get_main_menu_keyboard(user_id: int = None):
    """Create main menu keyboard dengan layout yang lebih bagus"""
    keyboard = [
        [
            KeyboardButton("🔍 Cari Nama"),
            KeyboardButton("🆔 Cari NIK")
        ],
        [
            KeyboardButton("📱 Cari Nomor HP"),
            KeyboardButton("🚗 Cek Plat")
        ],
        [
            KeyboardButton("📊 Laporan"),
            KeyboardButton("ℹ️ Bantuan")
        ]
    ]
    
    # Tambahkan menu admin jika owner
    if user_id is not None and is_owner(user_id):
        keyboard.append([KeyboardButton("🔐 Admin")])
    
    keyboard.append([KeyboardButton("📋 Menu Utama")])
    
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True, 
        one_time_keyboard=False,
        input_field_placeholder="Pilih menu atau ketik perintah..."
    )


async def check_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if the user is allowed to use the bot.
    If not, sends an access denied message and notifies the owner.
    Returns True if allowed, False otherwise.
    """
    user = update.effective_user
    user_id = user.id
    username = user.username or 'N/A'
    first_name = user.first_name or 'N/A'
    last_name = user.last_name or ''
    
    logger.info(f"🔒 Checking access for user_id: {user_id} ({username})")
    print(f"[TELEGRAM_BOT] 🔒 Checking access for user_id: {user_id} ({username})", file=sys.stderr)
    
    # PENTING: Cek owner TERLEBIH DAHULU sebelum cek database
    # Owner selalu diizinkan, bahkan jika database error
    owner_id = TELEGRAM_OWNER_ID
    if owner_id and str(user_id) == str(owner_id):
        logger.info(f"✅ Owner detected: {user_id} ({username}) - ALLOWING ACCESS")
        print(f"[TELEGRAM_BOT] ✅ Owner detected: {user_id} ({username}) - ALLOWING ACCESS", file=sys.stderr)
        
        # Update database jika tersedia
        if db:
            try:
                db.add_telegram_user(
                    telegram_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    is_allowed=True,
                    added_by=user_id,
                    notes='Owner'
                )
                db.update_telegram_user_last_used(user_id)
            except Exception as e:
                logger.warning(f"Error updating owner in database: {e}")
        
        return True
    
    # Jika bukan owner, cek database
    if not db:
        logger.error("❌ Database connection not available for whitelist check - BLOCKING ACCESS")
        print(f"[TELEGRAM_BOT] ❌ Database not available - BLOCKING ACCESS", file=sys.stderr)
        # Jika database tidak tersedia, BLOKIR akses untuk keamanan
        try:
            await update.message.reply_text(
                "🔒 *Akses Dibatasi*\n\n"
                "Sistem whitelist tidak tersedia saat ini.\n"
                "Silakan hubungi admin.",
                parse_mode='Markdown'
            )
        except:
            pass
        return False
    
    try:
        is_allowed = db.is_telegram_user_allowed(user_id)
        logger.info(f"🔒 User {user_id} whitelist status: {is_allowed}")
        print(f"[TELEGRAM_BOT] 🔒 User {user_id} whitelist status: {is_allowed}", file=sys.stderr)
        
        # Update user info in DB (or add if new)
        db.add_telegram_user(
            telegram_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_allowed=is_allowed
        )
        
        if is_allowed:
            db.update_telegram_user_last_used(user_id)
            logger.info(f"✅ User {user_id} access granted (whitelisted)")
            print(f"[TELEGRAM_BOT] ✅ User {user_id} access granted (whitelisted)", file=sys.stderr)
            return True
        else:
            # For non-whitelisted, non-owner users
            logger.warning(f"❌ Access DENIED for user {user_id} ({username}) - {first_name} {last_name}")
            print(f"[TELEGRAM_BOT] ❌ Access DENIED for user {user_id} ({username}) - {first_name} {last_name}", file=sys.stderr)
            
            # Send access denied message to user
            try:
                await update.message.reply_text(
                    "🔒 *Akses Dibatasi*\n\n"
                    "Anda tidak memiliki akses untuk menggunakan bot ini.\n"
                    "Silakan hubungi admin untuk mendapatkan akses.\n\n"
                    f"ID Telegram Anda: `{user_id}`",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error sending access denied message: {e}")
            
            # Notify owner
            if owner_id:
                try:
                    from telegram import Bot
                    bot = Bot(token=TELEGRAM_BOT_TOKEN)
                    await bot.send_message(
                        chat_id=int(owner_id),
                        text=(
                            f"🚨 *Notifikasi Akses Bot Baru/Ditolak* 🚨\n\n"
                            f"User baru mencoba mengakses bot:\n"
                            f"👤 *Nama:* {first_name} {last_name}\n"
                            f"📝 *Username:* @{username}\n"
                            f"🆔 *ID Telegram:* `{user_id}`\n\n"
                            f"Gunakan `/adduser {user_id}` untuk memberikan akses."
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to notify owner {owner_id}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Error during whitelist check for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        print(f"[TELEGRAM_BOT] ❌ Error during whitelist check: {e}", file=sys.stderr)
        print(f"[TELEGRAM_BOT] Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        # Jika error, BLOKIR akses untuk keamanan (kecuali owner sudah dicek di atas)
        try:
            await update.message.reply_text(
                "🔒 *Akses Dibatasi*\n\n"
                "Terjadi kesalahan saat memeriksa akses Anda.\n"
                "Silakan hubungi admin.",
                parse_mode='Markdown'
            )
        except:
            pass
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    # Cek akses user terlebih dahulu - PENTING: ini akan memblokir user yang tidak terdaftar
    if not await check_user_access(update, context):
        return
    
    user = update.effective_user
    user_id = user.id
    
    # Jika user terdaftar (sudah dicek oleh check_user_access), tampilkan menu normal
    welcome_message = (
        f"👋 *Halo {user.first_name}!*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 *BOT PROFILING*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Selamat datang! Saya dapat membantu Anda untuk:\n\n"
        "🔍 *Cari Data Orang*\n"
        "   • Cari berdasarkan Nama\n"
        "   • Cari berdasarkan NIK\n"
        "   • Cari berdasarkan Nomor HP\n\n"
        "🚗 *Cek Kendaraan*\n"
        "   • Cek data kendaraan berdasarkan nomor polisi\n\n"
        "📊 *Laporan*\n"
        "   • Lihat laporan profiling\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Gunakan tombol menu di bawah untuk memulai 👇\n\n"
        "Atau ketik `/help` untuk bantuan lebih lanjut"
    )
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(user_id)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    # Cek akses user
    if not await check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    
    help_text = (
        "📖 *BANTUAN BOT PROFILING*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *PERINTAH YANG TERSEDIA:*\n\n"
        "`/start` - Mulai bot dan tampilkan menu\n"
        "`/help` - Tampilkan bantuan ini\n"
        "`/login <username> <password>` - Login ke sistem\n"
        "`/logout` - Logout dari sistem\n"
        "`/search <type> <query>` - Cari data\n"
        "   • type: `nama`, `nik`, atau `phone`\n"
        "   • contoh: `/search nama Ahmad Hidayat`\n"
        "`/reports` - Lihat laporan profiling\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *CARA MENGGUNAKAN MENU:*\n\n"
        "1️⃣ Klik tombol menu yang diinginkan\n"
        "2️⃣ Ikuti instruksi yang muncul\n"
        "3️⃣ Ketik data yang diminta\n"
        "4️⃣ Bot akan menampilkan hasil\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *FITUR YANG TERSEDIA:*\n\n"
        "🔍 *Cari Nama* - Cari data berdasarkan nama lengkap\n"
        "🆔 *Cari NIK* - Cari data berdasarkan NIK (16 digit)\n"
        "📱 *Cari Nomor HP* - Cari data berdasarkan nomor HP\n"
        "🚗 *Cek Plat* - Cek data kendaraan berdasarkan nomor polisi\n"
        "📊 *Laporan* - Lihat laporan profiling yang tersimpan\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 *Tips:* Anda juga bisa langsung mengetik nama, NIK, atau nomor polisi tanpa klik menu!"
    )
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(update.effective_user.id)
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /login command"""
    # Cek akses user
    if not await check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format salah!\n"
            "Gunakan: /login <username> <password>\n"
            "Contoh: /login admin password123"
        )
        return
    
    username = context.args[0]
    password = context.args[1]
    
    try:
        # Authenticate user menggunakan database
        auth_result = authenticate_user(username, password, ip_address=None, user_agent='TelegramBot')
        
        if auth_result:
            user_data = auth_result.get('user', {})
            session_token = auth_result.get('session_token', '')
            
            user_credentials[user_id] = {
                'username': username,
                'password': password,
                'user_data': user_data,
                'session_token': session_token
            }
            user_states[user_id] = 'logged_in'
            
            await update.message.reply_text(
                f"✅ Login berhasil!\n"
                f"Selamat datang, {user_data.get('username', username)}"
            )
        else:
            await update.message.reply_text("❌ Username atau password salah!")
            
    except Exception as e:
        logger.error(f"Error in login: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /logout command"""
    user_id = update.effective_user.id
    
    if user_id in user_credentials:
        del user_credentials[user_id]
    if user_id in user_states:
        del user_states[user_id]
    
    await update.message.reply_text("✅ Logout berhasil!")


def get_auto_token():
    """Get token automatically using ensure_token (same as clearance_face_search.py)"""
    global _auto_token, _token_time
    
    import time
    
    # Check if token is still valid (within timeout)
    current_time = time.time()
    if _auto_token and (current_time - _token_time) < _token_timeout:
        return _auto_token
    
    # Get new token using ensure_token (automatic login)
    if CLEARANCE_AVAILABLE:
        try:
            # Use default credentials (same as clearance_face_search.py)
            # Server 116 uses hardcoded credentials: jambi/@ab526d
            token = ensure_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, force_refresh=False)
            _auto_token = token
            _token_time = current_time
            logger.info(f"✅ Auto login berhasil menggunakan kredensial: {DEFAULT_USERNAME}")
            return token
        except Exception as e:
            logger.error(f"Error getting auto token: {e}")
            return None
    else:
        logger.error("clearance_face_search tidak tersedia untuk auto login")
        return None


async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button clicks and text input"""
    user_id = update.effective_user.id
    text = update.message.text or ""
    
    # Log untuk debugging
    logger.info(f"📱 Menu button/text received: '{text}' from user {user_id}")
    print(f"[TELEGRAM_BOT] 📱 Menu button/text received: '{text}' from user {user_id}", file=sys.stderr)
    
    # Handle Admin button khusus (skip check_user_access untuk owner)
    if text == "🔐 Admin":
        user_search_state[user_id] = None
        user_admin_state[user_id] = None  # Reset admin state
        logger.info(f"🔐 Admin button clicked by user {user_id}")
        print(f"[TELEGRAM_BOT] 🔐 Admin button clicked by user {user_id}", file=sys.stderr)
        
        # Cek apakah owner - dengan logging detail
        owner_check = is_owner(user_id)
        logger.info(f"Owner check result: {owner_check}")
        print(f"[TELEGRAM_BOT] Owner check result: {owner_check}", file=sys.stderr)
        
        if not owner_check:
            logger.warning(f"User {user_id} is NOT owner, blocking access")
            print(f"[TELEGRAM_BOT] User {user_id} is NOT owner, blocking access", file=sys.stderr)
            await update.message.reply_text(
                "❌ *Akses Ditolak*\n\n"
                "Anda tidak memiliki akses ke menu admin.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Owner bisa langsung akses
        logger.info(f"User {user_id} is owner, calling admin_menu")
        print(f"[TELEGRAM_BOT] User {user_id} is owner, calling admin_menu", file=sys.stderr)
        try:
            await admin_menu(update, context)
            logger.info(f"admin_menu completed for user {user_id}")
            print(f"[TELEGRAM_BOT] admin_menu completed for user {user_id}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Error calling admin_menu: {e}")
            import traceback
            traceback.print_exc()
            print(f"[TELEGRAM_BOT] ❌ ERROR calling admin_menu: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            try:
                await update.message.reply_text(
                    f"❌ *Error:* {str(e)}\n\n"
                    "Silakan coba lagi atau gunakan command `/admin`.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard(user_id)
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {e2}")
                print(f"[TELEGRAM_BOT] Error sending error message: {e2}", file=sys.stderr)
        return
    
    # Cek akses user untuk menu lainnya
    if not await check_user_access(update, context):
        return
    
    # Handle menu buttons
    if text == "🔍 Cari Nama":
        user_search_state[user_id] = 'waiting_name'
        await update.message.reply_text(
            "🔍 *Cari Berdasarkan Nama*\n\n"
            "Ketik nama lengkap yang ingin dicari:\n\n"
            "Contoh:\n"
            "• Ahmad Hidayat\n"
            "• agus putra jambi\n"
            "• budi santoso jakarta\n\n"
            "💡 *Tips:* Tambahkan nama kota di akhir untuk filter lokasi\n\n"
            "Atau: `/search nama Ahmad Hidayat`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Ketik nama sekarang 👇",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif text == "🆔 Cari NIK":
        user_search_state[user_id] = 'waiting_nik'
        await update.message.reply_text(
            "🆔 *Cari Berdasarkan NIK*\n\n"
            "Ketik NIK yang ingin dicari:\n\n"
            "Contoh: 1505041107830002\n"
            "Atau: `/search nik 1505041107830002`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Ketik NIK sekarang 👇",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif text == "📱 Cari Nomor HP":
        user_search_state[user_id] = 'waiting_phone'
        await update.message.reply_text(
            "📱 *Cari Berdasarkan Nomor HP*\n\n"
            "Ketik nomor HP yang ingin dicari:\n\n"
            "Contoh: 081234567890\n"
            "Atau: `/search phone 081234567890`\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Ketik nomor HP sekarang 👇",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif text == "🚗 Cek Plat":
        user_search_state[user_id] = 'waiting_plat'
        logger.info(f"User {user_id} selected Cek Plat menu, state set to waiting_plat")
        await update.message.reply_text(
            "🚗 *Cek Nomor Polisi Kendaraan*\n\n"
            "Ketik nomor polisi yang ingin dicek:\n\n"
            "Contoh: BH 1234 AB\n"
            "Atau: BH1234AB\n"
            "Atau: BH 1\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Ketik nomor polisi sekarang 👇\n\n"
            "💡 *Catatan:* Sistem akan mencari data dari jambisamsat.net",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    elif text == "📊 Laporan":
        user_search_state[user_id] = None
        await reports(update, context)
    elif text == "ℹ️ Bantuan":
        user_search_state[user_id] = None
        await help_command(update, context)
    elif text == "📋 Menu" or text == "📋 Menu Utama":
        user_search_state[user_id] = None
        await start(update, context)
    else:
        # Handle admin state (input ID untuk add/remove user)
        admin_state = user_admin_state.get(user_id)
        if admin_state:
            if admin_state == 'waiting_add_id':
                # User sedang menunggu input ID untuk add
                try:
                    target_id = int(text.strip())
                    target_user = db.get_telegram_user(target_id) if db else None
                    
                    if db:
                        if target_user:
                            success = db.add_telegram_user(
                                telegram_id=target_id,
                                username=target_user.get('username'),
                                first_name=target_user.get('first_name'),
                                last_name=target_user.get('last_name'),
                                is_allowed=True,
                                added_by=user_id,
                                notes='Added by admin via menu input'
                            )
                        else:
                            success = db.add_telegram_user(
                                telegram_id=target_id,
                                is_allowed=True,
                                added_by=user_id,
                                notes='Added by admin via menu input'
                            )
                        
                        if success:
                            # Notify user
                            try:
                                from telegram import Bot
                                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                                await bot.send_message(
                                    chat_id=target_id,
                                    text=(
                                        "✅ *Akses Diberikan*\n\n"
                                        "Anda sekarang dapat menggunakan bot ini!\n\n"
                                        "Ketik `/start` untuk memulai."
                                    ),
                                    parse_mode='Markdown'
                                )
                            except:
                                pass
                            
                            user_admin_state[user_id] = None
                            await update.message.reply_text(
                                f"✅ *User Ditambahkan*\n\n"
                                f"🆔 *ID:* `{target_id}`\n"
                                f"✅ Status: *Diizinkan*\n\n"
                                f"User sekarang dapat menggunakan bot.",
                                parse_mode='Markdown',
                                reply_markup=get_main_menu_keyboard(user_id)
                            )
                        else:
                            await update.message.reply_text(
                                "❌ *Gagal menambahkan user*\n\n"
                                "Terjadi kesalahan saat menambahkan user ke database.",
                                parse_mode='Markdown',
                                reply_markup=get_main_menu_keyboard(user_id)
                            )
                    else:
                        await update.message.reply_text(
                            "❌ Database tidak tersedia",
                            parse_mode='Markdown',
                            reply_markup=get_main_menu_keyboard(user_id)
                        )
                except ValueError:
                    await update.message.reply_text(
                        "❌ *ID Tidak Valid*\n\n"
                        "ID Telegram harus berupa angka.\n\n"
                        "Ketik ID yang benar atau ketik `/admin` untuk kembali ke menu.",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                except Exception as e:
                    logger.error(f"Error adding user: {e}")
                    user_admin_state[user_id] = None
                    await update.message.reply_text(
                        f"❌ *Error:* {str(e)}",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                return
            elif admin_state == 'waiting_remove_id':
                # User sedang menunggu input ID untuk remove
                try:
                    target_id = int(text.strip())
                    success = db.remove_telegram_user(target_id) if db else False
                    
                    if success:
                        user_admin_state[user_id] = None
                        await update.message.reply_text(
                            f"✅ *User Dihapus*\n\n"
                            f"🆔 *ID:* `{target_id}`\n"
                            f"❌ Status: *Akses Dicabut*\n\n"
                            f"User tidak dapat menggunakan bot lagi.",
                            parse_mode='Markdown',
                            reply_markup=get_main_menu_keyboard(user_id)
                        )
                    else:
                        await update.message.reply_text(
                            "❌ *Gagal menghapus user*\n\n"
                            "Terjadi kesalahan saat menghapus user dari database.",
                            parse_mode='Markdown',
                            reply_markup=get_main_menu_keyboard(user_id)
                        )
                except ValueError:
                    await update.message.reply_text(
                        "❌ *ID Tidak Valid*\n\n"
                        "ID Telegram harus berupa angka.\n\n"
                        "Ketik ID yang benar atau ketik `/admin` untuk kembali ke menu.",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                except Exception as e:
                    logger.error(f"Error removing user: {e}")
                    user_admin_state[user_id] = None
                    await update.message.reply_text(
                        f"❌ *Error:* {str(e)}",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                return
        
        # Handle text input based on current state
        current_state = user_search_state.get(user_id)
        query = text.strip()
        
        if current_state == 'waiting_name':
            # User is waiting to input name - gunakan smart parsing
            if len(query) > 2:
                user_search_state[user_id] = None
                # Smart parse untuk deteksi lokasi
                parsed = smart_parse_search_query(query)
                if parsed['tempat_lahir']:
                    # Inform user bahwa lokasi terdeteksi
                    await update.message.reply_text(
                        f"🔍 *Pencarian Cerdas*\n\n"
                        f"📝 *Nama:* {parsed['name']}\n"
                        f"📍 *Lokasi:* {parsed['tempat_lahir'].title()}\n\n"
                        f"Mencari data...",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                context.args = ['nama', query]
                await search(update, context)
            else:
                await update.message.reply_text(
                    "❌ Nama terlalu pendek. Minimal 3 karakter.\n\n"
                    "Ketik nama lengkap yang ingin dicari:\n"
                    "💡 *Tips:* Tambahkan nama kota di akhir untuk filter lokasi\n"
                    "Contoh: agus putra jambi",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        elif current_state == 'waiting_nik':
            # User is waiting to input NIK
            if query.isdigit() and len(query) == 16:
                user_search_state[user_id] = None
                context.args = ['nik', query]
                await search(update, context)
            else:
                await update.message.reply_text(
                    "❌ Format NIK salah!\n\n"
                    "NIK harus 16 digit angka.\n"
                    "Contoh: 1505041107830002\n\n"
                    "Ketik NIK yang benar:",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        elif current_state == 'waiting_phone':
            # User is waiting to input phone number - LANGSUNG ke check_phone_from_database
            logger.info(f"User {user_id} in waiting_phone state, input: {query}")
            # Remove spaces and non-digit characters
            phone_clean = ''.join(filter(str.isdigit, query))
            if len(phone_clean) >= 10:
                user_search_state[user_id] = None
                logger.info(f"Calling check_phone_from_database with: {phone_clean}")
                await check_phone_from_database(update, context, phone_clean)
            else:
                await update.message.reply_text(
                    "❌ Format nomor HP salah!\n\n"
                    "Nomor HP minimal 10 digit.\n"
                    "Contoh: 081234567890\n\n"
                    "Ketik nomor HP yang benar:",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        elif current_state == 'waiting_plat':
            # User is waiting to input plate number - LANGSUNG ke check_plate
            logger.info(f"User {user_id} in waiting_plat state, input: {query}")
            # Clean and validate plate number
            plat_clean = query.upper().replace(' ', '').strip()
            if len(plat_clean) >= 3:  # Minimum format: AB1
                user_search_state[user_id] = None
                logger.info(f"Calling check_plate with: {plat_clean}")
                await check_plate(update, context, plat_clean)
            else:
                await update.message.reply_text(
                    "❌ Format nomor polisi salah!\n\n"
                    "Nomor polisi minimal 3 karakter.\n"
                    "Contoh: BH 1234 AB atau BH1234AB\n\n"
                    "Ketik nomor polisi yang benar:",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        else:
            # No active state - try to auto-detect
            if len(query) > 2:
                # PRIORITAS 1: Check if it looks like plate number
                # Pattern untuk nomor polisi Indonesia: 2-3 huruf + 1-4 angka + 0-3 huruf (opsional)
                # Contoh: BH 1, BH 1234, BH 1234 AB, BH1234AB
                import re
                query_upper = query.upper().strip()
                query_clean = query_upper.replace(' ', '')
                
                # Pattern yang lebih fleksibel: 2-3 huruf + 1-4 angka + 0-3 huruf (opsional)
                plate_pattern = re.compile(r'^[A-Z]{2,3}\s*\d{1,4}\s*[A-Z]{0,3}$')
                
                # Check jika mengandung huruf dan angka (karakteristik nomor polisi)
                has_letters = any(c.isalpha() for c in query)
                has_digits = any(c.isdigit() for c in query)
                
                # Jika match pattern atau mengandung huruf+angka dengan format yang mirip nomor polisi
                if plate_pattern.match(query_upper) or (has_letters and has_digits and len(query_clean) >= 3 and len(query_clean) <= 12):
                    # Cek lebih spesifik: harus dimulai dengan huruf (kode daerah)
                    if query_upper[0].isalpha():
                        # Ini kemungkinan besar nomor polisi
                        plat_clean = query_clean
                        logger.info(f"Auto-detected as plate number: {query} -> {plat_clean}")
                        await check_plate(update, context, plat_clean)
                        return
                
                # PRIORITAS 2: Check if it looks like NIK (16 digits)
                if query.isdigit() and len(query) == 16:
                    context.args = ['nik', query]
                    await search(update, context)
                    return
                
                # PRIORITAS 3: Check if it looks like phone number (10+ digits)
                elif query.replace(' ', '').replace('-', '').isdigit() and len(query.replace(' ', '').replace('-', '')) >= 10:
                    phone_clean = ''.join(filter(str.isdigit, query))
                    logger.info(f"Auto-detected as phone number: {query} -> {phone_clean}")
                    await check_phone_from_database(update, context, phone_clean)
                    return
                
                # PRIORITAS 4: Assume it's a name search - gunakan smart parsing
                else:
                    # Smart parse untuk deteksi lokasi
                    parsed = smart_parse_search_query(query)
                    if parsed['tempat_lahir']:
                        # Inform user bahwa lokasi terdeteksi
                        await update.message.reply_text(
                            f"🔍 *Pencarian Cerdas*\n\n"
                            f"📝 *Nama:* {parsed['name']}\n"
                            f"📍 *Lokasi:* {parsed['tempat_lahir'].title()}\n\n"
                            f"Mencari data...",
                            parse_mode='Markdown',
                            reply_markup=get_main_menu_keyboard(user_id)
                        )
                    context.args = ['nama', query]
                    await search(update, context)
                    return
            else:
                # Unknown input, show help
                await update.message.reply_text(
                    "❓ *Tidak mengerti perintah*\n\n"
                    "Gunakan tombol menu untuk memilih jenis pencarian:\n"
                    "• 🔍 Cari Nama\n"
                    "• 🆔 Cari NIK\n"
                    "• 📱 Cari Nomor HP\n\n"
                    "Atau ketik perintah:\n"
                    "`/search nama [nama]`\n"
                    "`/search nik [nik]`\n"
                    "`/search phone [nomor]`",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard(user_id)
                )


def smart_parse_search_query(query: str):
    """
    Parse query secara cerdas untuk memisahkan nama dan lokasi
    Contoh: "agus putra jambi" -> nama: "agus putra", tempat_lahir: "jambi"
    """
    # Daftar kota/kabupaten umum di Indonesia (prioritas Jambi dan sekitarnya)
    common_locations = [
        'jambi', 'jakarta', 'bandung', 'surabaya', 'medan', 'semarang', 'makassar', 'palembang',
        'pekanbaru', 'padang', 'bengkulu', 'lampung', 'banten', 'yogyakarta', 'denpasar',
        'banjarmasin', 'pontianak', 'samarinda', 'manado', 'ambon', 'jayapura', 'kupang',
        'tanjung pinang', 'batam', 'palu', 'kendari', 'ternate', 'mataram', 'gorontalo',
        'jambi selatan', 'jambi timur', 'jambi utara', 'jambi barat', 'muaro jambi',
        'tanjung jabung', 'tanjung jabung timur', 'tanjung jabung barat', 'bunga',
        'tebo', 'sarolangun', 'merangin', 'bungo', 'kerinci', 'sungaipenuh',
        'kota jambi', 'kabupaten jambi'
    ]
    
    query_lower = query.lower().strip()
    words = query_lower.split()
    
    if len(words) < 2:
        # Query terlalu pendek, tidak ada lokasi
        return {'name': query, 'tempat_lahir': ''}
    
    # Cek apakah kata terakhir atau 2 kata terakhir adalah lokasi
    # Cek 2 kata terakhir (untuk "kota jambi", "jambi selatan", dll)
    if len(words) >= 2:
        last_two = ' '.join(words[-2:])
        if last_two in common_locations:
            name = ' '.join(words[:-2]).strip()
            return {'name': name if name else query, 'tempat_lahir': last_two}
    
    # Cek 1 kata terakhir
    last_word = words[-1]
    if last_word in common_locations:
        name = ' '.join(words[:-1]).strip()
        return {'name': name if name else query, 'tempat_lahir': last_word}
    
    # Jika tidak ditemukan lokasi, return semua sebagai nama
    return {'name': query, 'tempat_lahir': ''}


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search command - menggunakan login otomatis seperti clearance_face_search.py"""
    # Cek akses user
    if not await check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    
    # Handle both command args and direct text input
    if context.args and len(context.args) >= 2:
        search_type = context.args[0].lower()
        search_value = ' '.join(context.args[1:])
    elif update.message.text and not update.message.text.startswith('/'):
        # Direct text input (from menu button)
        query = update.message.text.strip()
        if query.isdigit() and len(query) == 16:
            search_type = 'nik'
            search_value = query
        else:
            search_type = 'nama'
            search_value = query
    else:
        await update.message.reply_text(
            "❌ Format salah!\n"
            "Gunakan:\n"
            "/search nama <nama>\n"
            "/search nik <nik>\n"
            "/search phone <nomor_hp>\n\n"
            "Atau gunakan tombol menu di bawah 👇",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    if search_type not in ['nama', 'nik', 'phone']:
        await update.message.reply_text(
            "❌ Tipe pencarian tidak valid!\n"
            "Gunakan: nama, nik, atau phone",
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    try:
        await update.message.reply_text(
            "🔍 *Mencari data...*\n"
            "Mohon tunggu sebentar...",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        # Get token automatically (login otomatis seperti clearance_face_search.py)
        if not CLEARANCE_AVAILABLE:
            await update.message.reply_text(
                "❌ Sistem pencarian tidak tersedia",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        token = get_auto_token()
        if not token:
            await update.message.reply_text(
                "❌ Gagal mendapatkan token otomatis",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Smart parsing untuk pencarian nama (deteksi lokasi)
        parsed_query = None
        if search_type == 'nama':
            parsed_query = smart_parse_search_query(search_value)
            logger.info(f"Smart parse result: name='{parsed_query['name']}', tempat_lahir='{parsed_query['tempat_lahir']}'")
            if parsed_query['tempat_lahir']:
                print(f"[TELEGRAM_BOT] 🔍 Smart search: name='{parsed_query['name']}', location='{parsed_query['tempat_lahir']}'", file=sys.stderr)
        
        # Prepare search parameters (sama seperti clearance_face_search.py)
        params = {
            "name": "",
            "nik": "",
            "family_cert_number": "",
            "tempat_lahir": "",
            "tanggal_lahir": "",
            "no_prop": "",
            "no_kab": "",
            "no_kec": "",
            "no_desa": "",
            "page": "1",
            "limit": "100"
        }
        
        if search_type == 'nama':
            if parsed_query:
                params['name'] = parsed_query['name']
                params['tempat_lahir'] = parsed_query['tempat_lahir']
            else:
                params['name'] = search_value
        elif search_type == 'nik':
            params['nik'] = search_value
        elif search_type == 'phone':
            # Untuk phone search, kita perlu menggunakan API endpoint khusus
            # Tapi untuk sekarang, kita gunakan call_search dengan name
            params['name'] = search_value
        
        # Call search menggunakan call_search (sama seperti clearance_face_search.py)
        # PENTING: username/password diabaikan karena server 116 menggunakan kredensial hardcoded
        result = call_search(token, params, username=None, password=None)
        
        # Parse results menggunakan parse_people_from_response
        people = parse_people_from_response(result) if CLEARANCE_AVAILABLE else []
        
        if not people:
            await update.message.reply_text(
                "❌ Data tidak ditemukan",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Filter hasil berdasarkan lokasi jika tempat_lahir terdeteksi (PENTING: Filter KETAT)
        if parsed_query and parsed_query.get('tempat_lahir'):
            location_filter = parsed_query['tempat_lahir'].lower()
            original_count = len(people)
            filtered_people = []
            
            logger.info(f"🔍 Filtering results by location: '{location_filter}' (original: {original_count} results)")
            print(f"[TELEGRAM_BOT] 🔍 Filtering results by location: '{location_filter}' (original: {original_count} results)", file=sys.stderr)
            
            for person in people:
                if isinstance(person, dict):
                    # Cek semua field yang mungkin mengandung lokasi
                    alamat = (person.get('alamat') or person.get('address') or person.get('alamat_lengkap') or '').lower()
                    tempat_lahir = (person.get('tempat_lahir') or person.get('birth_place') or person.get('tempat_lahir_lengkap') or '').lower()
                    provinsi = (person.get('provinsi') or person.get('province') or person.get('nama_provinsi') or '').lower()
                    kota = (person.get('kota') or person.get('city') or person.get('nama_kota') or '').lower()
                    kabupaten = (person.get('kabupaten') or person.get('regency') or person.get('nama_kabupaten') or '').lower()
                    kecamatan = (person.get('kecamatan') or person.get('district') or person.get('nama_kecamatan') or '').lower()
                    kelurahan = (person.get('kelurahan') or person.get('village') or person.get('nama_kelurahan') or '').lower()
                    
                    # Gabungkan semua field lokasi untuk pencarian
                    all_location_text = f"{alamat} {tempat_lahir} {provinsi} {kota} {kabupaten} {kecamatan} {kelurahan}".strip()
                    
                    # Cek apakah lokasi cocok dengan filter (harus ada di salah satu field)
                    location_match = (
                        location_filter in alamat or
                        location_filter in tempat_lahir or
                        location_filter in provinsi or
                        location_filter in kota or
                        location_filter in kabupaten or
                        location_filter in kecamatan or
                        location_filter in kelurahan or
                        location_filter in all_location_text
                    )
                    
                    if location_match:
                        filtered_people.append(person)
                        person_name = person.get('full_name') or person.get('name', 'Unknown')
                        logger.debug(f"✅ Match: {person_name} - Location '{location_filter}' found in data")
            
            if filtered_people:
                people = filtered_people
                logger.info(f"✅ Filtered results: {original_count} -> {len(people)} (location: {location_filter})")
                print(f"[TELEGRAM_BOT] ✅ Filtered results: {original_count} -> {len(people)} (location: {location_filter})", file=sys.stderr)
                
                # Inform user bahwa hasil sudah difilter
                if len(people) < original_count:
                    await update.message.reply_text(
                        f"🔍 *Hasil Difilter*\n\n"
                        f"📍 *Lokasi:* {parsed_query['tempat_lahir'].title()}\n"
                        f"📊 *Hasil:* {len(people)} dari {original_count} data\n\n"
                        f"Menampilkan hanya data yang sesuai lokasi...",
                        parse_mode='Markdown',
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
            else:
                # Jika tidak ada yang match, tampilkan semua tapi dengan peringatan
                logger.warning(f"⚠️ No results match location filter: {location_filter}, showing all {original_count} results")
                print(f"[TELEGRAM_BOT] ⚠️ No results match location filter: {location_filter}, showing all {original_count} results", file=sys.stderr)
                await update.message.reply_text(
                    f"⚠️ *Tidak ada hasil yang sesuai lokasi*\n\n"
                    f"📍 *Lokasi yang dicari:* {parsed_query['tempat_lahir'].title()}\n"
                    f"📊 Menampilkan semua {original_count} hasil tanpa filter lokasi...",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard(user_id)
                )
        
        # Enrich people dengan family data jika tersedia
        # Import get_family_data dari app.py jika tersedia
        print(f"[TELEGRAM_BOT] Starting family data enrichment for {len(people)} people...", file=sys.stderr)
        try:
            import os
            # Add backend directory to path if not already there
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            
            from app import get_family_data
            print(f"[TELEGRAM_BOT] ✅ Successfully imported get_family_data", file=sys.stderr)
            
            logger.info(f"🔍 Enriching {len(people)} people with family data...")
            print(f"[TELEGRAM_BOT] 🔍 Enriching {len(people)} people with family data...", file=sys.stderr)
            enriched_count = 0
            
            for idx, person in enumerate(people, 1):
                if isinstance(person, dict):
                    nik = person.get('ktp_number') or person.get('nik')
                    nkk = person.get('family_cert_number') or person.get('nkk') or person.get('nomor_kk') or person.get('family_card_number')
                    person_name = person.get('full_name') or person.get('name', 'Unknown')
                    
                    if nik:
                        try:
                            logger.info(f"📋 [{idx}/{len(people)}] Getting family data for: {person_name} (NIK: {nik}, NKK: {nkk or 'None'})")
                            print(f"[TELEGRAM_BOT] 📋 [{idx}/{len(people)}] Getting family data for: {person_name} (NIK: {nik}, NKK: {nkk or 'None'})", file=sys.stderr)
                            
                            # Coba ambil family data
                            family_data = get_family_data(nik, nkk, token, person)
                            if family_data:
                                person['family_data'] = family_data
                                anggota_count = len(family_data.get('anggota_keluarga', []))
                                enriched_count += 1
                                logger.info(f"✅ [{idx}/{len(people)}] Added family data for {person_name}: {anggota_count} members")
                                print(f"[TELEGRAM_BOT] ✅ [{idx}/{len(people)}] Added family data for {person_name}: {anggota_count} members", file=sys.stderr)
                                
                                # Log detail anggota keluarga
                                if anggota_count > 0:
                                    for i, member in enumerate(family_data.get('anggota_keluarga', [])[:3], 1):
                                        logger.info(f"   - Member {i}: {member.get('nama', 'N/A')} ({member.get('hubungan', 'N/A')})")
                                        print(f"[TELEGRAM_BOT]    - Member {i}: {member.get('nama', 'N/A')} ({member.get('hubungan', 'N/A')})", file=sys.stderr)
                            else:
                                logger.info(f"⚠️ [{idx}/{len(people)}] No family data found for NIK: {nik}")
                                print(f"[TELEGRAM_BOT] ⚠️ [{idx}/{len(people)}] No family data found for NIK: {nik}", file=sys.stderr)
                        except Exception as e:
                            logger.warning(f"❌ [{idx}/{len(people)}] Failed to get family data for NIK {nik}: {e}")
                            print(f"[TELEGRAM_BOT] ❌ [{idx}/{len(people)}] Failed to get family data for NIK {nik}: {e}", file=sys.stderr)
                            import traceback
                            traceback.print_exc()
                    else:
                        logger.warning(f"⚠️ [{idx}/{len(people)}] No NIK found for person: {person_name}")
                        print(f"[TELEGRAM_BOT] ⚠️ [{idx}/{len(people)}] No NIK found for person: {person_name}", file=sys.stderr)
            
            logger.info(f"✅ Family data enrichment complete: {enriched_count}/{len(people)} people enriched")
            print(f"[TELEGRAM_BOT] ✅ Family data enrichment complete: {enriched_count}/{len(people)} people enriched", file=sys.stderr)
        except ImportError as e:
            logger.warning(f"⚠️ get_family_data not available: {e}, skipping family data enrichment")
            print(f"[TELEGRAM_BOT] ⚠️ get_family_data not available: {e}", file=sys.stderr)
        except Exception as e:
            logger.error(f"❌ Error enriching family data: {e}")
            print(f"[TELEGRAM_BOT] ❌ Error enriching family data: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
        
        # Send results (pesan filter sudah dikirim di atas jika ada)
        await send_search_results_from_people(update, people)
            
    except Exception as e:
        logger.error(f"Error in search: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def check_plate(update: Update, context: ContextTypes.DEFAULT_TYPE, no_polisi: str):
    """Handle plate number check - menggunakan logic dari cekplat.py langsung tanpa login"""
    # Cek akses user
    if not await check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    
    try:
        await update.message.reply_text(
            "🚗 *Mencari data kendaraan...*\n"
            "Mohon tunggu sebentar...",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        # Check if cekplat module is available
        if not CEKPLAT_AVAILABLE:
            await update.message.reply_text(
                "❌ *Modul cekplat tidak tersedia*\n\n"
                "Fitur cek plat tidak dapat digunakan saat ini.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Fetch data langsung dari jambisamsat.net (tidak perlu login)
        logger.info(f"Fetching data for plate: {no_polisi}")
        html = fetch_data(no_polisi)
        
        if not html:
            await update.message.reply_text(
                "❌ *Gagal mengambil data dari server*\n\n"
                "Server jambisamsat.net tidak dapat diakses atau nomor polisi tidak valid.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Process table data
        table_data = process_table_data(html)
        
        if not table_data:
            await update.message.reply_text(
                "❌ *Data tidak ditemukan*\n\n"
                "Nomor polisi yang Anda cari tidak ditemukan di database.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Extract data from table_data - ambil SEMUA data yang tersedia
        extracted_data = {}
        alamat = None
        
        # Simpan semua data dari table_data untuk ditampilkan lengkap
        all_data = {}
        for label, value in table_data:
            label_original = label.strip()
            label_clean = label_original.lower()
            all_data[label_original] = value  # Simpan dengan label asli untuk ditampilkan
            
            # Extract untuk keperluan khusus
            if 'nama' in label_clean and 'pemilik' in label_clean:
                extracted_data['nama_pemilik'] = value
            elif 'alamat' in label_clean:
                extracted_data['alamat'] = value
                alamat = value
            elif 'merk' in label_clean:
                extracted_data['merk_kendaraan'] = value
            elif 'type' in label_clean or 'tipe' in label_clean:
                extracted_data['type_kendaraan'] = value
            elif 'model' in label_clean:
                extracted_data['model_kendaraan'] = value
            elif 'tahun' in label_clean:
                extracted_data['tahun_pembuatan'] = value
            elif 'warna' in label_clean:
                extracted_data['warna_kendaraan'] = value
            elif 'rangka' in label_clean:
                extracted_data['no_rangka'] = value
            elif 'mesin' in label_clean:
                extracted_data['no_mesin'] = value
            elif 'silinder' in label_clean or 'cc' in label_clean:
                extracted_data['silinder'] = value
            elif 'bahan' in label_clean and 'bakar' in label_clean:
                extracted_data['bahan_bakar'] = value
            elif 'stnk' in label_clean:
                extracted_data['masa_berlaku_stnk'] = value
            elif 'pajak' in label_clean or 'pkb' in label_clean:
                extracted_data['masa_berlaku_pajak'] = value
            elif 'status' in label_clean:
                extracted_data['status_kendaraan'] = value
        
        # Geocode address if available
        coordinates = (None, None)
        accuracy_score = 0.0
        accuracy_details = []
        display_name = ""
        
        if alamat:
            try:
                processed_address = preprocess_address(alamat)
                lat, lon, acc_score, acc_details, disp_name = geocode_address(alamat)
                coordinates = (lat, lon) if lat and lon else (None, None)
                accuracy_score = acc_score
                accuracy_details = acc_details
                display_name = disp_name
                logger.info(f"Geocoded address: {alamat} -> {coordinates}, accuracy: {accuracy_score}")
            except Exception as e:
                logger.warning(f"Geocoding failed: {e}")
        
        # Build message dengan SEMUA informasi yang tersedia
        message = f"🚗 *DATA KENDARAAN*\n"
        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"🔢 *Nomor Polisi:* {no_polisi}\n\n"
        
        # Tampilkan SEMUA data dari table_data secara lengkap
        if all_data:
            # Tampilkan semua field yang ada, dengan format yang rapi
            for label, value in all_data.items():
                if value and str(value).strip():  # Hanya tampilkan jika ada value
                    # Format label dengan emoji yang sesuai
                    label_upper = label.upper()
                    emoji = "👤" if "NAMA" in label_upper and "PEMILIK" in label_upper else \
                            "🏠" if "ALAMAT" in label_upper else \
                            "🏭" if "MEREK" in label_upper else \
                            "🚙" if "MODEL" in label_upper or "TIPE" in label_upper or "TYPE" in label_upper else \
                            "📋" if "JENIS" in label_upper else \
                            "📅" if "TAHUN" in label_upper or "TGL" in label_upper else \
                            "🔩" if "CC" in label_upper else \
                            "🎨" if "WARNA" in label_upper else \
                            "💰" if "PKB" in label_upper or "PAJAK" in label_upper or "TARIF" in label_upper or "TOTAL" in label_upper or "PEMUTIHAN" in label_upper or "SWDKLJ" in label_upper or "SWDKLLJ" in label_upper or "PNBP" in label_upper else \
                            "📍" if "LOKASI" in label_upper else \
                            "📜" if "STNK" in label_upper else \
                            "•"
                    message += f"{emoji} *{label}:* {value}\n"
        
        # Add coordinates and geocoding info if available
        if coordinates[0] and coordinates[1]:
            message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📍 *Koordinat:*\n"
            message += f"   {coordinates[0]}, {coordinates[1]}\n"
            if accuracy_score > 0:
                message += f"\n*Akurasi Geokoding:* {accuracy_score:.1f}%\n"
            if display_name:
                message += f"*Lokasi Lengkap:* {display_name}\n"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Error in check_plate: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


def parse_html_table_response(html_content: str, phone_number: str):
    """Parse HTML table response to extract phone data from phpMyAdmin"""
    try:
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # PRIORITAS: Hanya cari tabel dengan class 'table_results' (spesifik phpMyAdmin hasil query)
        # Skip semua tabel lainnya untuk menghindari parsing menu/settings
        result_tables = soup.find_all('table', class_=re.compile(r'table_results', re.I))
        
        logger.info(f"Found {len(result_tables)} tables with 'table_results' class")
        
        # Jika tidak ada, coba cari di dalam div hasil query phpMyAdmin
        if not result_tables:
            result_divs = soup.find_all(['div'], class_=re.compile(r'sqlqueryresults|result_query|table-container', re.I))
            logger.info(f"Found {len(result_divs)} divs with query results class")
            for div in result_divs:
                # Cari tabel dengan class 'table_results' di dalam div hasil query
                tables = div.find_all('table', class_=re.compile(r'table_results', re.I))
                result_tables.extend(tables)
        
        # Jika masih tidak ada, coba cari semua tabel dan filter berdasarkan struktur
        if not result_tables:
            logger.info("No table_results found, trying to find all tables and filter by structure...")
            all_tables = soup.find_all('table')
            logger.info(f"Found {len(all_tables)} total tables in HTML")
            
            # Cari tabel yang memiliki tbody dengan banyak baris (menandakan tabel data)
            for table in all_tables:
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    if len(rows) > 0:
                        # Cek apakah tabel ini memiliki kolom yang relevan
                        headers = []
                        thead = table.find('thead')
                        if thead:
                            header_row = thead.find('tr')
                            if header_row:
                                for th in header_row.find_all(['th', 'td']):
                                    header_text = th.get_text(strip=True)
                                    if header_text and len(header_text) > 0:
                                        headers.append(header_text.lower())
                        
                        # Jika tabel memiliki kolom yang relevan, tambahkan ke result_tables
                        if headers and any(keyword in ' '.join(headers) for keyword in ['hp', 'nik', 'nm', 'id', 'nama']):
                            result_tables.append(table)
                            logger.info(f"Found potential data table with {len(rows)} rows and headers: {headers[:5]}")
        
        # Hanya gunakan tabel table_results, jika tidak ada maka return None
        if not result_tables:
            logger.warning("No table_results found in HTML response")
            print(f"[TELEGRAM_BOT] ⚠️ No data tables found in HTML response", file=sys.stderr)
            return None
        
        logger.info(f"Processing {len(result_tables)} potential data tables")
        print(f"[TELEGRAM_BOT] 📊 Found {len(result_tables)} potential data tables to parse", file=sys.stderr)
        
        # FILTER TAMBAHAN: Pastikan tabel memiliki tbody (menandakan ini tabel data, bukan form/settings)
        filtered_tables = []
        for table in result_tables:
            tbody = table.find('tbody')
            if tbody and len(tbody.find_all('tr')) > 0:
                filtered_tables.append(table)
        
        if not filtered_tables:
            logger.warning("No table_results with tbody found in HTML response")
            return None
        
        result_tables = filtered_tables
        
        phone_clean = re.sub(r'\D', '', phone_number)
        
        for table in result_tables:
            
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            # Ambil header dari thead atau baris pertama
            headers = []
            # Cek apakah ada thead
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
            else:
                header_row = rows[0] if rows else None
            
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    header_text = None
                    # Prioritaskan data-column attribute (phpMyAdmin menggunakan ini)
                    if th.get('data-column'):
                        header_text = th.get('data-column')
                    else:
                        # Ambil text dari link jika ada
                        link = th.find('a')
                        if link:
                            link_text = link.get_text(strip=True)
                            if link_text:
                                header_text = link_text
                        # Jika tidak ada link, ambil langsung dari element
                        if not header_text:
                            header_text = th.get_text(strip=True)
                    
                    # Skip jika header kosong atau hanya berisi karakter khusus
                    if header_text and len(header_text) > 0 and not header_text.startswith('+'):
                        headers.append(header_text.lower())
            
            if not headers or len(headers) < 3:  # Minimal 3 kolom untuk tabel data
                continue
            
            # Pastikan ini tabel penduduk (harus ada kolom hp, nik, atau nm)
            headers_combined = ' '.join(headers)
            
            # Skip jika ini tabel settings (biasanya ada keyword tertentu) - PRIORITAS
            skip_header_keywords = ['tampilkan', 'atur', 'jumlah', 'maksimum', 'favorit', 'navigasi', 'panel', 'lebar', 'ikon', 'teks', 'ulangi', 'judul', 'header', 'baris', 'saring', 'urut', 'checkbox', 'input', 'select', 'option']
            if any(keyword in headers_combined for keyword in skip_header_keywords):
                logger.info(f"Skipping table with settings keywords in headers: {headers_combined[:100]}")
                continue
            
            # Pastikan ini tabel penduduk (harus ada kolom hp, nik, atau nm)
            # Tapi juga pastikan tidak ada kolom yang menandakan ini form/settings
            has_data_columns = any(keyword in headers_combined for keyword in ['hp', 'nik', 'nm', 'id'])
            has_form_columns = any(keyword in headers_combined for keyword in ['checkbox', 'input', 'select', 'option', 'label', 'form'])
            
            if has_form_columns:
                logger.info(f"Skipping table - has form columns: {headers_combined[:100]}")
                continue
            
            if not has_data_columns:
                logger.info(f"Skipping table - no relevant columns (hp/nik/nm/id)")
                continue
            
            # Pastikan minimal ada kolom yang relevan untuk data penduduk
            required_columns = ['hp', 'nik', 'nm']
            has_required = any(col in headers for col in required_columns)
            if not has_required:
                logger.info(f"Skipping table - missing required columns. Headers: {headers}")
                continue
            
            # Cari kolom yang berisi nomor HP
            hp_column_index = None
            for idx, header in enumerate(headers):
                if any(keyword in header for keyword in ['hp', 'phone', 'telp', 'nomor']):
                    hp_column_index = idx
                    break
            
            # Jika tidak ada kolom HP spesifik, cari di semua kolom
            # PENTING: Hanya ambil data dari tbody, bukan dari thead atau tabel menu
            tbody = table.find('tbody')
            data_rows = tbody.find_all('tr') if tbody else rows[1:]
            
            logger.info(f"Found {len(data_rows)} data rows in table with headers: {headers[:10]}")
            print(f"[TELEGRAM_BOT] 📊 Found {len(data_rows)} data rows, headers: {headers[:10]}", file=sys.stderr)
            
            # Log beberapa baris pertama untuk debugging
            if len(data_rows) > 0:
                # Cari kolom HP di sample rows
                for sample_idx in range(min(3, len(data_rows))):
                    sample_row = data_rows[sample_idx]
                    sample_cells = sample_row.find_all(['td', 'th'])
                    sample_data = {}
                    for idx, cell in enumerate(sample_cells):
                        if idx < len(headers):
                            sample_data[headers[idx]] = cell.get_text(strip=True)[:30]
                    
                    # Cari nomor HP di sample data
                    for key, value in sample_data.items():
                        if any(kw in key.lower() for kw in ['hp', 'phone', 'telp', 'nomor']):
                            logger.info(f"Sample row {sample_idx} - {key}: {value}")
                            print(f"[TELEGRAM_BOT] 📋 Sample row {sample_idx} - {key}: {value}", file=sys.stderr)
                            # Cek apakah ini match dengan nomor yang dicari
                            value_clean = re.sub(r'\D', '', value)
                            phone_clean_check = re.sub(r'\D', '', phone_number)
                            if value_clean and phone_clean_check:
                                match_status = "MATCH" if value_clean[-10:] == phone_clean_check[-10:] else "NO MATCH"
                                logger.info(f"  Phone comparison: {value_clean[-10:]} vs {phone_clean_check[-10:]} = {match_status}")
                                print(f"[TELEGRAM_BOT]   Phone comparison: {value_clean[-10:]} vs {phone_clean_check[-10:]} = {match_status}", file=sys.stderr)
            
            if hp_column_index is None:
                # Cari di semua data rows (hanya dari tbody)
                # Jika ini dari tbl_select.php dengan WHERE clause, semua baris seharusnya sudah match
                # Tapi kita tetap filter untuk memastikan
                rows_processed = 0
                rows_matched = 0
                
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:  # Skip jika terlalu sedikit kolom
                        continue
                    
                    rows_processed += 1
                    row_data = {}
                    found_phone = False
                    
                    for idx, cell in enumerate(cells):
                        # Skip cell dengan class print_ignore atau cell kosong
                        cell_classes = cell.get('class', [])
                        if 'print_ignore' in str(cell_classes).lower():
                            continue
                            
                        cell_text = cell.get_text(strip=True)
                        if not cell_text:
                            continue
                            
                        if idx < len(headers):
                            row_data[headers[idx]] = cell_text
                        else:
                            row_data[f'col_{idx}'] = cell_text
                        
                        # Cek apakah cell ini berisi nomor HP yang dicari
                        cell_clean = re.sub(r'\D', '', cell_text)
                        if cell_clean and phone_clean and len(cell_clean) >= 10:
                            # Check if phone numbers match (with various formats)
                            # Cek exact match atau partial match (minimal 10 digit terakhir)
                            cell_normalized = cell_clean[-10:] if len(cell_clean) >= 10 else cell_clean
                            phone_normalized = phone_clean[-10:] if len(phone_clean) >= 10 else phone_clean
                            
                            if (cell_clean == phone_clean or 
                                cell_normalized == phone_normalized or
                                (len(cell_clean) >= 10 and len(phone_clean) >= 10 and 
                                 (cell_clean[-10:] == phone_clean[-10:] or phone_clean[-10:] == cell_clean[-10:])) or
                                cell_clean.endswith(phone_normalized) or 
                                phone_clean.endswith(cell_normalized) or
                                phone_normalized in cell_clean or
                                cell_normalized in phone_clean):
                                found_phone = True
                                if rows_matched < 3:  # Log first 3 matches
                                    logger.info(f"Match found in row {rows_processed}: {cell_text} (normalized: {cell_normalized})")
                                    print(f"[TELEGRAM_BOT] ✅ Match found: {cell_text} (normalized: {cell_normalized})", file=sys.stderr)
                    
                    # Jika ini dari tbl_select.php dengan WHERE clause, semua baris seharusnya sudah match
                    # Tapi kita tetap filter untuk memastikan
                    if found_phone:
                        rows_matched += 1
                        results.append(row_data)
                    elif rows_processed <= 50:  # Jika <= 50 rows, kemungkinan sudah difilter oleh WHERE clause, ambil semua
                        # Ambil semua baris jika jumlahnya sedikit (kemungkinan sudah difilter)
                        results.append(row_data)
                        logger.info(f"Taking row {rows_processed} without phone match (likely pre-filtered by WHERE clause)")
                
                logger.info(f"Processed {rows_processed} rows, found {rows_matched} matches")
                print(f"[TELEGRAM_BOT] 📊 Processed {rows_processed} rows, found {rows_matched} matches", file=sys.stderr)
            else:
                # Ada kolom HP spesifik, cari baris yang match
                # Skip thead jika ada
                tbody = table.find('tbody')
                data_rows = tbody.find_all('tr') if tbody else rows[1:]
                
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    if hp_column_index < len(cells):
                        hp_cell = cells[hp_column_index].get_text(strip=True)
                        hp_cell_clean = re.sub(r'\D', '', hp_cell)
                        
                        if hp_cell_clean and phone_clean and len(hp_cell_clean) >= 10:
                            # Check if phone numbers match (dengan berbagai format)
                            # Normalize kedua nomor untuk perbandingan (ambil 10 digit terakhir)
                            hp_normalized = hp_cell_clean[-10:] if len(hp_cell_clean) >= 10 else hp_cell_clean
                            phone_normalized = phone_clean[-10:] if len(phone_clean) >= 10 else phone_clean
                            
                            # Cek juga dengan format lengkap (dengan/tanpa prefix 62, dengan/tanpa leading 0)
                            hp_without_62 = hp_cell_clean[2:] if hp_cell_clean.startswith('62') else hp_cell_clean
                            hp_with_62 = '62' + hp_cell_clean if not hp_cell_clean.startswith('62') else hp_cell_clean
                            hp_with_0 = '0' + hp_cell_clean if not hp_cell_clean.startswith('0') else hp_cell_clean
                            hp_without_0 = hp_cell_clean[1:] if hp_cell_clean.startswith('0') else hp_cell_clean
                            
                            phone_without_62 = phone_clean[2:] if phone_clean.startswith('62') else phone_clean
                            phone_with_62 = '62' + phone_clean if not phone_clean.startswith('62') else phone_clean
                            phone_with_0 = '0' + phone_clean if not phone_clean.startswith('0') else phone_clean
                            phone_without_0 = phone_clean[1:] if phone_clean.startswith('0') else phone_clean
                            
                            # Cek exact match atau partial match dengan berbagai format
                            match_found = (
                                hp_cell_clean == phone_clean or 
                                hp_normalized == phone_normalized or
                                hp_cell_clean.endswith(phone_normalized) or 
                                phone_clean.endswith(hp_normalized) or
                                hp_normalized in phone_clean or
                                phone_normalized in hp_cell_clean or
                                # Cek dengan berbagai format
                                hp_without_62 == phone_without_62 or
                                hp_with_62 == phone_with_62 or
                                hp_with_0 == phone_with_0 or
                                hp_without_0 == phone_without_0 or
                                hp_cell_clean[-10:] == phone_clean[-10:] or
                                hp_cell_clean[-11:] == phone_clean[-11:] if len(hp_cell_clean) >= 11 and len(phone_clean) >= 11 else False
                            )
                            
                            if match_found:
                                # Match found, extract all row data
                                row_data = {}
                                for idx, cell in enumerate(cells):
                                    cell_text = cell.get_text(strip=True)
                                    # Skip cell kosong atau cell dengan class tertentu
                                    if not cell_text or 'print_ignore' in str(cell.get('class', [])):
                                        continue
                                        
                                    if idx < len(headers):
                                        row_data[headers[idx]] = cell_text
                                    else:
                                        row_data[f'col_{idx}'] = cell_text
                                results.append(row_data)
        
        # Log hasil parsing
        if results:
            logger.info(f"✅ Successfully parsed {len(results)} matching records from HTML table")
            print(f"[TELEGRAM_BOT] ✅ Successfully parsed {len(results)} matching records from HTML", file=sys.stderr)
        else:
            logger.warning("No matching records found in HTML table after parsing")
            print(f"[TELEGRAM_BOT] ⚠️ No matching records found in HTML table", file=sys.stderr)
        
        return results if results else None
        
    except ImportError:
        logger.warning("BeautifulSoup not available, cannot parse HTML")
        return None
    except Exception as e:
        logger.error(f"Error parsing HTML table: {e}")
        return None


def get_phone_db_connection():
    """Get connection to phone database MySQL"""
    try:
        import mysql.connector
        from mysql.connector import Error
        
        conn = mysql.connector.connect(
            host=PHONE_DB_HOST,
            port=PHONE_DB_PORT,
            user=PHONE_DB_USER,
            password=PHONE_DB_PASSWORD,
            database=PHONE_DB_NAME if PHONE_DB_NAME else None,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=True,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to phone database: {e}")
        print(f"[TELEGRAM_BOT] ❌ Error connecting to phone database: {e}", file=sys.stderr)
        return None


def query_phone_from_mysql(phone_number: str):
    """Query phone data directly from MySQL database"""
    conn = None
    cursor = None
    
    try:
        conn = get_phone_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        
        # Normalize phone number for query (try multiple formats)
        phone_clean = ''.join(filter(str.isdigit, phone_number))
        phone_variants = [
            phone_clean,  # Original
            phone_clean.lstrip('0'),  # Remove leading 0
            '0' + phone_clean if not phone_clean.startswith('0') else phone_clean,  # Add leading 0
            '62' + phone_clean.lstrip('0') if not phone_clean.startswith('62') else phone_clean,  # Add 62 prefix
            phone_clean.replace('62', '0', 1) if phone_clean.startswith('62') else phone_clean,  # Replace 62 with 0
        ]
        
        # Try common table and column names
        # PRIORITAS: Tabel penduduk di database sipudat1 (sesuai dengan struktur yang ada)
        possible_queries = [
            # Format 1: Table 'penduduk' di database sipudat1 (PRIORITAS)
            # Cari dengan berbagai format nomor HP dan kolom yang mungkin
            "SELECT * FROM penduduk WHERE hp = %s OR hp LIKE %s OR hp LIKE %s OR hp LIKE %s LIMIT 100",
            "SELECT * FROM penduduk WHERE phone = %s OR phone LIKE %s OR phone LIKE %s OR phone LIKE %s LIMIT 100",
            "SELECT * FROM penduduk WHERE nomor_hp = %s OR nomor_hp LIKE %s OR nomor_hp LIKE %s OR nomor_hp LIKE %s LIMIT 100",
            "SELECT * FROM penduduk WHERE telp = %s OR telp LIKE %s OR telp LIKE %s OR telp LIKE %s LIMIT 100",
            # Format 2: Table 'phone' or 'phones' with column 'phone' or 'nomor_hp' or 'hp'
            "SELECT * FROM phone WHERE phone = %s OR nomor_hp = %s OR hp = %s OR msisdn = %s LIMIT 100",
            "SELECT * FROM phones WHERE phone = %s OR nomor_hp = %s OR hp = %s OR msisdn = %s LIMIT 100",
            "SELECT * FROM data_phone WHERE phone = %s OR nomor_hp = %s OR hp = %s OR msisdn = %s LIMIT 100",
            "SELECT * FROM phone_data WHERE phone = %s OR nomor_hp = %s OR hp = %s OR msisdn = %s LIMIT 100",
            # Format 3: Table with phone in name
            "SELECT * FROM informasi_phone WHERE phone_number = %s OR phone = %s LIMIT 100",
        ]
        
        results = []
        
        for query_template in possible_queries:
            try:
                # Try each phone variant
                for variant in phone_variants:
                    if not variant or len(variant) < 10:
                        continue
                    
                    # Untuk query penduduk dengan LIKE, gunakan berbagai format pencarian
                    if 'penduduk' in query_template.lower() and 'LIKE' in query_template:
                        # Coba exact match dan partial match dengan berbagai format
                        like_patterns = [
                            variant,  # Exact match: 085218341136
                            f'%{variant}%',  # Contains: %085218341136%
                            f'{variant}%',  # Starts with: 085218341136%
                            f'%{variant}',  # Ends with: %085218341136
                        ]
                        # Ambil 4 pattern pertama untuk query dengan 4 placeholder
                        patterns = like_patterns[:4] if len(like_patterns) >= 4 else like_patterns + [variant] * (4 - len(like_patterns))
                        try:
                            cursor.execute(query_template, tuple(patterns))
                        except Exception as e:
                            logger.debug(f"Query failed with patterns {patterns}: {e}")
                            continue
                    else:
                        # Untuk query lain, gunakan variant yang sama untuk semua placeholder
                        try:
                            cursor.execute(query_template, (variant, variant, variant, variant))
                        except Exception as e:
                            logger.debug(f"Query failed with variant {variant}: {e}")
                            continue
                    
                    rows = cursor.fetchall()
                    
                    if rows:
                        results.extend(rows)
                        logger.info(f"✅ Found {len(rows)} results with query: {query_template[:50]}... (variant: {variant})")
                        print(f"[TELEGRAM_BOT] ✅ Found {len(rows)} results with variant {variant}", file=sys.stderr)
                        break  # Found results, no need to try other variants for this query
            except Exception as e:
                # Table or column doesn't exist, try next query
                logger.debug(f"Query failed: {query_template[:50]}... Error: {e}")
                continue
        
        # Remove duplicates based on first unique identifier found
        if results:
            seen = set()
            unique_results = []
            for row in results:
                # Create a unique key from common ID fields
                unique_key = None
                for key in ['id', 'nik', 'phone', 'nomor_hp', 'hp', 'msisdn']:
                    if key in row and row[key]:
                        unique_key = str(row[key])
                        break
                
                if unique_key and unique_key not in seen:
                    seen.add(unique_key)
                    unique_results.append(row)
            
            return unique_results if unique_results else results
        
        return None
        
    except Exception as e:
        logger.error(f"Error querying phone from MySQL: {e}")
        print(f"[TELEGRAM_BOT] ❌ Error querying phone from MySQL: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


async def check_phone_from_database(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str):
    """Check phone number from dedicated database (MySQL or HTTP API)"""
    user_id = update.effective_user.id
    status_msg = None
    
    print(f"[TELEGRAM_BOT] 🚀 check_phone_from_database called with phone: {phone_number}", file=sys.stderr)
    logger.info(f"check_phone_from_database called with phone: {phone_number}")
    
    try:
        # Kirim pesan status bahwa bot sedang mencari
        status_msg = await update.message.reply_text(
            f"🔍 *Mencari Data...*\n\n"
            f"📱 Nomor HP: `{phone_number}`\n\n"
            f"⏳ Sedang mencari di database 30 juta record...\n"
            f"Mohon tunggu sebentar...",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
        # Normalize phone number
        phone_clean = ''.join(filter(str.isdigit, phone_number))
        if phone_clean.startswith('0'):
            phone_clean = '62' + phone_clean[1:]
        elif not phone_clean.startswith('62'):
            phone_clean = '62' + phone_clean
        
        logger.info(f"Checking phone number: {phone_clean} from database")
        print(f"[TELEGRAM_BOT] 📱 Checking phone: {phone_clean}", file=sys.stderr)
        print(f"[TELEGRAM_BOT] 🔄 Starting search process...", file=sys.stderr)
        
        phone_data = None
        last_error = None
        
        # PRIORITAS 1: Coba endpoint API lokal Flask (localhost)
        # Endpoint ini lebih cepat dan tidak memerlukan token/authentication
        print(f"[TELEGRAM_BOT] 🔍 PRIORITAS 1: Mencoba endpoint API lokal Flask...", file=sys.stderr)
        logger.info("PRIORITAS 1: Mencoba endpoint API lokal Flask")
        
        try:
            import requests
            # Get Flask app base URL from environment or use default
            flask_base_url = os.getenv('FLASK_BASE_URL', 'http://localhost:5000')
            local_api_url = f"{flask_base_url}/api/phone/search"
            
            logger.info(f"Trying local Flask API: {local_api_url}")
            print(f"[TELEGRAM_BOT] 🌐 Trying local Flask API: {local_api_url}", file=sys.stderr)
            print(f"[TELEGRAM_BOT] 📱 Phone number to search: {phone_number}", file=sys.stderr)
            
            response = requests.get(
                local_api_url,
                params={'phone': phone_number},
                timeout=30
            )
            
            logger.info(f"Local Flask API response status: {response.status_code}")
            print(f"[TELEGRAM_BOT] 📡 Local Flask API response status: {response.status_code}", file=sys.stderr)
            
            if response.status_code == 200:
                json_data = response.json()
                logger.info(f"Local Flask API response: success={json_data.get('success')}, count={json_data.get('count', 0)}")
                print(f"[TELEGRAM_BOT] 📊 Local Flask API response: success={json_data.get('success')}, count={json_data.get('count', 0)}", file=sys.stderr)
                
                if json_data.get('success') and json_data.get('data'):
                    phone_data = json_data['data']
                    logger.info(f"✅ Successfully fetched {len(phone_data)} results from local Flask API")
                    print(f"[TELEGRAM_BOT] ✅ Successfully fetched {len(phone_data)} results from local Flask API", file=sys.stderr)
                elif json_data.get('success') == False:
                    # No data found, but API is working
                    logger.info(f"Local Flask API returned no data (API is working)")
                    print(f"[TELEGRAM_BOT] ℹ️ Local Flask API returned no data (API is working)", file=sys.stderr)
                    # Don't set phone_data, let it try other methods
                else:
                    logger.warning(f"Local Flask API returned unexpected response: {json_data}")
                    print(f"[TELEGRAM_BOT] ⚠️ Local Flask API returned unexpected response", file=sys.stderr)
            else:
                logger.warning(f"Local Flask API returned status {response.status_code}: {response.text[:200]}")
                print(f"[TELEGRAM_BOT] ⚠️ Local Flask API returned status {response.status_code}", file=sys.stderr)
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Local Flask API connection error: {e}")
            print(f"[TELEGRAM_BOT] ⚠️ Local Flask API connection error (Flask app mungkin belum running): {e}", file=sys.stderr)
            print(f"[TELEGRAM_BOT] 💡 Pastikan Flask app berjalan di {flask_base_url}", file=sys.stderr)
            last_error = "Local Flask API tidak tersedia"
        except requests.exceptions.Timeout as e:
            logger.warning(f"Local Flask API timeout: {e}")
            print(f"[TELEGRAM_BOT] ⚠️ Local Flask API timeout: {e}", file=sys.stderr)
            last_error = "Local Flask API timeout"
        except Exception as e:
            logger.error(f"Local Flask API error: {e}", exc_info=True)
            print(f"[TELEGRAM_BOT] ❌ Local Flask API error: {e}", file=sys.stderr)
            import traceback
            print(f"[TELEGRAM_BOT] Traceback: {traceback.format_exc()}", file=sys.stderr)
            last_error = f"Local Flask API error: {str(e)}"
        
        # Log status setelah mencoba Flask API
        if phone_data:
            print(f"[TELEGRAM_BOT] ✅ Flask API berhasil, skip ke metode lain", file=sys.stderr)
        else:
            print(f"[TELEGRAM_BOT] ⚠️ Flask API tidak berhasil, lanjut ke metode berikutnya...", file=sys.stderr)
        
        # PRIORITAS 2: Coba koneksi langsung ke MySQL database
        # Coba koneksi MySQL jika host dan port tersedia (tidak perlu menunggu PHONE_DB_NAME)
        if not phone_data and PHONE_DB_HOST and PHONE_DB_PORT:
            db_name_display = PHONE_DB_NAME if PHONE_DB_NAME else 'sipudat1'
            logger.info(f"Trying MySQL connection to {PHONE_DB_HOST}:{PHONE_DB_PORT}/{db_name_display}")
            print(f"[TELEGRAM_BOT] Trying MySQL connection to {PHONE_DB_HOST}:{PHONE_DB_PORT}/{db_name_display}", file=sys.stderr)
            phone_data = query_phone_from_mysql(phone_number)
            if phone_data:
                logger.info(f"✅ Successfully fetched {len(phone_data)} results from MySQL")
                print(f"[TELEGRAM_BOT] ✅ Successfully fetched {len(phone_data)} results from MySQL", file=sys.stderr)
        
        # Hanya menggunakan Flask API lokal dan MySQL langsung, tidak menggunakan phpMyAdmin
        if not phone_data:
            logger.warning("Flask API dan MySQL langsung tidak berhasil, tidak ada metode lain yang tersedia")
            print(f"[TELEGRAM_BOT] ⚠️ Flask API dan MySQL langsung tidak berhasil", file=sys.stderr)
            print(f"[TELEGRAM_BOT] 💡 Pastikan Flask app berjalan di http://localhost:5000", file=sys.stderr)
            print(f"[TELEGRAM_BOT] 💡 Atau pastikan MySQL database dapat diakses", file=sys.stderr)
            last_error = "Flask API dan MySQL langsung tidak tersedia"
        
        if not phone_data:
            # Hapus pesan status dan kirim pesan error
            try:
                if status_msg:
                    await status_msg.delete()
            except:
                pass
            
            await update.message.reply_text(
                f"❌ *Data Tidak Ditemukan*\n\n"
                f"Nomor HP: `{phone_number}`\n\n"
                f"Data tidak ditemukan di database.\n"
                f"Error: {last_error or 'Tidak dapat terhubung ke database'}",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # Format and display phone data
        message = f"📱 *DATA NOMOR HP*\n"
        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"📞 *Nomor HP:* `{phone_number}`\n\n"
        
        # Handle MySQL results (list of dicts)
        if isinstance(phone_data, list) and len(phone_data) > 0:
            message += f"✅ *Ditemukan {len(phone_data)} hasil*\n\n"
            for idx, item in enumerate(phone_data[:5], 1):  # Limit to 5 results
                message += f"━━━━━━━━━━━━━━━━━━━━\n"
                message += f"📋 *HASIL {idx}*\n"
                message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                message += format_phone_data_item(item)
                if idx < min(len(phone_data), 5):
                    message += "\n"
        # Handle different response formats (HTTP API)
        elif isinstance(phone_data, dict):
            # If response has 'data' key
            if 'data' in phone_data:
                data = phone_data['data']
                if isinstance(data, list) and len(data) > 0:
                    # Multiple results
                    message += f"✅ *Ditemukan {len(data)} hasil*\n\n"
                    for idx, item in enumerate(data[:5], 1):  # Limit to 5 results
                        message += f"━━━━━━━━━━━━━━━━━━━━\n"
                        message += f"📋 *HASIL {idx}*\n"
                        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        message += format_phone_data_item(item)
                        if idx < min(len(data), 5):
                            message += "\n"
                elif isinstance(data, dict):
                    # Single result
                    message += format_phone_data_item(data)
                else:
                    message += format_phone_data_item(phone_data)
            # If response has 'result' key
            elif 'result' in phone_data:
                result = phone_data['result']
                if isinstance(result, list) and len(result) > 0:
                    message += f"✅ *Ditemukan {len(result)} hasil*\n\n"
                    for idx, item in enumerate(result[:5], 1):
                        message += f"━━━━━━━━━━━━━━━━━━━━\n"
                        message += f"📋 *HASIL {idx}*\n"
                        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                        message += format_phone_data_item(item)
                        if idx < min(len(result), 5):
                            message += "\n"
                elif isinstance(result, dict):
                    message += format_phone_data_item(result)
                else:
                    message += format_phone_data_item(phone_data)
            # If response is a list directly
            elif isinstance(phone_data, list) and len(phone_data) > 0:
                message += f"✅ *Ditemukan {len(phone_data)} hasil*\n\n"
                for idx, item in enumerate(phone_data[:5], 1):
                    message += f"━━━━━━━━━━━━━━━━━━━━\n"
                    message += f"📋 *HASIL {idx}*\n"
                    message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    message += format_phone_data_item(item)
                    if idx < min(len(phone_data), 5):
                        message += "\n"
            else:
                # Single dict result
                message += format_phone_data_item(phone_data)
        elif isinstance(phone_data, list) and len(phone_data) > 0:
            message += f"✅ *Ditemukan {len(phone_data)} hasil*\n\n"
            for idx, item in enumerate(phone_data[:5], 1):
                message += f"━━━━━━━━━━━━━━━━━━━━\n"
                message += f"📋 *HASIL {idx}*\n"
                message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
                message += format_phone_data_item(item)
                if idx < min(len(phone_data), 5):
                    message += "\n"
        else:
            message += "❌ Format data tidak dikenali"
        
        # Add footer
        message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
        if PHONE_DB_NAME:
            message += f"💡 *Sumber:* Database MySQL langsung\n"
            message += f"🌐 *Server:* {PHONE_DB_HOST}:{PHONE_DB_PORT}/{PHONE_DB_NAME}"
        else:
            message += f"💡 *Sumber:* Flask API lokal\n"
            message += f"🌐 *Endpoint:* http://localhost:5000/api/phone/search"
        
        # Hapus pesan status sebelum mengirim hasil
        try:
            if status_msg:
                await status_msg.delete()
        except:
            pass
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        
    except Exception as e:
        logger.error(f"Error in check_phone_from_database: {e}")
        import traceback
        traceback.print_exc()
        
        # Hapus pesan status jika ada
        try:
            if status_msg:
                await status_msg.delete()
        except:
            pass
        
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}\n\n"
            f"Terjadi kesalahan saat mencari data nomor HP.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


def format_phone_data_item(item):
    """Format a single phone data item for display"""
    if not isinstance(item, dict):
        return f"📄 {str(item)}\n"
    
    message = ""
    
    # Common field mappings (prioritaskan kolom dari tabel penduduk)
    field_mappings = {
        # Kolom utama dari tabel penduduk
        'id': ('🆔', 'ID'),
        'nik': ('🆔', 'NIK'),
        'nm': ('👤', 'Nama'),
        'nama': ('👤', 'Nama'),
        'name': ('👤', 'Nama'),
        'full_name': ('👤', 'Nama Lengkap'),
        'jk': ('⚧️', 'Jenis Kelamin'),
        'ttl': ('📅', 'Tanggal/Tempat Lahir'),
        'hp': ('📱', 'Nomor HP'),
        'nomor_hp': ('📱', 'Nomor HP'),
        'phone': ('📱', 'Nomor HP'),
        'phone_number': ('📱', 'Nomor HP'),
        'msisdn': ('📱', 'Nomor HP'),
        'alamat': ('🏠', 'Alamat'),
        'address': ('🏠', 'Alamat'),
        'kel': ('🏡', 'Kelurahan'),
        'kelurahan': ('🏡', 'Kelurahan'),
        'kec': ('📍', 'Kecamatan'),
        'kecamatan': ('📍', 'Kecamatan'),
        'kab_kota': ('🏘️', 'Kabupaten/Kota'),
        'kabupaten': ('🏘️', 'Kabupaten'),
        'kota': ('🏘️', 'Kota'),
        'id_prov': ('🗺️', 'ID Provinsi'),
        'provinsi': ('🗺️', 'Provinsi'),
        # Kolom tambahan
        'tempat_lahir': ('📍', 'Tempat Lahir'),
        'tanggal_lahir': ('📅', 'Tanggal Lahir'),
        'birth_date': ('📅', 'Tanggal Lahir'),
        'jenis_kelamin': ('⚧️', 'Jenis Kelamin'),
        'gender': ('⚧️', 'Jenis Kelamin'),
        'pekerjaan': ('💼', 'Pekerjaan'),
        'occupation': ('💼', 'Pekerjaan'),
        'operator': ('📡', 'Operator'),
        'provider': ('📡', 'Provider'),
        'register_date': ('📅', 'Tanggal Registrasi'),
        'registered_at': ('📅', 'Tanggal Registrasi'),
        'status': ('📊', 'Status'),
    }
    
    # Display known fields first (urutkan sesuai prioritas kolom penduduk)
    priority_order = ['id', 'nik', 'nm', 'nama', 'name', 'full_name', 'jk', 'ttl', 'hp', 'nomor_hp', 'phone', 'alamat', 'address', 'kel', 'kelurahan', 'kec', 'kecamatan', 'kab_kota', 'kabupaten', 'kota', 'id_prov', 'provinsi']
    
    displayed_keys = set()
    
    # Tampilkan kolom prioritas dulu (kolom dari tabel penduduk)
    for key in priority_order:
        if key in field_mappings:
            value = item.get(key) or item.get(key.upper()) or item.get(key.lower())
            if value and str(value).strip() and str(value) != 'None' and str(value) != '':
                emoji, label = field_mappings[key]
                message += f"{emoji} *{label}:* {value}\n"
                displayed_keys.add(key.lower())
    
    # Tampilkan kolom lain yang belum ditampilkan
    for key, (emoji, label) in field_mappings.items():
        if key.lower() not in displayed_keys:
            value = item.get(key) or item.get(key.upper()) or item.get(key.lower())
            if value and str(value).strip() and str(value) != 'None' and str(value) != '':
                message += f"{emoji} *{label}:* {value}\n"
                displayed_keys.add(key.lower())
    
    # Display any remaining fields yang belum ditampilkan
    for key, value in item.items():
        if key.lower() not in displayed_keys:
            if value and str(value).strip() and str(value) != 'None' and str(value) != '':
                # Skip kolom yang tidak relevan
                if key.lower().startswith('col_') or 'print_ignore' in key.lower():
                    continue
                    
                # Auto-detect emoji based on key name
                key_lower = key.lower()
                emoji = "📄"
                if 'nama' in key_lower or 'name' in key_lower or 'nm' in key_lower:
                    emoji = "👤"
                elif 'alamat' in key_lower or 'address' in key_lower:
                    emoji = "🏠"
                elif 'hp' in key_lower or 'phone' in key_lower or 'telp' in key_lower:
                    emoji = "📱"
                elif 'tanggal' in key_lower or 'date' in key_lower or 'tgl' in key_lower or 'ttl' in key_lower:
                    emoji = "📅"
                elif 'nik' in key_lower or ('id' in key_lower and 'prov' not in key_lower):
                    emoji = "🆔"
                elif 'operator' in key_lower or 'provider' in key_lower:
                    emoji = "📡"
                elif 'kel' in key_lower or 'kelurahan' in key_lower:
                    emoji = "🏡"
                elif 'kec' in key_lower or 'kecamatan' in key_lower:
                    emoji = "📍"
                elif 'kab' in key_lower or 'kota' in key_lower:
                    emoji = "🏘️"
                elif 'prov' in key_lower or 'provinsi' in key_lower:
                    emoji = "🗺️"
                
                # Format key name untuk display
                display_key = key.replace('_', ' ').title()
                message += f"{emoji} *{display_key}:* {value}\n"
    
    if not message:
        message = "📄 *Data tidak tersedia*\n"
    
    return message


def is_owner(user_id: int) -> bool:
    """Check if user is owner/admin"""
    owner_id = TELEGRAM_OWNER_ID
    # Convert both to string for comparison
    user_id_str = str(user_id)
    owner_id_str = str(owner_id) if owner_id else ""
    result = bool(owner_id_str and user_id_str == owner_id_str)
    logger.info(f"is_owner check: user_id={user_id} ({type(user_id).__name__}), owner_id={owner_id} ({type(owner_id).__name__}), result={result}")
    print(f"[TELEGRAM_BOT] is_owner check: user_id={user_id} ({type(user_id).__name__}), owner_id={owner_id} ({type(owner_id).__name__}), result={result}", file=sys.stderr)
    return result


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin menu for managing whitelist"""
    try:
        user_id = update.effective_user.id
        logger.info(f"🔐 admin_menu() called by user {user_id}, owner_id={TELEGRAM_OWNER_ID}")
        print(f"[TELEGRAM_BOT] 🔐 admin_menu() called by user {user_id}, owner_id={TELEGRAM_OWNER_ID}", file=sys.stderr)
        
        if not is_owner(user_id):
            logger.warning(f"User {user_id} tried to access admin menu but is not owner")
            print(f"[TELEGRAM_BOT] ⚠️ User {user_id} tried to access admin menu but is not owner", file=sys.stderr)
            await update.message.reply_text(
                "❌ *Akses Ditolak*\n\n"
                "Anda tidak memiliki akses ke menu admin.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        logger.info(f"✅ User {user_id} is owner, creating admin menu")
        print(f"[TELEGRAM_BOT] ✅ User {user_id} is owner, creating admin menu", file=sys.stderr)
        
        # Buat keyboard dengan tombol admin interaktif
        try:
            keyboard = [
                [
                    InlineKeyboardButton("➕ Tambah User", callback_data="admin_adduser"),
                    InlineKeyboardButton("➖ Hapus User", callback_data="admin_removeuser")
                ],
                [
                    InlineKeyboardButton("📋 List User Terdaftar", callback_data="admin_listusers"),
                    InlineKeyboardButton("🆕 User Pending", callback_data="admin_pendingusers")
                ],
                [
                    InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")
                ]
            ]
            logger.info(f"Keyboard created successfully")
            print(f"[TELEGRAM_BOT] Keyboard created successfully", file=sys.stderr)
        except Exception as e:
            logger.error(f"Error creating keyboard: {e}")
            print(f"[TELEGRAM_BOT] ❌ Error creating keyboard: {e}", file=sys.stderr)
            raise
        
        menu_text = (
            "🔐 *MENU ADMIN*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📋 *Manage Whitelist*\n\n"
            "Pilih menu di bawah:\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💡 *Command:*\n"
            "`/adduser <id>` - Tambah user\n"
            "`/removeuser <id>` - Hapus user\n"
            "`/listusers` - List user\n"
            "`/pendingusers` - User pending"
        )
        
        logger.info(f"📤 Sending admin menu to user {user_id}")
        print(f"[TELEGRAM_BOT] 📤 Sending admin menu to user {user_id}", file=sys.stderr)
        
        try:
            result = await update.message.reply_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            logger.info(f"✅ Admin menu sent successfully to user {user_id}, message_id={result.message_id if result else 'None'}")
            print(f"[TELEGRAM_BOT] ✅ Admin menu sent successfully to user {user_id}, message_id={result.message_id if result else 'None'}", file=sys.stderr)
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            print(f"[TELEGRAM_BOT] ❌ Error sending message: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise
    except Exception as e:
        logger.error(f"Error in admin_menu: {e}")
        import traceback
        traceback.print_exc()
        print(f"[TELEGRAM_BOT] Error in admin_menu: {e}", file=sys.stderr)
        print(f"[TELEGRAM_BOT] Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        try:
            await update.message.reply_text(
                f"❌ *Error:* {str(e)}\n\n"
                "Silakan coba lagi atau gunakan command `/admin`.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(update.effective_user.id if update.effective_user else None)
            )
        except Exception as e2:
            logger.error(f"Error sending error message: {e2}")
            print(f"[TELEGRAM_BOT] Error sending error message: {e2}", file=sys.stderr)


async def add_user_to_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add user to whitelist"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Hanya owner yang dapat menambahkan user.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ *Format Salah*\n\n"
            "Gunakan: `/adduser <telegram_id>`\n\n"
            "Contoh: `/adduser 123456789`",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    try:
        target_id = int(context.args[0])
        target_user = db.get_telegram_user(target_id)
        
        if target_user:
            # Update existing user
            success = db.add_telegram_user(
                telegram_id=target_id,
                username=target_user.get('username'),
                first_name=target_user.get('first_name'),
                last_name=target_user.get('last_name'),
                is_allowed=True,
                added_by=user_id,
                notes=f'Added by admin via /adduser'
            )
        else:
            # Add new user
            success = db.add_telegram_user(
                telegram_id=target_id,
                is_allowed=True,
                added_by=user_id,
                notes=f'Added by admin via /adduser'
            )
        
        if success:
            await update.message.reply_text(
                f"✅ *User Ditambahkan*\n\n"
                f"🆔 *ID:* `{target_id}`\n"
                f"✅ Status: *Diizinkan*\n\n"
                f"User sekarang dapat menggunakan bot.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            
            # Notify user jika mungkin
            try:
                from telegram import Bot
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                await bot.send_message(
                    chat_id=target_id,
                    text=(
                        "✅ *Akses Diberikan*\n\n"
                        "Anda sekarang dapat menggunakan bot ini!\n\n"
                        "Ketik `/start` untuk memulai."
                    ),
                    parse_mode='Markdown'
                )
            except:
                pass  # User mungkin belum pernah chat dengan bot
        else:
            await update.message.reply_text(
                "❌ *Gagal menambahkan user*\n\n"
                "Terjadi kesalahan saat menambahkan user ke database.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except ValueError:
        await update.message.reply_text(
            "❌ *ID Tidak Valid*\n\n"
            "ID Telegram harus berupa angka.\n\n"
            "Contoh: `/adduser 123456789`",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error adding user to whitelist: {e}")
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


async def remove_user_from_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove user from whitelist"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Hanya owner yang dapat menghapus user.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ *Format Salah*\n\n"
            "Gunakan: `/removeuser <telegram_id>`\n\n"
            "Contoh: `/removeuser 123456789`",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    try:
        target_id = int(context.args[0])
        success = db.remove_telegram_user(target_id)
        
        if success:
            await update.message.reply_text(
                f"✅ *User Dihapus*\n\n"
                f"🆔 *ID:* `{target_id}`\n"
                f"❌ Status: *Akses Dicabut*\n\n"
                f"User tidak dapat menggunakan bot lagi.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
        else:
            await update.message.reply_text(
                "❌ *Gagal menghapus user*\n\n"
                "Terjadi kesalahan saat menghapus user dari database.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
    except ValueError:
        await update.message.reply_text(
            "❌ *ID Tidak Valid*\n\n"
            "ID Telegram harus berupa angka.\n\n"
            "Contoh: `/removeuser 123456789`",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error removing user from whitelist: {e}")
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


async def list_whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all whitelisted users"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Hanya owner yang dapat melihat daftar user.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    try:
        users = db.get_all_telegram_users(only_allowed=True)
        
        if not users:
            await update.message.reply_text(
                "📋 *Daftar User*\n\n"
                "Tidak ada user yang terdaftar.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        message = f"📋 *Daftar User Terdaftar ({len(users)})*\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, user in enumerate(users[:20], 1):  # Limit to 20 users
            user_id_str = str(user.get('telegram_id', 'N/A'))
            username = user.get('username') or 'N/A'
            first_name = user.get('first_name') or 'N/A'
            last_name = user.get('last_name') or ''
            last_used = user.get('last_used')
            
            message += f"{idx}. 👤 *{first_name} {last_name}*\n"
            message += f"   🆔 ID: `{user_id_str}`\n"
            message += f"   📝 @{username}\n"
            if last_used:
                message += f"   🕐 Terakhir: {last_used}\n"
            message += "\n"
        
        if len(users) > 20:
            message += f"\n... dan {len(users) - 20} user lainnya"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


async def list_pending_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List users who tried to access but not yet allowed"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ *Akses Ditolak*\n\n"
            "Hanya owner yang dapat melihat daftar user pending.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    try:
        users = db.get_pending_telegram_users()
        
        if not users:
            await update.message.reply_text(
                "📋 *User Pending*\n\n"
                "Tidak ada user yang menunggu akses.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        message = f"🆕 *User Menunggu Akses ({len(users)})*\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "Gunakan `/adduser <id>` untuk memberikan akses\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, user in enumerate(users[:20], 1):  # Limit to 20 users
            user_id_str = str(user.get('telegram_id', 'N/A'))
            username = user.get('username') or 'N/A'
            first_name = user.get('first_name') or 'N/A'
            last_name = user.get('last_name') or ''
            added_at = user.get('added_at')
            
            message += f"{idx}. 👤 *{first_name} {last_name}*\n"
            message += f"   🆔 ID: `{user_id_str}`\n"
            message += f"   📝 @{username}\n"
            message += f"   ➕ Tambahkan: `/adduser {user_id_str}`\n"
            if added_at:
                message += f"   🕐 Mencoba akses: {added_at}\n"
            message += "\n"
        
        if len(users) > 20:
            message += f"\n... dan {len(users) - 20} user lainnya"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        logger.error(f"Error listing pending users: {e}")
        await update.message.reply_text(
            f"❌ *Error:* {str(e)}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(update.effective_user.id if update.effective_user else None)
        )


def format_field_value(value, max_length=200):
    """Format field value untuk Telegram, dengan batas panjang"""
    if value is None or value == '':
        return 'N/A'
    value_str = str(value)
    if len(value_str) > max_length:
        return value_str[:max_length] + '...'
    return value_str


async def send_person_detail_complete(update: Update, person: dict, index: int = None):
    """Send complete person detail seperti profiling.html - tanpa badge server"""
    if not isinstance(person, dict):
        return
    
    # Debug: Log person structure untuk melihat data yang tersedia
    logger.info(f"Person data keys: {list(person.keys())}")
    logger.info(f"Has family_data: {bool(person.get('family_data'))}")
    logger.info(f"Family data type: {type(person.get('family_data'))}")
    
    # Build complete message
    messages = []
    
    # Header tanpa server badge
    header = f"━━━━━━━━━━━━━━━━━━━━\n"
    if index:
        header += f"*📋 HASIL {index}*\n"
    header += f"━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Informasi Pribadi Lengkap
    full_name = person.get('full_name') or person.get('name', 'N/A')
    ktp_number = person.get('ktp_number') or person.get('nik', 'N/A')
    
    personal_info = f"*👤 INFORMASI PRIBADI*\n"
    personal_info += f"━━━━━━━━━━━━━━━━━━━━\n"
    personal_info += f"👤 *Nama Lengkap:* {format_field_value(full_name)}\n"
    personal_info += f"🆔 *NIK:* {format_field_value(ktp_number)}\n"
    personal_info += f"📅 *Tanggal Lahir:* {format_field_value(person.get('date_of_birth') or person.get('tanggal_lahir') or person.get('birth_date'))}\n"
    personal_info += f"📍 *Tempat Lahir:* {format_field_value(person.get('birth_place') or person.get('tempat_lahir'))}\n"
    personal_info += f"⚧️ *Jenis Kelamin:* {format_field_value(person.get('sex') or person.get('jenis_kelamin') or person.get('gender'))}\n"
    personal_info += f"💍 *Status Perkawinan:* {format_field_value(person.get('marital_status'))}\n"
    personal_info += f"🕌 *Agama:* {format_field_value(person.get('religion'))}\n"
    personal_info += f"💼 *Pekerjaan:* {format_field_value(person.get('occupation'))}\n"
    personal_info += f"🏠 *Alamat:* {format_field_value(person.get('address') or person.get('alamat'), max_length=300)}\n"
    personal_info += f"🗺️ *Provinsi:* {format_field_value(person.get('province_name') or person.get('provinsi'))}\n"
    personal_info += f"🏘️ *Kecamatan:* {format_field_value(person.get('district_name') or person.get('kecamatan'))}\n"
    personal_info += f"🏡 *Desa/Kelurahan:* {format_field_value(person.get('village_name') or person.get('desa') or person.get('kelurahan'))}\n"
    
    # Additional fields yang mungkin ada
    if person.get('rt'):
        personal_info += f"🏘️ *RT:* {format_field_value(person.get('rt'))}\n"
    if person.get('rw'):
        personal_info += f"🏘️ *RW:* {format_field_value(person.get('rw'))}\n"
    if person.get('kode_pos'):
        personal_info += f"📮 *Kode Pos:* {format_field_value(person.get('kode_pos'))}\n"
    if person.get('golongan_darah'):
        personal_info += f"🩸 *Golongan Darah:* {format_field_value(person.get('golongan_darah'))}\n"
    if person.get('kewarganegaraan'):
        personal_info += f"🌍 *Kewarganegaraan:* {format_field_value(person.get('kewarganegaraan'))}\n"
    if person.get('nama_ayah'):
        personal_info += f"👨 *Nama Ayah:* {format_field_value(person.get('nama_ayah'))}\n"
    if person.get('nama_ibu'):
        personal_info += f"👩 *Nama Ibu:* {format_field_value(person.get('nama_ibu'))}\n"
    
    # Phone Data
    phone_data = person.get('phone_data', [])
    if phone_data and isinstance(phone_data, list) and len(phone_data) > 0:
        personal_info += f"\n*📱 NOMOR TELEPON ({len(phone_data)})*\n"
        personal_info += f"━━━━━━━━━━━━━━━━━━━━\n"
        for idx, phone in enumerate(phone_data[:5], 1):  # Limit to 5 phones
            phone_num = phone.get('number') or phone.get('msisdn') or 'N/A'
            operator = phone.get('operator') or 'Unknown'
            register_date = phone.get('register_date') or 'N/A'
            personal_info += f"{idx}. *{phone_num}*\n"
            personal_info += f"   📶 Operator: {operator}\n"
            personal_info += f"   📅 Terdaftar: {register_date}\n"
        if len(phone_data) > 5:
            personal_info += f"\n... dan {len(phone_data) - 5} nomor lainnya\n"
    
    # Family Data - Otomatis muncul jika ada (dari server manapun)
    # Cek berbagai kemungkinan struktur data keluarga
    family_data = person.get('family_data', {})
    anggota_keluarga = []
    has_family_data = False
    
    # Debug logging
    logger.info(f"   Checking family data for {person.get('full_name', 'Unknown')}")
    logger.info(f"   person.get('family_data'): {bool(family_data)}, type: {type(family_data)}")
    
    # Cek 1: family_data sebagai dict dengan anggota_keluarga
    if family_data and isinstance(family_data, dict):
        anggota_keluarga = family_data.get('anggota_keluarga', [])
        logger.info(f"   Found family_data dict, anggota_keluarga: {len(anggota_keluarga) if isinstance(anggota_keluarga, list) else 'not list'}")
        if anggota_keluarga and isinstance(anggota_keluarga, list) and len(anggota_keluarga) > 0:
            has_family_data = True
            logger.info(f"   ✅ Has family_data with {len(anggota_keluarga)} members")
    
    # Cek 2: anggota_keluarga langsung di person (beberapa server mengirim langsung)
    if not has_family_data:
        anggota_keluarga = person.get('anggota_keluarga', [])
        logger.info(f"   Checking person.anggota_keluarga: {len(anggota_keluarga) if isinstance(anggota_keluarga, list) else 'not list'}")
        if anggota_keluarga and isinstance(anggota_keluarga, list) and len(anggota_keluarga) > 0:
            has_family_data = True
            logger.info(f"   ✅ Has anggota_keluarga at person level with {len(anggota_keluarga)} members")
            # Jika anggota_keluarga ada di root, coba ambil family_data lainnya juga
            if not family_data:
                family_data = {}
    
    # Cek 3: Cek field lain yang mungkin berisi data keluarga
    if not has_family_data:
        # Cek apakah ada field keluarga lainnya
        kepala_keluarga_check = person.get('kepala_keluarga')
        nkk_check = person.get('nkk') or person.get('family_cert_number')
        alamat_keluarga_check = person.get('alamat_keluarga')
        logger.info(f"   Checking other family fields: kepala_keluarga={bool(kepala_keluarga_check)}, nkk={bool(nkk_check)}, alamat={bool(alamat_keluarga_check)}")
        if kepala_keluarga_check or nkk_check or alamat_keluarga_check:
            has_family_data = True
            logger.info(f"   ✅ Has family data in other fields")
            if not family_data:
                family_data = {}
    
    # Tampilkan data keluarga jika ada - SELALU tampilkan jika ada data
    # Cek apakah ada family_data yang valid
    has_valid_family_data = False
    if family_data and isinstance(family_data, dict):
        # Cek apakah ada anggota_keluarga atau data keluarga lainnya
        if family_data.get('anggota_keluarga') or family_data.get('kepala_keluarga') or family_data.get('nkk'):
            has_valid_family_data = True
            logger.info(f"   ✅ Found family_data dict with data")
    
    # Juga cek di level person
    if not has_valid_family_data:
        if person.get('kepala_keluarga') or person.get('nkk') or person.get('alamat_keluarga') or person.get('anggota_keluarga'):
            has_valid_family_data = True
            logger.info(f"   ✅ Found family data at person level")
    
    # Log untuk debugging
    logger.info(f"   has_family_data: {has_family_data}, has_valid_family_data: {has_valid_family_data}")
    logger.info(f"   family_data type: {type(family_data)}, anggota_keluarga count: {len(anggota_keluarga) if anggota_keluarga else 0}")
    
    if has_valid_family_data or has_family_data:
        personal_info += f"\n*👨‍👩‍👧‍👦 DATA KELUARGA*\n"
        personal_info += f"━━━━━━━━━━━━━━━━━━━━\n"
        
        # Kepala Keluarga
        kepala_keluarga = None
        if family_data and isinstance(family_data, dict):
            kepala_keluarga = family_data.get('kepala_keluarga')
        if not kepala_keluarga:
            kepala_keluarga = person.get('kepala_keluarga') or person.get('nama_kepala_keluarga')
        if kepala_keluarga and kepala_keluarga != 'N/A' and kepala_keluarga != '':
            personal_info += f"👨 *Kepala Keluarga:* {format_field_value(kepala_keluarga)}\n"
        
        # NKK
        nkk = None
        if family_data and isinstance(family_data, dict):
            nkk = family_data.get('nkk')
        if not nkk:
            nkk = person.get('nkk') or person.get('nomor_kk') or person.get('no_kk') or person.get('family_cert_number')
        if nkk and nkk != 'N/A' and nkk != '':
            personal_info += f"🆔 *NKK:* {format_field_value(nkk)}\n"
        
        # Alamat Keluarga
        alamat_keluarga = None
        if family_data and isinstance(family_data, dict):
            alamat_keluarga = family_data.get('alamat_keluarga')
        if not alamat_keluarga:
            alamat_keluarga = person.get('alamat_keluarga')
        if alamat_keluarga and alamat_keluarga != 'N/A' and alamat_keluarga != '':
            personal_info += f"🏠 *Alamat Keluarga:* {format_field_value(alamat_keluarga, max_length=300)}\n"
        
        # Anggota Keluarga - SELALU tampilkan jika ada
        if anggota_keluarga and len(anggota_keluarga) > 0:
            personal_info += f"\n*Anggota Keluarga ({len(anggota_keluarga)}):*\n"
            logger.info(f"   ✅ Displaying {len(anggota_keluarga)} anggota keluarga")
            
            for idx, member in enumerate(anggota_keluarga[:10], 1):  # Limit to 10 members
                if not isinstance(member, dict):
                    continue
                    
                member_name = member.get('nama') or member.get('name', 'N/A')
                member_nik = member.get('nik') or member.get('ktp_number', 'N/A')
                hubungan = member.get('hubungan') or member.get('relationship') or member.get('status_hubungan', 'N/A')
                member_ttl = member.get('tanggal_lahir') or member.get('date_of_birth') or member.get('birth_date', 'N/A')
                member_jk = member.get('jenis_kelamin') or member.get('gender') or member.get('sex', 'N/A')
                
                personal_info += f"\n{idx}. *{member_name}*\n"
                personal_info += f"   🆔 NIK: {member_nik}\n"
                personal_info += f"   👤 Hubungan: {hubungan}\n"
                personal_info += f"   📅 TTL: {member_ttl}\n"
                personal_info += f"   ⚧️ JK: {member_jk}\n"
            
            if len(anggota_keluarga) > 10:
                personal_info += f"\n... dan {len(anggota_keluarga) - 10} anggota lainnya\n"
        else:
            # Jika tidak ada anggota_keluarga tapi ada data keluarga lainnya, tetap tampilkan header
            logger.info(f"   ⚠️ No anggota_keluarga found, but checking other fields...")
            if kepala_keluarga or nkk or alamat_keluarga:
                personal_info += f"\n*Data keluarga tersedia, namun detail anggota belum lengkap*\n"
            else:
                logger.info(f"   ⚠️ No family data found at all for this person")
    
    # Cek juga untuk informasi keluarga dasar (nama ayah/ibu) jika tidak ada data keluarga lengkap
    if not has_family_data:
        # Cek alternatif field names untuk family data
        if person.get('nama_ayah') or person.get('nama_ibu'):
            personal_info += f"\n*👨‍👩‍👧‍👦 INFORMASI KELUARGA*\n"
            personal_info += f"━━━━━━━━━━━━━━━━━━━━\n"
            if person.get('nama_ayah'):
                personal_info += f"👨 *Nama Ayah:* {format_field_value(person.get('nama_ayah'))}\n"
            if person.get('nama_ibu'):
                personal_info += f"👩 *Nama Ibu:* {format_field_value(person.get('nama_ibu'))}\n"
    
    # Combine header and personal info
    full_message = header + personal_info
    
    # Split message if too long (Telegram limit is 4096 characters)
    if len(full_message) > 4000:
        # Send in parts
        parts = []
        current_part = header + "*👤 INFORMASI PRIBADI*\n━━━━━━━━━━━━━━━━━━━━\n"
        
        # Split personal info into chunks
        lines = personal_info.split('\n')
        for line in lines:
            if len(current_part + line + '\n') > 4000:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        
        if current_part:
            parts.append(current_part)
        
        for part in parts:
            await update.message.reply_text(part, parse_mode='Markdown')
    else:
        await update.message.reply_text(full_message, parse_mode='Markdown')


async def send_search_results_from_people(update: Update, people: list):
    """Send search results from parsed people list (from parse_people_from_response) - LENGKAP seperti profiling.html"""
    user_id = update.effective_user.id
    
    if not people:
        await update.message.reply_text(
            "❌ *Data tidak ditemukan*\n\n"
            "Coba gunakan kata kunci yang lebih spesifik atau gunakan tombol menu untuk bantuan.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    # Send summary first
    total = len(people)
    await update.message.reply_text(
        f"✅ *Ditemukan {total} hasil pencarian*\n"
        f"Menampilkan data lengkap dari semua server...\n\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(user_id)
    )
    
    # Send each result with complete data (limit to 5 untuk menghindari spam)
    for idx, person in enumerate(people[:5], 1):
        await send_person_detail_complete(update, person, index=idx)
        # Small delay between messages to avoid rate limiting
        import asyncio
        await asyncio.sleep(0.5)
    
    if total > 5:
        await update.message.reply_text(
            f"⚠️ *Menampilkan 5 dari {total} hasil*\n"
            f"Gunakan pencarian yang lebih spesifik untuk melihat semua hasil.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )


async def send_search_results(update: Update, result: dict):
    """Send search results to user (legacy function for API response)"""
    if 'error' in result:
        await update.message.reply_text(f"❌ Error: {result['error']}")
        return
    
    # Check if result has people data
    people = result.get('people', [])
    if not people:
        await update.message.reply_text("❌ Data tidak ditemukan")
        return
    
    await send_search_results_from_people(update, people)


async def reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reports command"""
    # Cek akses user
    if not await check_user_access(update, context):
        return
    
    user_id = update.effective_user.id
    
    # Check if user is logged in
    if user_id not in user_credentials:
        await update.message.reply_text(
            "❌ Anda belum login!\n"
            "Gunakan /login <username> <password> terlebih dahulu"
        )
        return
    
    try:
        await update.message.reply_text("📊 Mengambil laporan...")
        
        # Get session token from stored credentials
        creds = user_credentials[user_id]
        session_token = creds.get('session_token')
        
        if not session_token:
            # Try to re-authenticate
            auth_result = authenticate_user(creds['username'], creds['password'], ip_address=None, user_agent='TelegramBot')
            if auth_result:
                session_token = auth_result.get('session_token', '')
                creds['session_token'] = session_token
            else:
                await update.message.reply_text("❌ Session expired. Silakan login lagi dengan /login")
                return
        
        # Get reports
        reports_response = requests.get(
            f"{API_BASE_URL}/api/profiling/reports",
            headers={
                'Authorization': f'Bearer {session_token}',
                'Content-Type': 'application/json'
            },
            params={'limit': 10},
            timeout=30
        )
        
        if reports_response.status_code == 200:
            reports_data = reports_response.json()
            if reports_data.get('success'):
                reports_list = reports_data.get('data', [])
                await send_reports_list(update, reports_list)
            else:
                await update.message.reply_text(f"❌ Error: {reports_data.get('error', 'Unknown error')}")
        else:
            await update.message.reply_text(f"❌ HTTP Error: {reports_response.status_code}")
            
    except Exception as e:
        logger.error(f"Error in reports: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def send_reports_list(update: Update, reports: list):
    """Send reports list to user"""
    if not reports:
        await update.message.reply_text("❌ Tidak ada laporan ditemukan")
        return
    
    await update.message.reply_text(f"📊 Ditemukan {len(reports)} laporan:")
    
    for idx, report in enumerate(reports[:10], 1):
        message = f"""
*Laporan {idx}:*
━━━━━━━━━━━━━━━━━━━━
👤 *Nama:* {report.get('nama', 'N/A')}
🆔 *NIK:* {report.get('nik', 'N/A')}
📍 *TTL:* {report.get('ttl', 'N/A')}
🏠 *Alamat:* {report.get('alamat', 'N/A')[:50]}...
📅 *Tanggal:* {report.get('tanggal_input', 'N/A')}
"""
        
        keyboard = [[InlineKeyboardButton(
            "📄 Detail",
            callback_data=f"report_{report.get('id')}"
        )]]
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    
    # Handle admin callbacks (cek owner dulu)
    if callback_data.startswith('admin_'):
        if not is_owner(user_id):
            await query.edit_message_text(
                "❌ *Akses Ditolak*\n\n"
                "Hanya owner yang dapat mengakses menu admin.",
                parse_mode='Markdown'
            )
            return
        
        if callback_data == 'admin_adduser':
            await query.edit_message_text(
                "➕ *Tambah User ke Whitelist*\n\n"
                "Kirim command:\n"
                "`/adduser <telegram_id>`\n\n"
                "Contoh:\n"
                "`/adduser 123456789`\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Atau gunakan `/pendingusers` untuk melihat user yang menunggu akses.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                ]])
            )
            return
        elif callback_data == 'admin_removeuser':
            # Set state untuk input ID
            user_admin_state[user_id] = 'waiting_remove_id'
            
            # Tampilkan list users yang terdaftar
            try:
                users = db.get_all_telegram_users(only_allowed=True) if db else []
                
                if users:
                    # Buat keyboard dengan tombol untuk setiap user
                    keyboard_buttons = []
                    for user in users[:10]:  # Limit 10 users
                        user_id_str = str(user.get('telegram_id', 'N/A'))
                        username = user.get('username') or 'N/A'
                        first_name = user.get('first_name') or 'N/A'
                        button_text = f"➖ {first_name} ({user_id_str})"
                        keyboard_buttons.append([InlineKeyboardButton(
                            button_text,
                            callback_data=f"admin_remove_{user_id_str}"
                        )])
                    
                    keyboard_buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")])
                    
                    message = (
                        "➖ *Hapus User dari Whitelist*\n\n"
                        "━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Pilih user dari daftar di bawah, atau:\n\n"
                        "Ketik ID Telegram yang ingin dihapus:\n"
                        "Contoh: `123456789`\n\n"
                        "━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"📋 *User Terdaftar ({len(users)}):*"
                    )
                    
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup(keyboard_buttons)
                    )
                else:
                    message = (
                        "➖ *Hapus User dari Whitelist*\n\n"
                        "━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Tidak ada user yang terdaftar.\n\n"
                        "Atau gunakan command:\n"
                        "`/removeuser <telegram_id>`"
                    )
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error showing remove user menu: {e}")
                await query.edit_message_text(
                    f"❌ Error: {str(e)}\n\n"
                    "Ketik ID Telegram yang ingin dihapus:\n"
                    "Contoh: `123456789`",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            return
        elif callback_data.startswith('admin_remove_'):
            # User klik tombol remove dari list
            target_id_str = callback_data.replace('admin_remove_', '')
            try:
                target_id = int(target_id_str)
                success = db.remove_telegram_user(target_id) if db else False
                
                if success:
                    await query.edit_message_text(
                        f"✅ *User Dihapus*\n\n"
                        f"🆔 *ID:* `{target_id}`\n"
                        f"❌ Status: *Akses Dicabut*\n\n"
                        f"User tidak dapat menggunakan bot lagi.",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="admin_back")
                        ]])
                    )
                else:
                    await query.edit_message_text(
                        "❌ *Gagal menghapus user*",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
            except ValueError:
                await query.edit_message_text(
                    "❌ ID tidak valid",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            except Exception as e:
                logger.error(f"Error removing user: {e}")
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            return
        elif callback_data == 'admin_listusers':
            try:
                users = db.get_all_telegram_users(only_allowed=True) if db else []
                if not users:
                    await query.edit_message_text(
                        "📋 *Daftar User*\n\n"
                        "Tidak ada user yang terdaftar.",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
                else:
                    message = f"📋 *User Terdaftar ({len(users)})*\n\n"
                    for idx, user in enumerate(users[:10], 1):
                        user_id_str = str(user.get('telegram_id', 'N/A'))
                        username = user.get('username') or 'N/A'
                        first_name = user.get('first_name') or 'N/A'
                        message += f"{idx}. 👤 *{first_name}*\n"
                        message += f"   🆔 `{user_id_str}`\n"
                        message += f"   📝 @{username}\n\n"
                    if len(users) > 10:
                        message += f"\n... dan {len(users) - 10} user lainnya"
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            return
        elif callback_data == 'admin_pendingusers':
            try:
                users = db.get_pending_telegram_users() if db else []
                if not users:
                    await query.edit_message_text(
                        "🆕 *User Pending*\n\n"
                        "Tidak ada user yang menunggu akses.",
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
                else:
                    message = f"🆕 *User Pending ({len(users)})*\n\n"
                    message += "Gunakan `/adduser <id>` untuk memberikan akses\n\n"
                    message += "━━━━━━━━━━━━━━━━━━━━\n\n"
                    for idx, user in enumerate(users[:10], 1):
                        user_id_str = str(user.get('telegram_id', 'N/A'))
                        username = user.get('username') or 'N/A'
                        first_name = user.get('first_name') or 'N/A'
                        message += f"{idx}. 👤 *{first_name}*\n"
                        message += f"   🆔 `{user_id_str}`\n"
                        message += f"   📝 @{username}\n"
                        message += f"   ➕ `/adduser {user_id_str}`\n\n"
                    if len(users) > 10:
                        message += f"\n... dan {len(users) - 10} user lainnya"
                    await query.edit_message_text(
                        message,
                        parse_mode='Markdown',
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                        ]])
                    )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            return
        elif callback_data == 'admin_stats':
            try:
                all_users = db.get_all_telegram_users() if db else []
                allowed_users = [u for u in all_users if u.get('is_allowed')]
                pending_users = [u for u in all_users if not u.get('is_allowed')]
                
                message = (
                    "📊 *Statistik Whitelist*\n\n"
                    f"✅ User Terdaftar: {len(allowed_users)}\n"
                    f"🆕 User Pending: {len(pending_users)}\n"
                    f"📋 Total: {len(all_users)}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━"
                )
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ Error: {str(e)}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="admin_back")
                    ]])
                )
            return
        elif callback_data == 'admin_back':
            keyboard = [
                [
                    InlineKeyboardButton("➕ Tambah User", callback_data="admin_adduser"),
                    InlineKeyboardButton("➖ Hapus User", callback_data="admin_removeuser")
                ],
                [
                    InlineKeyboardButton("📋 List User Terdaftar", callback_data="admin_listusers"),
                    InlineKeyboardButton("🆕 User Pending", callback_data="admin_pendingusers")
                ],
                [
                    InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")
                ]
            ]
            menu_text = (
                "🔐 *MENU ADMIN*\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📋 *Manage Whitelist:*\n\n"
                "Pilih menu di bawah atau gunakan command:\n\n"
                "`/adduser <telegram_id>` - Tambahkan user\n"
                "`/removeuser <telegram_id>` - Hapus user\n"
                "`/listusers` - Lihat user terdaftar\n"
                "`/pendingusers` - Lihat user pending\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💡 *Tips:*\n"
                "• User baru otomatis muncul di User Pending\n"
                "• Klik tombol untuk aksi cepat\n"
                "• ID user muncul saat mereka mencoba akses"
            )
            await query.edit_message_text(
                menu_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    # Untuk callback lainnya, cek akses normal
    if not is_owner(user_id):
        if not (db and db.is_telegram_user_allowed(user_id)):
            await query.edit_message_text(
                "🔒 *Akses Dibatasi*\n\n"
                "Anda tidak memiliki akses untuk menggunakan bot ini.",
                parse_mode='Markdown'
            )
            return
    
    data = callback_data
    
    if data.startswith('detail_'):
        profiling_id = data.replace('detail_', '')
        await show_profiling_detail(query, profiling_id)
    elif data.startswith('report_'):
        report_id = data.replace('report_', '')
        await show_report_detail(query, report_id)


async def show_profiling_detail(query, profiling_id: str):
    """Show detailed profiling information"""
    try:
        user_id = query.from_user.id
        if user_id not in user_credentials:
            await query.edit_message_text("❌ Session expired. Silakan login lagi.")
            return
        
        # Get session token from stored credentials
        creds = user_credentials[user_id]
        session_token = creds.get('session_token')
        
        if not session_token:
            # Try to re-authenticate
            auth_result = authenticate_user(creds['username'], creds['password'], ip_address=None, user_agent='TelegramBot')
            if auth_result:
                session_token = auth_result.get('session_token', '')
                creds['session_token'] = session_token
            else:
                await query.edit_message_text("❌ Session expired. Silakan login lagi dengan /login")
                return
        
        # Get profiling data detail
        # Try using profiling-data endpoint
        response = requests.get(
            f"{API_BASE_URL}/api/profiling-data",
            headers={
                'Authorization': f'Bearer {session_token}',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                profiling_list = data.get('data', [])
                # Find the specific profiling data
                profiling = next((p for p in profiling_list if str(p.get('id')) == profiling_id), None)
                
                if profiling:
                    person_data = profiling.get('person_data', {})
                    family_data = profiling.get('family_data', {})
                    
                    detail_message = f"""
*Detail Profiling:*
━━━━━━━━━━━━━━━━━━━━
👤 *Nama:* {person_data.get('full_name', 'N/A')}
🆔 *NIK:* {person_data.get('ktp_number', 'N/A')}
📍 *TTL:* {person_data.get('tempat_lahir', 'N/A')}, {person_data.get('tanggal_lahir', 'N/A')}
🏠 *Alamat:* {person_data.get('alamat', 'N/A')}
📱 *HP:* {person_data.get('phone_number', 'N/A')}
👨 *Ayah:* {family_data.get('nama_ayah', 'N/A')}
👩 *Ibu:* {family_data.get('nama_ibu', 'N/A')}
"""
                    await query.edit_message_text(detail_message, parse_mode='Markdown')
                else:
                    await query.edit_message_text("❌ Data tidak ditemukan")
            else:
                await query.edit_message_text(f"❌ Error: {data.get('error', 'Unknown')}")
        else:
            await query.edit_message_text(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error showing detail: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")


async def show_report_detail(query, report_id: str):
    """Show detailed report information"""
    try:
        user_id = query.from_user.id
        if user_id not in user_credentials:
            await query.edit_message_text("❌ Session expired. Silakan login lagi.")
            return
        
        # Get session token from stored credentials
        creds = user_credentials[user_id]
        session_token = creds.get('session_token')
        
        if not session_token:
            # Try to re-authenticate
            auth_result = authenticate_user(creds['username'], creds['password'], ip_address=None, user_agent='TelegramBot')
            if auth_result:
                session_token = auth_result.get('session_token', '')
                creds['session_token'] = session_token
            else:
                await query.edit_message_text("❌ Session expired. Silakan login lagi dengan /login")
                return
        
        # Get report detail
        response = requests.get(
            f"{API_BASE_URL}/api/profiling/reports/{report_id}",
            headers={
                'Authorization': f'Bearer {session_token}',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                report = data.get('data', {})
                
                detail_message = f"""
*Detail Laporan:*
━━━━━━━━━━━━━━━━━━━━
👤 *Nama:* {report.get('nama', 'N/A')}
🆔 *NIK:* {report.get('nik', 'N/A')}
📍 *TTL:* {report.get('ttl', 'N/A')}
🏠 *Alamat:* {report.get('alamat', 'N/A')}
📱 *HP:* {report.get('hp', 'N/A')}
👨 *Ayah:* {report.get('nama_ayah', 'N/A')}
👩 *Ibu:* {report.get('nama_ibu', 'N/A')}
💼 *Pekerjaan:* {report.get('pekerjaan', 'N/A')}
📅 *Tanggal Input:* {report.get('tanggal_input', 'N/A')}
"""
                await query.edit_message_text(detail_message, parse_mode='Markdown')
            else:
                await query.edit_message_text(f"❌ Error: {data.get('error', 'Unknown')}")
        else:
            await query.edit_message_text(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error showing report detail: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}")


def run_bot():
    """Run the Telegram bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN tidak ditemukan!")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("reports", reports))
    
    # Admin commands untuk manage whitelist
    application.add_handler(CommandHandler("adduser", add_user_to_whitelist))
    application.add_handler(CommandHandler("removeuser", remove_user_from_whitelist))
    application.add_handler(CommandHandler("listusers", list_whitelist_users))
    application.add_handler(CommandHandler("pendingusers", list_pending_users))
    application.add_handler(CommandHandler("admin", admin_menu))
    
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for menu buttons and direct text input
    # PENTING: Handler ini harus di-register SETELAH CommandHandler agar command tetap berfungsi
    # Handler ini akan menangkap semua text message yang bukan command (termasuk button press)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_button))
    
    logger.info("✅ All handlers registered successfully")
    print("[TELEGRAM_BOT] ✅ All handlers registered successfully", file=sys.stderr)
    
    # Start bot with proper event loop handling for thread
    logger.info("Starting Telegram bot...")
    
    # Create new event loop for this thread (required for Python 3.12+)
    # This must be done before calling run_polling
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Now run_polling will use the event loop we just set
        application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Clean up event loop
        try:
            loop.close()
        except:
            pass


if __name__ == '__main__':
    run_bot()

