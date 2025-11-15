import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import threading

class UserDatabase:
    def __init__(self):
        # Use thread-local storage for connections (thread-safe)
        self._local = threading.local()
        self._init_connection = None  # Only for init_database
        self.init_database()
    
    def get_connection(self, force_new=False):
        """Get MySQL database connection - thread-safe version"""
        try:
            # Get thread-local connection
            if not force_new and hasattr(self._local, 'connection'):
                conn = self._local.connection
                if conn is not None:
                    try:
                        # Quick check if connection is still alive
                        if hasattr(conn, 'is_connected') and conn.is_connected():
                            return conn
                        else:
                            # Connection is dead, close it
                            try:
                                conn.close()
                            except:
                                pass
                            self._local.connection = None
                    except:
                        # Error checking, assume dead
                        try:
                            conn.close()
                        except:
                            pass
                        self._local.connection = None
            
            # Create new connection for this thread
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'clearance_facesearch'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=True,
                connect_timeout=30,  # Increased timeout
                sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION',
                use_unicode=True,
                raise_on_warnings=False
            )
            
            # Store in thread-local storage
            self._local.connection = conn
            return conn
            
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            if hasattr(self._local, 'connection'):
                self._local.connection = None
            return None
        except Exception as e:
            print(f"Unexpected error connecting to MySQL: {e}")
            if hasattr(self._local, 'connection'):
                self._local.connection = None
            return None
    
    def init_database(self):
        """Initialize the database with required tables"""
        # Use a separate connection for initialization
        try:
            self._init_connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'clearance_facesearch'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=True,
                connect_timeout=30
            )
            conn = self._init_connection
        except Exception as e:
            print(f"Failed to connect to MySQL database for initialization: {e}")
            return
        
        if not conn:
            print("Failed to connect to MySQL database")
            return
        
        cursor = conn.cursor()
        
        try:
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    role ENUM('admin', 'user', 'viewer') NOT NULL DEFAULT 'user',
                    status ENUM('active', 'inactive', 'pending') NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    login_attempts INT DEFAULT 0,
                    locked_until TIMESTAMP NULL,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    INDEX idx_session_token (session_token),
                    INDEX idx_user_id (user_id),
                    INDEX idx_expires_at (expires_at),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # User activities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    description TEXT,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_activity_type (activity_type),
                    INDEX idx_created_at (created_at),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # System settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_setting_key (setting_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # API keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    api_key VARCHAR(255) NOT NULL,
                    api_type VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_CSE',
                    status ENUM('active', 'inactive', 'quota_exceeded') NOT NULL DEFAULT 'active',
                    usage_count INT DEFAULT 0,
                    daily_limit INT DEFAULT 100,
                    last_used TIMESTAMP NULL,
                    quota_exceeded_at TIMESTAMP NULL,
                    error_message TEXT,
                    description TEXT,
                    priority INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_api_type (api_type),
                    INDEX idx_status (status),
                    INDEX idx_priority (priority),
                    INDEX idx_last_used (last_used)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Migrate existing api_keys table - add missing columns if they don't exist
            try:
                # Check and add daily_limit column
                cursor.execute('''
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'daily_limit'
                ''')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('ALTER TABLE api_keys ADD COLUMN daily_limit INT DEFAULT 100')
                    print("Added daily_limit column to api_keys table")
                
                # Check and add priority column
                cursor.execute('''
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'priority'
                ''')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('ALTER TABLE api_keys ADD COLUMN priority INT DEFAULT 0')
                    print("Added priority column to api_keys table")
                
                # Check and add description column
                cursor.execute('''
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'description'
                ''')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('ALTER TABLE api_keys ADD COLUMN description TEXT')
                    print("Added description column to api_keys table")
                
                # Check and add error_message column
                cursor.execute('''
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'error_message'
                ''')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('ALTER TABLE api_keys ADD COLUMN error_message TEXT')
                    print("Added error_message column to api_keys table")
                
                # Check and add quota_exceeded_at column
                cursor.execute('''
                    SELECT COUNT(*) as col_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'quota_exceeded_at'
                ''')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('ALTER TABLE api_keys ADD COLUMN quota_exceeded_at TIMESTAMP NULL')
                    print("Added quota_exceeded_at column to api_keys table")
                
                # Check and update status ENUM if needed (add quota_exceeded if missing)
                cursor.execute('''
                    SELECT COLUMN_TYPE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'api_keys'
                    AND COLUMN_NAME = 'status'
                ''')
                status_result = cursor.fetchone()
                if status_result and 'quota_exceeded' not in status_result[0]:
                    try:
                        cursor.execute('''
                            ALTER TABLE api_keys 
                            MODIFY COLUMN status ENUM('active', 'inactive', 'quota_exceeded') 
                            NOT NULL DEFAULT 'active'
                        ''')
                        print("Updated status ENUM to include quota_exceeded")
                    except Error as e:
                        print(f"Note: Could not update status ENUM (may already be correct): {e}")
                
            except Error as e:
                print(f"Error migrating api_keys table: {e}")
                # Continue anyway - table might already have all columns
            
            # Profiling data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS profiling_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    search_type ENUM('identity', 'phone', 'face') NOT NULL,
                    search_params TEXT,
                    search_results TEXT,
                    person_data TEXT,
                    family_data TEXT,
                    phone_data TEXT,
                    face_data TEXT,
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    INDEX idx_user_id (user_id),
                    INDEX idx_search_type (search_type),
                    INDEX idx_search_timestamp (search_timestamp),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Cek plat data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cek_plat_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    no_polisi VARCHAR(20) NOT NULL,
                    nama_pemilik VARCHAR(255),
                    alamat TEXT,
                    merk_kendaraan VARCHAR(100),
                    type_kendaraan VARCHAR(100),
                    model_kendaraan VARCHAR(100),
                    tahun_pembuatan INT,
                    warna_kendaraan VARCHAR(50),
                    no_rangka VARCHAR(50),
                    no_mesin VARCHAR(50),
                    silinder VARCHAR(20),
                    bahan_bakar VARCHAR(50),
                    masa_berlaku_stnk DATE,
                    masa_berlaku_pajak DATE,
                    status_kendaraan VARCHAR(50),
                    coordinates_lat DECIMAL(10, 8),
                    coordinates_lon DECIMAL(11, 8),
                    accuracy_score DECIMAL(5, 2),
                    accuracy_details TEXT,
                    display_name VARCHAR(255),
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    INDEX idx_user_id (user_id),
                    INDEX idx_no_polisi (no_polisi),
                    INDEX idx_search_timestamp (search_timestamp),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Create default admin user if not exists
            self.create_default_admin()
            
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def create_default_admin(self):
        """Create default admin user if no users exist"""
        if not self.user_exists('admin'):
            self.create_user(
                username='admin',
                email='admin@clearancefacesearch.com',
                password='admin123',
                full_name='System Administrator',
                role='admin'
            )
            print("Default admin user created: admin/admin123")
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_part = password_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == hash_part
        except:
            return False
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str, role: str = 'user', status: str = 'active') -> bool:
        """Create a new user"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, email, password_hash, full_name, role, status))
            
            return True
        except Error as e:
            if e.errno == 1062:  # Duplicate entry
                return False
            print(f"Error creating user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data if successful"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, password_hash, full_name, role, status,
                       login_attempts, locked_until
                FROM users WHERE username = %s OR email = %s
            ''', (username, username))
            
            user = cursor.fetchone()
            if not user:
                return None
            
            user_id, db_username, email, password_hash, full_name, role, status, login_attempts, locked_until = user
            
            # Check if account is locked
            if locked_until and datetime.now() < locked_until:
                return None
            
            # Verify password
            if not self.verify_password(password, password_hash):
                # Increment login attempts
                cursor.execute('''
                    UPDATE users SET login_attempts = login_attempts + 1
                    WHERE id = %s
                ''', (user_id,))
                
                # Lock account after 5 failed attempts
                if login_attempts + 1 >= 5:
                    lock_until = datetime.now() + timedelta(minutes=30)
                    cursor.execute('''
                        UPDATE users SET locked_until = %s
                        WHERE id = %s
                    ''', (lock_until, user_id))
                
                return None
            
            # Reset login attempts on successful login
            cursor.execute('''
                UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = NOW()
                WHERE id = %s
            ''', (user_id,))
            
            return {
                'id': user_id,
                'username': db_username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'status': status
            }
        except Error as e:
            print(f"Error authenticating user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """Create a new session for user"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))
            
            return session_token
        except Error as e:
            print(f"Error creating session: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user data"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, s.expires_at, u.username, u.email, u.full_name, u.role, u.status
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = %s AND s.is_active = 1 AND s.expires_at > %s
            ''', (session_token, datetime.now()))
            
            session = cursor.fetchone()
            if not session:
                return None
            
            user_id, expires_at, username, email, full_name, role, status = session
            
            # Check if user is still active
            if status != 'active':
                return None
            
            return {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'role': role,
                'status': status
            }
        except Error as e:
            print(f"Error validating session: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def logout_session(self, session_token: str) -> bool:
        """Logout user by deactivating session"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions SET is_active = 0 WHERE session_token = %s
            ''', (session_token,))
            
            return True
        except Error as e:
            print(f"Error logging out session: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, full_name, role, status, created_at, last_login
                FROM users ORDER BY created_at DESC
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'role': row[4],
                    'status': row[5],
                    'created_at': row[6].isoformat() if row[6] else None,
                    'last_login': row[7].isoformat() if row[7] else None
                })
            
            return users
        except Error as e:
            print(f"Error getting users: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['username', 'email', 'full_name', 'role', 'status']:
                    update_fields.append(f"{key} = %s")
                    values.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = NOW()")
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            
            return True
        except Error as e:
            print(f"Error updating user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def delete_user(self, user_id: int, soft_delete: bool = False) -> bool:
        """Delete user (hard delete by default, or soft delete if specified)"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            if soft_delete:
                # Soft delete: set status to inactive
                cursor.execute('''
                    UPDATE users SET status = 'inactive', updated_at = NOW()
                    WHERE id = %s
                ''', (user_id,))
                
                # Also deactivate all sessions
                cursor.execute('''
                    UPDATE sessions SET is_active = 0 WHERE user_id = %s
                ''', (user_id,))
            else:
                # Hard delete: completely remove from database
                # First delete related records
                cursor.execute('DELETE FROM user_activities WHERE user_id = %s', (user_id,))
                cursor.execute('DELETE FROM sessions WHERE user_id = %s', (user_id,))
                
                # Then delete the user
                cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def log_activity(self, user_id: int, activity_type: str, description: str, 
                    ip_address: str = None, user_agent: str = None):
        """Log user activity"""
        try:
            conn = self.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activities (user_id, activity_type, description, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, activity_type, description, ip_address, user_agent))
            
        except Error as e:
            print(f"Error logging activity: {e}")
        finally:
            if cursor:
                cursor.close()
    
    def get_user_activities(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """Get user activities"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT ua.activity_type, ua.description, ua.ip_address, ua.created_at, u.username
                    FROM user_activities ua
                    JOIN users u ON ua.user_id = u.id
                    WHERE ua.user_id = %s
                    ORDER BY ua.created_at DESC
                    LIMIT %s
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT ua.activity_type, ua.description, ua.ip_address, ua.created_at, u.username
                    FROM user_activities ua
                    JOIN users u ON ua.user_id = u.id
                    ORDER BY ua.created_at DESC
                    LIMIT %s
                ''', (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'activity_type': row[0],
                    'description': row[1],
                    'ip_address': row[2],
                    'created_at': row[3].isoformat() if row[3] else None,
                    'username': row[4]
                })
            
            return activities
        except Error as e:
            print(f"Error getting activities: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, username))
            exists = cursor.fetchone() is not None
            
            return exists
        except Error as e:
            print(f"Error checking user existence: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error getting user by username: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Profiling Data Methods
    def save_profiling_data(self, user_id: int, search_type: str, search_params: dict, 
                           search_results: dict, person_data: dict = None, family_data: dict = None,
                           phone_data: dict = None, face_data: dict = None, 
                           ip_address: str = None, user_agent: str = None) -> bool:
        """Save profiling search data to database"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Check if NIK already exists in person_data
            if person_data and person_data.get('ktp_number'):
                nik = person_data.get('ktp_number')
                cursor.execute('''
                    SELECT COUNT(*) FROM profiling_data 
                    WHERE person_data LIKE %s
                ''', (f'%"ktp_number": "{nik}"%',))
                
                existing_count = cursor.fetchone()[0]
                if existing_count > 0:
                    print(f"Data with NIK {nik} already exists. Skipping save.")
                    return False
            
            cursor.execute('''
                INSERT INTO profiling_data 
                (user_id, search_type, search_params, search_results, person_data, 
                 family_data, phone_data, face_data, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id, search_type, 
                json.dumps(search_params) if search_params else None,
                json.dumps(search_results) if search_results else None,
                json.dumps(person_data) if person_data else None,
                json.dumps(family_data) if family_data else None,
                json.dumps(phone_data) if phone_data else None,
                json.dumps(face_data) if face_data else None,
                ip_address, user_agent
            ))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error saving profiling data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_profiling_data(self, user_id: int = None, search_type: str = None, 
                          limit: int = 100, offset: int = 0) -> list:
        """Get profiling data with optional filters"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build query with optional filters
            query = '''
                SELECT pd.*, u.username, u.full_name as user_name
                FROM profiling_data pd
                JOIN users u ON pd.user_id = u.id
            '''
            conditions = []
            params = []
            
            if user_id:
                conditions.append('pd.user_id = %s')
                params.append(user_id)
            
            if search_type:
                conditions.append('pd.search_type = %s')
                params.append(search_type)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY pd.search_timestamp DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Parse JSON fields
            for result in results:
                for field in ['search_params', 'search_results', 'person_data', 
                             'family_data', 'phone_data', 'face_data']:
                    if result[field]:
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            result[field] = None
            
            return results
        except Error as e:
            print(f"Error getting profiling data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_profiling_data_count(self, user_id: int = None, search_type: str = None) -> int:
        """Get count of profiling data with optional filters"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM profiling_data pd'
            conditions = []
            params = []
            
            if user_id:
                conditions.append('pd.user_id = %s')
                params.append(user_id)
            
            if search_type:
                conditions.append('pd.search_type = %s')
                params.append(search_type)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            return count
        except Error as e:
            print(f"Error getting profiling data count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_profiling_data(self, profiling_id: int) -> bool:
        """Delete profiling data by ID"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM profiling_data WHERE id = %s', (profiling_id,))
            conn.commit()
            
            return True
        except Error as e:
            print(f"Error deleting profiling data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Cek Plat Data Methods
    def save_cekplat_data(self, user_id: int, no_polisi: str, nama_pemilik: str = None, 
                         alamat: str = None, merk_kendaraan: str = None, type_kendaraan: str = None,
                         model_kendaraan: str = None, tahun_pembuatan: str = None, 
                         warna_kendaraan: str = None, no_rangka: str = None, no_mesin: str = None,
                         silinder: str = None, bahan_bakar: str = None, masa_berlaku_stnk: str = None,
                         masa_berlaku_pajak: str = None, status_kendaraan: str = None,
                         coordinates_lat: float = None, coordinates_lon: float = None,
                         accuracy_score: float = None, accuracy_details: str = None,
                         display_name: str = None, ip_address: str = None, user_agent: str = None) -> bool:
        """Save cek plat search data to database"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO cek_plat_data 
                (user_id, no_polisi, nama_pemilik, alamat, merk_kendaraan, type_kendaraan, 
                 model_kendaraan, tahun_pembuatan, warna_kendaraan, no_rangka, no_mesin, 
                 silinder, bahan_bakar, masa_berlaku_stnk, masa_berlaku_pajak, status_kendaraan,
                 coordinates_lat, coordinates_lon, accuracy_score, accuracy_details, display_name,
                 ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id, no_polisi, nama_pemilik, alamat, merk_kendaraan, type_kendaraan,
                model_kendaraan, tahun_pembuatan, warna_kendaraan, no_rangka, no_mesin,
                silinder, bahan_bakar, masa_berlaku_stnk, masa_berlaku_pajak, status_kendaraan,
                coordinates_lat, coordinates_lon, accuracy_score, accuracy_details, display_name,
                ip_address, user_agent
            ))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error saving cek plat data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_cekplat_data(self, user_id: int = None, limit: int = 100, offset: int = 0) -> list:
        """Get cek plat data with optional filters"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build query with optional filters
            query = '''
                SELECT cpd.*, u.username, u.full_name as user_name
                FROM cek_plat_data cpd
                JOIN users u ON cpd.user_id = u.id
            '''
            conditions = []
            params = []
            
            if user_id:
                conditions.append('cpd.user_id = %s')
                params.append(user_id)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY cpd.search_timestamp DESC LIMIT %s OFFSET %s'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return results
        except Error as e:
            print(f"Error getting cek plat data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_cekplat_data_count(self, user_id: int = None) -> int:
        """Get count of cek plat data with optional filters"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0
            
            cursor = conn.cursor()
            
            query = 'SELECT COUNT(*) FROM cek_plat_data cpd'
            conditions = []
            params = []
            
            if user_id:
                conditions.append('cpd.user_id = %s')
                params.append(user_id)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            return count
        except Error as e:
            print(f"Error getting cek plat data count: {e}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_cekplat_data(self, cekplat_id: int) -> bool:
        """Delete cek plat data by ID"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cek_plat_data WHERE id = %s', (cekplat_id,))
            conn.commit()
            
            return True
        except Error as e:
            print(f"Error deleting cek plat data: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Dashboard Statistics Methods
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor(dictionary=True)
            stats = {}
            
            # Total searches (from profiling_data)
            cursor.execute('SELECT COUNT(*) as total FROM profiling_data')
            result = cursor.fetchone()
            stats['total_searches'] = result['total'] if result else 0
            
            # Active users (users with recent login)
            cursor.execute('''
                SELECT COUNT(*) as active_users 
                FROM users 
                WHERE status = 'active' 
                AND last_login > DATE_SUB(NOW(), INTERVAL 7 DAY)
            ''')
            result = cursor.fetchone()
            stats['active_users'] = result['active_users'] if result else 0
            
            # Face matches (face search type)
            cursor.execute('''
                SELECT COUNT(*) as face_matches 
                FROM profiling_data 
                WHERE search_type = 'face'
            ''')
            result = cursor.fetchone()
            stats['face_matches'] = result['face_matches'] if result else 0
            
            # System alerts (failed searches or errors)
            cursor.execute('''
                SELECT COUNT(*) as system_alerts 
                FROM user_activities 
                WHERE activity_type = 'error' 
                AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
            ''')
            result = cursor.fetchone()
            stats['system_alerts'] = result['system_alerts'] if result else 0
            
            # Search types distribution
            cursor.execute('''
                SELECT search_type, COUNT(*) as count 
                FROM profiling_data 
                GROUP BY search_type
            ''')
            search_types = cursor.fetchall()
            stats['search_types'] = {row['search_type']: row['count'] for row in search_types}
            
            # Daily activity (last 7 days)
            cursor.execute('''
                SELECT DATE(search_timestamp) as date, 
                       COUNT(*) as profiling_searches
                FROM profiling_data 
                WHERE search_timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(search_timestamp)
                ORDER BY date
            ''')
            daily_activity = cursor.fetchall()
            stats['daily_activity'] = daily_activity
            
            # Cek plat daily activity (last 7 days)
            cursor.execute('''
                SELECT DATE(search_timestamp) as date,
                       COUNT(*) as cek_plat_searches
                FROM cek_plat_data
                WHERE search_timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(search_timestamp)
                ORDER BY date
            ''')
            cek_plat_daily_activity = cursor.fetchall()
            stats['cek_plat_daily_activity'] = cek_plat_daily_activity

            # Cek plat data count
            cursor.execute('SELECT COUNT(*) as cek_plat_count FROM cek_plat_data')
            result = cursor.fetchone()
            stats['cek_plat_searches'] = result['cek_plat_count'] if result else 0
            
            # Cek plat by region (first 2 letters of no_polisi)
            cursor.execute('''
                SELECT SUBSTRING(no_polisi, 1, 2) as region, COUNT(*) as count
                FROM cek_plat_data 
                GROUP BY SUBSTRING(no_polisi, 1, 2)
                ORDER BY count DESC
                LIMIT 7
            ''')
            cek_plat_regions = cursor.fetchall()
            stats['cek_plat_regions'] = cek_plat_regions
            
            # Recent activities
            cursor.execute('''
                SELECT ua.activity_type, ua.description, ua.created_at, u.username
                FROM user_activities ua
                JOIN users u ON ua.user_id = u.id
                ORDER BY ua.created_at DESC
                LIMIT 5
            ''')
            recent_activities = cursor.fetchall()
            stats['recent_activities'] = recent_activities
            
            return stats
            
        except Error as e:
            print(f"Error getting dashboard stats: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # API Keys Management Methods
    def get_api_key(self, api_type: str = 'GOOGLE_CSE') -> Optional[str]:
        """Get an active API key from database with rotation logic"""
        max_retries = 3  # Increased retries for better reliability
        for attempt in range(max_retries):
            cursor = None
            conn = None
            try:
                # Always get fresh connection for thread safety (each thread gets its own)
                conn = self.get_connection(force_new=True)
                if not conn:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(0.1 * (attempt + 1))  # Small delay before retry
                        continue
                    return None
                
                # Use a single cursor for all operations to avoid sync issues
                cursor = conn.cursor(buffered=True)
                
                # Set connection timeout to prevent hanging
                try:
                    cursor.execute("SET SESSION wait_timeout = 300")
                    cursor.execute("SET SESSION interactive_timeout = 300")
                except:
                    pass  # Ignore if can't set timeout
                
                # Get the best available API key
                cursor.execute('''
                    SELECT id, api_key, usage_count, daily_limit, last_used
                    FROM api_keys
                    WHERE api_type = %s AND status = 'active'
                    ORDER BY priority DESC, (last_used IS NULL) DESC, last_used ASC, id ASC
                    LIMIT 1
                ''', (api_type,))
                
                result = cursor.fetchone()
                
                # Validate result before unpacking - check None first!
                if result is None:
                    if cursor:
                        cursor.close()
                    return None
                
                # Check if result has enough elements (must be tuple/list with 5 elements)
                try:
                    if len(result) < 5:
                        if cursor:
                            cursor.close()
                        return None
                except (TypeError, AttributeError):
                    # Result is not a sequence, can't unpack
                    if cursor:
                        cursor.close()
                    return None
                
                # Now safe to unpack
                try:
                    key_id, api_key, usage_count, daily_limit, last_used = result
                except (ValueError, TypeError) as e:
                    # Can't unpack - wrong number of values or wrong type
                    print(f"Error unpacking result: {e}, result: {result}")
                    if cursor:
                        cursor.close()
                    return None
                
                # Validate all values are not None
                if key_id is None or api_key is None:
                    if cursor:
                        cursor.close()
                    return None
                
                # Check if daily limit is exceeded
                if daily_limit and daily_limit > 0 and usage_count and usage_count >= daily_limit:
                    # Check if it's a new day (reset usage)
                    if last_used and hasattr(last_used, 'date') and last_used.date() < datetime.now().date():
                        # Reset usage count for new day
                        cursor.execute('''
                            UPDATE api_keys SET usage_count = 0 WHERE id = %s
                        ''', (key_id,))
                        usage_count = 0
                    else:
                        # Try next key
                        cursor.execute('''
                            SELECT id, api_key, usage_count, daily_limit, last_used
                            FROM api_keys
                            WHERE api_type = %s AND status = 'active' AND id != %s
                            ORDER BY priority DESC, (last_used IS NULL) DESC, last_used ASC, id ASC
                            LIMIT 1
                        ''', (api_type, key_id))
                        next_result = cursor.fetchone()
                        
                        # Validate next_result before unpacking - check None first!
                        if next_result is None:
                            if cursor:
                                cursor.close()
                            return None
                        
                        # Check if next_result has enough elements
                        try:
                            if len(next_result) < 5:
                                if cursor:
                                    cursor.close()
                                return None
                        except (TypeError, AttributeError):
                            # next_result is not a sequence
                            if cursor:
                                cursor.close()
                            return None
                        
                        # Now safe to unpack
                        try:
                            key_id, api_key, usage_count, daily_limit, last_used = next_result
                        except (ValueError, TypeError) as e:
                            # Can't unpack
                            print(f"Error unpacking next_result: {e}, result: {next_result}")
                            if cursor:
                                cursor.close()
                            return None
                        
                        # Validate values are not None
                        if key_id is None or api_key is None:
                            if cursor:
                                cursor.close()
                            return None
                
                # Update last_used and increment usage_count
                cursor.execute('''
                    UPDATE api_keys 
                    SET usage_count = usage_count + 1, last_used = NOW()
                    WHERE id = %s
                ''', (key_id,))
                
                # Close cursor before returning
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                    cursor = None
                
                # Close connection after use (thread-safe: each thread has its own)
                if conn:
                    try:
                        # Don't close thread-local connection, just clear it if needed
                        # Connection will be reused in same thread
                        pass
                    except:
                        pass
                
                return api_key
                
            except Error as e:
                error_msg = str(e)
                print(f"Error getting API key (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Close cursor on error
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                    cursor = None
                
                # Close connection on error
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    # Clear thread-local connection
                    if hasattr(self._local, 'connection'):
                        self._local.connection = None
                
                # If it's a connection/packet error and we have retries left, try again
                if (('Lost connection' in error_msg or 'not available' in error_msg or 
                     'Malformed packet' in error_msg or '2027' in error_msg) and 
                    attempt < max_retries - 1):
                    import time
                    time.sleep(0.2 * (attempt + 1))  # Delay before retry
                    continue
                
                # If no more retries or different error, return None
                if attempt >= max_retries - 1:
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Unexpected error getting API key (attempt {attempt + 1}/{max_retries}): {e}")
                
                # Close cursor on error
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                    cursor = None
                
                # Close connection on error
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    # Clear thread-local connection
                    if hasattr(self._local, 'connection'):
                        self._local.connection = None
                
                # If it's a subscriptable error or fetch error, try again with fresh connection
                if (('subscriptable' in error_msg or 'fetch' in error_msg.lower() or 
                     'NoneType' in error_msg) and attempt < max_retries - 1):
                    import time
                    time.sleep(0.2 * (attempt + 1))  # Delay before retry
                    continue
                
                # If no more retries, return None
                if attempt >= max_retries - 1:
                    return None
        
        return None
    
    def get_all_api_keys(self, api_type: str = None) -> List[Dict]:
        """Get all API keys with optional filter by type"""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            if api_type:
                cursor.execute('''
                    SELECT id, api_key, api_type, status, usage_count, daily_limit,
                           last_used, quota_exceeded_at, error_message, description,
                           priority, created_at, updated_at
                    FROM api_keys
                    WHERE api_type = %s
                    ORDER BY priority DESC, created_at DESC
                ''', (api_type,))
            else:
                cursor.execute('''
                    SELECT id, api_key, api_type, status, usage_count, daily_limit,
                           last_used, quota_exceeded_at, error_message, description,
                           priority, created_at, updated_at
                    FROM api_keys
                    ORDER BY api_type, priority DESC, created_at DESC
                ''')
            
            results = cursor.fetchall()
            
            # Format datetime fields
            for result in results:
                if result.get('last_used'):
                    result['last_used'] = result['last_used'].isoformat() if hasattr(result['last_used'], 'isoformat') else str(result['last_used'])
                if result.get('quota_exceeded_at'):
                    result['quota_exceeded_at'] = result['quota_exceeded_at'].isoformat() if hasattr(result['quota_exceeded_at'], 'isoformat') else str(result['quota_exceeded_at'])
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat() if hasattr(result['created_at'], 'isoformat') else str(result['created_at'])
                if result.get('updated_at'):
                    result['updated_at'] = result['updated_at'].isoformat() if hasattr(result['updated_at'], 'isoformat') else str(result['updated_at'])
                # Mask API key for security (show only first 10 and last 10 chars)
                if result.get('api_key'):
                    key = result['api_key']
                    if len(key) > 20:
                        result['api_key_masked'] = f"{key[:10]}...{key[-10:]}"
                    else:
                        result['api_key_masked'] = "***"
            
            return results
        except Error as e:
            print(f"Error getting API keys: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def create_api_key(self, api_key: str, api_type: str = 'GOOGLE_CSE', 
                      description: str = None, priority: int = 0, 
                      daily_limit: int = 100, status: str = 'active') -> bool:
        """Create a new API key"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_keys (api_key, api_type, description, priority, daily_limit, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (api_key, api_type, description, priority, daily_limit, status))
            
            return True
        except Error as e:
            print(f"Error creating API key: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def update_api_key(self, key_id: int, **kwargs) -> bool:
        """Update API key information"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            allowed_fields = ['api_key', 'api_type', 'status', 'description', 'priority', 
                            'daily_limit', 'usage_count', 'error_message', 'quota_exceeded_at']
            
            for key, value in kwargs.items():
                if key in allowed_fields:
                    update_fields.append(f"{key} = %s")
                    values.append(value)
            
            if not update_fields:
                return False
            
            update_fields.append("updated_at = NOW()")
            values.append(key_id)
            
            query = f"UPDATE api_keys SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            
            return True
        except Error as e:
            print(f"Error updating API key: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_keys WHERE id = %s', (key_id,))
            
            return True
        except Error as e:
            print(f"Error deleting API key: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def mark_api_key_quota_exceeded(self, key_id: int, error_message: str = None) -> bool:
        """Mark API key as quota exceeded"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_keys 
                SET status = 'quota_exceeded', 
                    quota_exceeded_at = NOW(),
                    error_message = %s,
                    updated_at = NOW()
                WHERE id = %s
            ''', (error_message, key_id))
            
            return True
        except Error as e:
            print(f"Error marking API key quota exceeded: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def reset_api_key_usage(self, key_id: int = None) -> bool:
        """Reset usage count for API key(s) - useful for daily reset"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            if key_id:
                cursor.execute('''
                    UPDATE api_keys 
                    SET usage_count = 0, 
                        status = CASE 
                            WHEN status = 'quota_exceeded' THEN 'active'
                            ELSE status
                        END,
                        quota_exceeded_at = NULL,
                        error_message = NULL
                    WHERE id = %s
                ''', (key_id,))
            else:
                # Reset all keys that haven't been used today
                cursor.execute('''
                    UPDATE api_keys 
                    SET usage_count = 0,
                        status = CASE 
                            WHEN status = 'quota_exceeded' THEN 'active'
                            ELSE status
                        END,
                        quota_exceeded_at = NULL,
                        error_message = NULL
                    WHERE DATE(last_used) < CURDATE() OR last_used IS NULL
                ''')
            
            return True
        except Error as e:
            print(f"Error resetting API key usage: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def log_export_audit(self, user_id: int, export_type: str, record_ids: list, 
                        filename: str, file_path: str, ip_address: str = None, 
                        user_agent: str = None) -> bool:
        """Log export audit trail"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activities (user_id, activity_type, description, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, 'export', 
                  f'Exported {len(record_ids)} records to {export_type}: {filename}', 
                  ip_address, user_agent))
            
            return True
        except Error as e:
            print(f"Error logging export audit: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

# Global database instance
db = UserDatabase()

# Helper functions for Flask integration
def authenticate_user(username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
    """Authenticate user and create session"""
    user = db.authenticate_user(username, password)
    if user:
        session_token = db.create_session(user['id'], ip_address, user_agent)
        if session_token:
            db.log_activity(user['id'], 'login', f'User {username} logged in', ip_address, user_agent)
            return {
                'user': user,
                'session_token': session_token
            }
    return None

def validate_session_token(session_token: str) -> Optional[Dict]:
    """Validate session token"""
    return db.validate_session(session_token)

def logout_user(session_token: str, user_id: int = None):
    """Logout user"""
    success = db.logout_session(session_token)
    if success and user_id:
        db.log_activity(user_id, 'logout', 'User logged out')
    return success