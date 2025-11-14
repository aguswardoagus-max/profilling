import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

class UserDatabase:
    def __init__(self):
        self.connection = None
        self.init_database()
    
    def get_connection(self):
        """Get MySQL database connection - Fail gracefully if unavailable"""
        try:
            # Check if existing connection is still valid
            if self.connection is not None:
                try:
                    if self.connection.is_connected():
                        # Connection exists and is connected, return it
                        return self.connection
                    else:
                        # Not connected, close it
                        try:
                            self.connection.close()
                        except:
                            pass
                        self.connection = None
                except:
                    # Error checking connection, reset it
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None
            
            # Create new connection
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'clearance_facesearch'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=True,
                connection_timeout=5,  # Shorter timeout for faster fail
                raise_on_warnings=False
            )
            
            # Verify connection is actually connected
            if self.connection and self.connection.is_connected():
                return self.connection
            else:
                self.connection = None
                return None
                
        except Error as e:
            error_msg = str(e)
            # Only log if it's not a common connection error (to reduce noise)
            if "Lost connection" not in error_msg and "MySQL Connection not available" not in error_msg:
                print(f"Error connecting to MySQL: {e}")
            
            # Reset connection on error
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            return None
        except Exception as e:
            # Handle any unexpected errors
            error_msg = str(e)
            if "Connection" not in error_msg:  # Only log non-connection errors
                print(f"Unexpected error connecting to MySQL: {e}")
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            return None
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
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
            
            # API Keys table for multiple API key management with rotation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    api_key VARCHAR(255) NOT NULL,
                    api_type VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_CSE',
                    status ENUM('active', 'quota_exceeded', 'disabled', 'error') NOT NULL DEFAULT 'active',
                    usage_count INT DEFAULT 0,
                    last_used TIMESTAMP NULL,
                    quota_exceeded_at TIMESTAMP NULL,
                    error_message TEXT,
                    description VARCHAR(255),
                    priority INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_api_type (api_type),
                    INDEX idx_status (status),
                    INDEX idx_priority (priority),
                    INDEX idx_status_priority (status, priority)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
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

    # System Settings Methods
    def get_setting(self, setting_key: str) -> Optional[str]:
        """Get a system setting value by key - Fail gracefully if DB unavailable"""
        cursor = None
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            # Check if connection is actually usable
            try:
                if not conn.is_connected():
                    return None
            except:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_value FROM system_settings WHERE setting_key = %s
            ''', (setting_key,))
            
            result = cursor.fetchone()
            
            # Validate result before accessing
            if result is None:
                return None
            
            # Check if result has elements
            if not isinstance(result, (tuple, list)) or len(result) < 1:
                return None
            
            setting_value = result[0]
            
            # Validate setting value is not None
            if setting_value is None:
                return None
            
            return str(setting_value)
            
        except Error as e:
            error_msg = str(e)
            error_code = getattr(e, 'errno', None)
            
            # Only log if it's not a common connection error
            if error_code not in [2013, 2014] and "Lost connection" not in error_msg and "MySQL Connection not available" not in error_msg:
                print(f"Error getting setting: {e}")
            
            # Reset connection on error
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            return None
        except Exception as e:
            # Handle any unexpected errors (like NoneType subscriptable)
            error_msg = str(e)
            if "'NoneType' object is not subscriptable" in error_msg:
                # This means result was None or invalid - just return None silently
                pass
            else:
                print(f"Unexpected error getting setting: {e}")
            
            # Reset connection on error
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

    def update_setting(self, setting_key: str, setting_value: str, description: str = None) -> bool:
        """Update or insert a system setting"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Check if setting exists
            cursor.execute('SELECT id FROM system_settings WHERE setting_key = %s', (setting_key,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing setting
                if description:
                    cursor.execute('''
                        UPDATE system_settings 
                        SET setting_value = %s, description = %s, updated_at = NOW()
                        WHERE setting_key = %s
                    ''', (setting_value, description, setting_key))
                else:
                    cursor.execute('''
                        UPDATE system_settings 
                        SET setting_value = %s, updated_at = NOW()
                        WHERE setting_key = %s
                    ''', (setting_value, setting_key))
            else:
                # Insert new setting
                cursor.execute('''
                    INSERT INTO system_settings (setting_key, setting_value, description)
                    VALUES (%s, %s, %s)
                ''', (setting_key, setting_value, description))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error updating setting: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    # API Keys Management Methods
    def add_api_key(self, api_key: str, api_type: str = 'GOOGLE_CSE', description: str = None, priority: int = 0) -> bool:
        """Add a new API key (check for duplicates first)"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Check if API key already exists
            cursor.execute('''
                SELECT id FROM api_keys 
                WHERE api_key = %s AND api_type = %s
            ''', (api_key, api_type))
            
            existing = cursor.fetchone()
            if existing:
                # API key already exists, update it instead
                cursor.execute('''
                    UPDATE api_keys 
                    SET status = 'active', 
                        description = %s, 
                        priority = %s,
                        updated_at = NOW(),
                        quota_exceeded_at = NULL,
                        error_message = NULL
                    WHERE id = %s
                ''', (description, priority, existing[0]))
                conn.commit()
                return True
            
            # Insert new API key
            cursor.execute('''
                INSERT INTO api_keys (api_key, api_type, description, priority, status)
                VALUES (%s, %s, %s, %s, 'active')
            ''', (api_key, api_type, description, priority))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error adding API key: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_active_api_key(self, api_type: str = 'GOOGLE_CSE') -> Optional[str]:
        """Get the next active API key (with rotation) - Fail gracefully if DB unavailable"""
        cursor = None
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            # Check if connection is actually usable
            try:
                if not conn.is_connected():
                    return None
            except:
                return None
            
            cursor = conn.cursor()
            
            # Get active API key ordered by priority (higher first), then by last_used (oldest first for rotation)
            cursor.execute('''
                SELECT api_key, id FROM api_keys
                WHERE api_type = %s AND status = 'active'
                ORDER BY priority DESC, last_used ASC, id ASC
                LIMIT 1
            ''', (api_type,))
            
            result = cursor.fetchone()
            
            # Validate result before unpacking
            if result is None:
                return None
            
            # Check if result has enough elements
            if not isinstance(result, (tuple, list)) or len(result) < 2:
                return None
            
            api_key = result[0]
            key_id = result[1]
            
            # Validate API key is not None or empty
            if not api_key or not isinstance(api_key, str) or len(api_key.strip()) == 0:
                return None
            
            # Close cursor before update to avoid sync issues
            cursor.close()
            cursor = None
            
            # Try to update usage stats (non-critical, don't fail if it doesn't work)
            update_cursor = None
            try:
                # Check connection is still alive
                if conn and conn.is_connected():
                    update_cursor = conn.cursor()
                    update_cursor.execute('''
                        UPDATE api_keys 
                        SET usage_count = usage_count + 1, last_used = NOW()
                        WHERE id = %s
                    ''', (key_id,))
                    conn.commit()
            except Exception as update_error:
                # Silently ignore - stats update is not critical
                # The API key itself is what matters
                pass
            finally:
                if update_cursor:
                    try:
                        update_cursor.close()
                    except:
                        pass
            
            return api_key
            
        except Error as e:
            error_msg = str(e)
            error_code = getattr(e, 'errno', None)
            
            # Only log if it's not a common connection error
            if error_code not in [2013, 2014] and "Lost connection" not in error_msg and "MySQL Connection not available" not in error_msg:
                print(f"Error getting active API key: {e}")
            
            # Reset connection on error
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            return None
        except Exception as e:
            # Handle any unexpected errors (like NoneType subscriptable)
            error_msg = str(e)
            if "'NoneType' object is not subscriptable" in error_msg:
                # This means result was None or invalid - just return None silently
                pass
            else:
                print(f"Unexpected error getting active API key: {e}")
            
            # Reset connection on error
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                self.connection = None
            
            return None
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass

    def mark_api_key_quota_exceeded(self, api_key: str, error_message: str = None) -> bool:
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
                    error_message = %s
                WHERE api_key = %s
            ''', (error_message, api_key))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error marking API key quota exceeded: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def mark_api_key_error(self, api_key: str, error_message: str) -> bool:
        """Mark API key as error"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_keys 
                SET status = 'error', 
                    error_message = %s,
                    updated_at = NOW()
                WHERE api_key = %s
            ''', (error_message, api_key))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error marking API key error: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

    def get_all_api_keys(self, api_type: str = 'GOOGLE_CSE') -> List[Dict]:
        """Get all API keys for a type"""
        cursor = None
        try:
            conn = self.get_connection()
            if not conn:
                print("Warning: No database connection available for get_all_api_keys")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if table exists first
            cursor.execute('''
                SELECT COUNT(*) as table_exists
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'api_keys'
            ''')
            table_check = cursor.fetchone()
            
            if not table_check or table_check['table_exists'] == 0:
                print("Warning: api_keys table does not exist. Creating it now...")
                # Try to create the table
                try:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS api_keys (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            api_key VARCHAR(255) NOT NULL,
                            api_type VARCHAR(50) NOT NULL DEFAULT 'GOOGLE_CSE',
                            status ENUM('active', 'quota_exceeded', 'disabled', 'error') NOT NULL DEFAULT 'active',
                            usage_count INT DEFAULT 0,
                            last_used TIMESTAMP NULL,
                            quota_exceeded_at TIMESTAMP NULL,
                            error_message TEXT,
                            description VARCHAR(255),
                            priority INT DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                            INDEX idx_api_type (api_type),
                            INDEX idx_status (status),
                            INDEX idx_priority (priority),
                            INDEX idx_status_priority (status, priority)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    ''')
                    conn.commit()
                    print("Successfully created api_keys table")
                except Exception as create_error:
                    print(f"Error creating api_keys table: {create_error}")
                    return []
            
            cursor.execute('''
                SELECT id, api_key, status, usage_count, last_used, quota_exceeded_at, 
                       error_message, description, priority, created_at
                FROM api_keys
                WHERE api_type = %s
                ORDER BY priority DESC, created_at DESC
            ''', (api_type,))
            
            results = cursor.fetchall()
            
            # Mask API keys for security
            for result in results:
                if result['api_key'] and len(result['api_key']) > 14:
                    result['api_key_masked'] = f"{result['api_key'][:10]}...{result['api_key'][-4:]}"
                else:
                    result['api_key_masked'] = "***"
                # Don't expose full API key
                result['api_key'] = None
            
            return results
        except Error as e:
            import traceback
            print(f"Error getting API keys: {e}")
            print(traceback.format_exc())
            return []
        except Exception as e:
            import traceback
            print(f"Unexpected error getting API keys: {e}")
            print(traceback.format_exc())
            return []
        finally:
            if cursor:
                cursor.close()

    def update_api_key_status(self, key_id: int, status: str) -> bool:
        """Update API key status"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE api_keys 
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            ''', (status, key_id))
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error updating API key status: {e}")
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
            
            conn.commit()
            return True
        except Error as e:
            print(f"Error deleting API key: {e}")
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