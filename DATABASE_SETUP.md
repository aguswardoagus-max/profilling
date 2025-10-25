# Database Setup Guide

## MySQL Database Setup for Clearance Face Search

### Prerequisites

1. **MySQL Server** (version 5.7 or higher)
2. **Python 3.7+**
3. **mysql-connector-python** package

### Installation Steps

#### 1. Install MySQL Server

**Windows:**
```bash
# Download MySQL Installer from https://dev.mysql.com/downloads/installer/
# Or use Chocolatey
choco install mysql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
```

**macOS:**
```bash
# Using Homebrew
brew install mysql
```

#### 2. Start MySQL Service

**Windows:**
```bash
# Start MySQL service
net start mysql
```

**Ubuntu/Debian:**
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
```

**macOS:**
```bash
brew services start mysql
```

#### 3. Secure MySQL Installation

```bash
sudo mysql_secure_installation
```

#### 4. Create Database User (Optional)

```sql
-- Login to MySQL as root
mysql -u root -p

-- Create database user
CREATE USER 'clearance_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON clearance_facesearch.* TO 'clearance_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 5. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 6. Configure Environment Variables

Copy the example configuration file:
```bash
cp config_example.env .env
```

Edit `.env` file with your database credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=clearance_facesearch
```

#### 7. Run Database Setup

**Option 1: Using Python Script (Recommended)**
```bash
python setup_database.py
```

**Option 2: Using SQL Script**
```bash
mysql -u root -p < database_setup.sql
```

### Database Schema

The setup creates the following tables:

#### 1. `users` Table
- **id**: Primary key (AUTO_INCREMENT)
- **username**: Unique username (VARCHAR 50)
- **email**: Unique email (VARCHAR 100)
- **password_hash**: Hashed password (TEXT)
- **full_name**: Full name (VARCHAR 100)
- **role**: User role (ENUM: admin, user, viewer)
- **status**: User status (ENUM: active, inactive, pending)
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp
- **last_login**: Last login timestamp
- **login_attempts**: Failed login attempts counter
- **locked_until**: Account lock expiration

#### 2. `sessions` Table
- **id**: Primary key (AUTO_INCREMENT)
- **user_id**: Foreign key to users table
- **session_token**: Unique session token (VARCHAR 255)
- **created_at**: Session creation timestamp
- **expires_at**: Session expiration timestamp
- **ip_address**: Client IP address (VARCHAR 45)
- **user_agent**: Client user agent (TEXT)
- **is_active**: Session status (BOOLEAN)

#### 3. `user_activities` Table
- **id**: Primary key (AUTO_INCREMENT)
- **user_id**: Foreign key to users table
- **activity_type**: Type of activity (VARCHAR 50)
- **description**: Activity description (TEXT)
- **ip_address**: Client IP address (VARCHAR 45)
- **user_agent**: Client user agent (TEXT)
- **created_at**: Activity timestamp

#### 4. `system_settings` Table
- **id**: Primary key (AUTO_INCREMENT)
- **setting_key**: Setting key (VARCHAR 100)
- **setting_value**: Setting value (TEXT)
- **description**: Setting description (TEXT)
- **updated_at**: Last update timestamp

### Default Users

After setup, the following users are created:

| Username | Password | Role | Status |
|----------|----------|------|--------|
| admin | admin123 | admin | active |
| user1 | admin123 | user | active |
| viewer1 | admin123 | viewer | active |
| user2 | admin123 | user | pending |

### Troubleshooting

#### Connection Issues

1. **Check MySQL Service:**
   ```bash
   # Windows
   net start mysql
   
   # Linux/macOS
   sudo systemctl status mysql
   ```

2. **Check MySQL Port:**
   ```bash
   netstat -an | grep 3306
   ```

3. **Test Connection:**
   ```bash
   mysql -u root -p -h localhost -P 3306
   ```

#### Permission Issues

1. **Grant Privileges:**
   ```sql
   GRANT ALL PRIVILEGES ON clearance_facesearch.* TO 'your_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

2. **Check User Permissions:**
   ```sql
   SHOW GRANTS FOR 'your_user'@'localhost';
   ```

#### Database Creation Issues

1. **Check Database Exists:**
   ```sql
   SHOW DATABASES;
   ```

2. **Drop and Recreate:**
   ```sql
   DROP DATABASE IF EXISTS clearance_facesearch;
   CREATE DATABASE clearance_facesearch CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

### Security Considerations

1. **Change Default Passwords:**
   - Change the default admin password immediately
   - Use strong passwords for database users

2. **Network Security:**
   - Use SSL connections in production
   - Restrict database access to application servers only

3. **Backup Strategy:**
   ```bash
   # Create backup
   mysqldump -u root -p clearance_facesearch > backup.sql
   
   # Restore backup
   mysql -u root -p clearance_facesearch < backup.sql
   ```

### Production Deployment

For production deployment:

1. **Use Environment Variables:**
   ```bash
   export DB_HOST=your_production_host
   export DB_PORT=3306
   export DB_USER=your_production_user
   export DB_PASSWORD=your_secure_password
   export DB_NAME=clearance_facesearch
   ```

2. **Enable SSL:**
   ```python
   connection = mysql.connector.connect(
       host=host,
       user=user,
       password=password,
       database=database,
       ssl_disabled=False,
       ssl_verify_cert=True,
       ssl_verify_identity=True
   )
   ```

3. **Connection Pooling:**
   ```python
   from mysql.connector import pooling
   
   config = {
       'user': 'user',
       'password': 'password',
       'host': 'localhost',
       'database': 'clearance_facesearch',
       'pool_name': 'mypool',
       'pool_size': 10
   }
   
   connection_pool = pooling.MySQLConnectionPool(**config)
   ```

### Monitoring

1. **Check Database Status:**
   ```sql
   SHOW PROCESSLIST;
   SHOW STATUS;
   ```

2. **Monitor User Activities:**
   ```sql
   SELECT * FROM user_activities ORDER BY created_at DESC LIMIT 10;
   ```

3. **Check Active Sessions:**
   ```sql
   SELECT u.username, s.created_at, s.expires_at 
   FROM sessions s 
   JOIN users u ON s.user_id = u.id 
   WHERE s.is_active = 1 AND s.expires_at > NOW();
   ```

### Support

If you encounter issues:

1. Check the application logs
2. Verify database connectivity
3. Ensure all environment variables are set correctly
4. Check MySQL error logs

For additional help, refer to the MySQL documentation or contact the development team.
