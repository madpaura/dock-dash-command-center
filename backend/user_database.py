# db_utilities.py
import mysql.connector
from mysql.connector import pooling
import hashlib
from datetime import datetime
import json
import os
from typing import Dict, List, Tuple, Optional

class DatabaseConfig:
    # Load database configuration from environment variables or config file
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', '0.0.0.0'),
            'database': os.getenv('DB_NAME', 'user_auth_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '12qwaszx'),
            'port': os.getenv('DB_PORT', 3306),
            'pool_name': 'mypool',
            'pool_size': 5
        }

class UserDatabase:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserDatabase, cls).__new__(cls)
            cls._setup_connection_pool()
        return cls._instance

    @classmethod
    def _setup_connection_pool(cls):
        if cls._pool is None:
            db_config = DatabaseConfig()
            print(db_config.config)
            cls._pool = mysql.connector.pooling.MySQLConnectionPool(**db_config.config)

    def _get_connection(self):
        return self._pool.get_connection()

    def initialize_database(self):
        """Create necessary tables if they don't exist"""
        create_tables_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(256) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            is_approved BOOLEAN DEFAULT FALSE,
            redirect_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            metadata JSON
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            session_token VARCHAR(256),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            action_type VARCHAR(50),
            action_details JSON,
            ip_address VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for query in create_tables_query.split(';'):
                if query.strip():
                    cursor.execute(query)
            conn.commit()

            # Create default admin if not exists
            self.create_default_admin()
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def create_default_admin(self):
        """Create default admin user if not exists"""
        admin_exists = self.get_user_by_username('admin')
        if not admin_exists:
            admin_data = {
                'username': 'admin',
                'password': hashlib.sha256('admin123'.encode()).hexdigest(),
                'email': 'admin@example.com',
                'is_admin': True,
                'is_approved': True
            }
            self.create_user(admin_data)

    def create_user(self, user_data: Dict) -> bool:
        """Create a new user"""
        query = """
        INSERT INTO users (username, password, email, is_admin, is_approved, metadata)
        VALUES (%(username)s, %(password)s, %(email)s, %(is_admin)s, %(is_approved)s, %(metadata)s)
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            metadata = user_data.get('metadata', {})
            cursor.execute(query, {
                'username': user_data['username'],
                'password': user_data['password'],
                'email': user_data['email'],
                'is_admin': user_data.get('is_admin', False),
                'is_approved': user_data.get('is_approved', False),
                'metadata': json.dumps(metadata)
            })
            conn.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = %s"
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by username"""
        query = "SELECT * FROM users WHERE id = %s"
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def delete_user_by_username(self, username: str) -> bool:
        """Delete a user by their username"""
        query = "DELETE FROM users WHERE username = %s"
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username,))
            conn.commit()
            
            # Check if any row was affected
            if cursor.rowcount > 0:
                return True
            else:
                return False
        except mysql.connector.Error as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update_user(self, user_id: int, update_data: Dict) -> bool:
        """Update user information"""
        allowed_fields = ['email', 'password', 'is_approved', 'is_admin', 'redirect_url', 'status', 'metadata']
        update_fields = []
        values = []
        
        for field in allowed_fields:
            if field in update_data:
                if field == 'metadata':  # Handle metadata separately
                    update_fields.append(f"{field} = %s")
                    values.append(json.dumps(update_data[field]))  # Convert dict to JSON string
                else:
                    update_fields.append(f"{field} = %s")
                    values.append(update_data[field])
            
        if not update_fields:
            return False

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        values.append(user_id)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return True
        except mysql.connector.Error as e:
            print(f"Error updating user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def verify_login(self, email    : str, password: str) -> Optional[Dict]:
        """Verify user login credentials"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = """
        SELECT * FROM users 
        WHERE email = %s AND password = %s AND status = 'active'
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (email, hashed_password))
            user = cursor.fetchone()
            
            if user:
                # Update last login timestamp
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()
            
            return user
        finally:
            cursor.close()
            conn.close()

    def get_pending_users(self) -> List[Dict]:
        """Get users pending approval"""
        query = """
        SELECT id, username, email, created_at 
        FROM users 
        WHERE is_approved = FALSE AND is_admin = FALSE
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_all_users(self, exclude_admin: bool = True) -> List[Dict]:
        """Get all users"""
        query = "SELECT * FROM users"
        # if exclude_admin:
        #     query += " WHERE is_admin = FALSE"
            
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def log_audit(self, user_id: int, action_type: str, action_details: Dict, ip_address: str):
        """Log user actions for audit"""
        query = """
        INSERT INTO audit_log (user_id, action_type, action_details, ip_address)
        VALUES (%s, %s, %s, %s)
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (
                user_id,
                action_type,
                json.dumps(action_details),
                ip_address
            ))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def log_audit_event(self, username: str, action_type: str, action_details: Dict, ip_address: str):
        """Log user actions for audit using username instead of user_id"""
        # Get user_id from username
        user = self.get_user_by_username(username)
        if user:
            user_id = user['id']
        else:
            # For system actions, create or get system user
            if username.lower() == 'system':
                user_id = self._get_or_create_system_user()
            else:
                # If user not found, try to use admin as fallback
                admin_user = self.get_user_by_username('admin')
                user_id = admin_user['id'] if admin_user else self._get_or_create_system_user()
        
        self.log_audit(user_id, action_type, action_details, ip_address)

    def _get_or_create_system_user(self) -> int:
        """Get or create a system user for audit logging"""
        # First try to get existing system user
        system_user = self.get_user_by_username('System')
        if system_user:
            return system_user['id']
        
        # Create system user if it doesn't exist
        query = """
        INSERT INTO users (username, password, email, is_admin, is_approved, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (
                'System',
                'system_user_no_login',  # System user cannot login
                'system@localhost',
                0,  # Not admin
                1,  # Approved
                'system'  # System status
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            # If system user already exists (race condition), get it
            system_user = self.get_user_by_username('System')
            if system_user:
                return system_user['id']
            raise e
        finally:
            cursor.close()
            conn.close()

    def create_session(self, user_id: int, session_token: str, expires_at: datetime) -> bool:
        """Create a new user session"""
        query = """
        INSERT INTO user_sessions (user_id, session_token, expires_at)
        VALUES (%s, %s, %s)
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (user_id, session_token, expires_at))
            conn.commit()
            return True
        except mysql.connector.Error:
            return False
        finally:
            cursor.close()
            conn.close()

    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify a session token"""
        query = """
        SELECT u.* FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP
        """
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (session_token,))
            session = cursor.fetchone()
            return session is not None
        finally:
            cursor.close()
            conn.close()

    def remove_session(self, session_token=None) -> bool:
        """Remove a session by ID or token"""
        if session_token:
            query = "DELETE FROM user_sessions WHERE session_token = %s"
            params = (session_token,)
        else:
            return False
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as e:
            print(f"Error removing session: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_audit_logs(self, username: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs with optional username filter"""
        if username and username != "All Users":
            query = """
            SELECT a.*, u.username 
            FROM audit_log a
            JOIN users u ON a.user_id = u.id
            WHERE u.username = %s
            ORDER BY a.timestamp DESC
            LIMIT %s
            """
            params = (username, limit)
        else:
            query = """
            SELECT a.*, u.username 
            FROM audit_log a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.timestamp DESC
            LIMIT %s
            """
            params = (limit,)
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
    
    def clear_audit_logs(self) -> bool:
        """Clear all audit logs from the database"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audit_log")
            conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing audit logs: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
