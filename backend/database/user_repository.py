"""User repository for database operations."""

import mysql.connector
import hashlib
import json
from typing import Dict, List, Optional
from .base import DatabaseManager


class UserRepository:
    """Repository class for user-related database operations."""
    
    def __init__(self):
        """Initialize user repository."""
        self.db_manager = DatabaseManager()
    
    def create_user(self, user_data: Dict) -> bool:
        """Create a new user."""
        query = """
        INSERT INTO users (username, password, email, is_admin, is_approved, metadata)
        VALUES (%(username)s, %(password)s, %(email)s, %(is_admin)s, %(is_approved)s, %(metadata)s)
        """
        conn = self.db_manager.get_connection()
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
        """Get user by username."""
        query = "SELECT * FROM users WHERE username = %s"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (username,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (email,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def delete_user_by_username(self, username: str) -> bool:
        """Delete a user by their username."""
        query = "DELETE FROM users WHERE username = %s"
        
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (username,))
            conn.commit()
            
            # Check if any row was affected
            return cursor.rowcount > 0
        except mysql.connector.Error as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update_user(self, user_id: int, update_data: Dict) -> bool:
        """Update user information."""
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

        conn = self.db_manager.get_connection()
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

    def verify_login(self, email: str, password: str) -> Optional[Dict]:
        """Verify user login credentials."""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = """
        SELECT * FROM users 
        WHERE email = %s AND password = %s AND status = 'active'
        """
        
        conn = self.db_manager.get_connection()
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
        """Get users pending approval."""
        query = """
        SELECT id, username, email, created_at 
        FROM users 
        WHERE is_approved = FALSE AND is_admin = FALSE AND username != 'System' AND status != 'system'
        """
        
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_all_users(self, exclude_admin: bool = True) -> List[Dict]:
        """Get all users."""
        query = "SELECT * FROM users"
        # Note: exclude_admin parameter is preserved for backward compatibility
        # but currently not used as per the original implementation
            
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_or_create_system_user(self) -> int:
        """Get or create a system user for audit logging."""
        # First try to get existing system user
        system_user = self.get_user_by_username('System')
        if system_user:
            return system_user['id']
        
        # Create system user if it doesn't exist
        query = """
        INSERT INTO users (username, password, email, is_admin, is_approved, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        conn = self.db_manager.get_connection()
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
