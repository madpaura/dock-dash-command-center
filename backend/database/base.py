"""Database manager for user authentication system."""

import mysql.connector
from mysql.connector import pooling
import logging
import os
from typing import Optional, Dict, Any
from .config import DatabaseConfig


class DatabaseManager:
    """Singleton database manager with connection pooling."""
    
    _instance = None
    _pool = None

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._setup_connection_pool()
        return cls._instance

    @classmethod
    def _setup_connection_pool(cls):
        """Set up MySQL connection pool."""
        if cls._pool is None:
            db_config = DatabaseConfig()
            print(f"Setting up database connection pool: {db_config.get_config()}")
            cls._pool = mysql.connector.pooling.MySQLConnectionPool(**db_config.get_config())

    def get_connection(self):
        """Get a connection from the pool."""
        return self._pool.get_connection()

    def initialize_database(self):
        """Create necessary tables if they don't exist."""
        create_tables_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(256) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            is_approved BOOLEAN DEFAULT FALSE,
            user_type ENUM('regular', 'qvp', 'admin') DEFAULT 'regular',
            status ENUM('active', 'inactive', 'suspended', 'system') DEFAULT 'active',
            redirect_url VARCHAR(255),
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action_type VARCHAR(100) NOT NULL,
            action_details JSON,
            ip_address VARCHAR(45),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_access_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            session_token VARCHAR(255),
            ip_address VARCHAR(45) NOT NULL,
            user_agent TEXT,
            endpoint VARCHAR(255),
            method VARCHAR(10),
            status_code INT,
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_start TIMESTAMP,
            session_end TIMESTAMP,
            duration_seconds INT,
            bytes_sent BIGINT DEFAULT 0,
            bytes_received BIGINT DEFAULT 0,
            INDEX idx_user_id (user_id),
            INDEX idx_ip_address (ip_address),
            INDEX idx_access_time (access_time),
            INDEX idx_session_token (session_token),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS password_reset_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('pending', 'completed', 'rejected') DEFAULT 'pending',
            admin_id INT,
            completed_at TIMESTAMP NULL,
            reason TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_status (status),
            INDEX idx_user_id (user_id)
        );

        CREATE TABLE IF NOT EXISTS registry_servers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            url VARCHAR(255) NOT NULL,
            registry_type ENUM('docker_hub', 'private', 'gcr', 'ecr', 'acr', 'harbor') DEFAULT 'private',
            username VARCHAR(100),
            password VARCHAR(255),
            is_default BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            metadata JSON,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_name (name),
            INDEX idx_is_active (is_active)
        );

        CREATE TABLE IF NOT EXISTS build_projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            repo_url VARCHAR(500) NOT NULL,
            repo_branch VARCHAR(100) DEFAULT 'main',
            dockerfile_path VARCHAR(255) DEFAULT 'Dockerfile',
            build_context VARCHAR(255) DEFAULT '.',
            git_pat VARCHAR(500),
            default_registry_id INT,
            image_name VARCHAR(255),
            auto_increment_tag BOOLEAN DEFAULT TRUE,
            last_tag VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            metadata JSON,
            created_by INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (default_registry_id) REFERENCES registry_servers(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_name (name),
            INDEX idx_is_active (is_active)
        );

        CREATE TABLE IF NOT EXISTS build_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            registry_id INT,
            tag VARCHAR(100) NOT NULL,
            status ENUM('pending', 'cloning', 'building', 'pushing', 'completed', 'failed') DEFAULT 'pending',
            build_logs LONGTEXT,
            error_message TEXT,
            image_digest VARCHAR(255),
            image_size BIGINT,
            git_commit VARCHAR(100),
            triggered_by INT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            duration_seconds INT,
            metadata JSON,
            FOREIGN KEY (project_id) REFERENCES build_projects(id) ON DELETE CASCADE,
            FOREIGN KEY (registry_id) REFERENCES registry_servers(id) ON DELETE SET NULL,
            FOREIGN KEY (triggered_by) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_project_id (project_id),
            INDEX idx_status (status),
            INDEX idx_started_at (started_at)
        );
        """
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for statement in create_tables_query.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            conn.commit()
            print("Database tables initialized successfully")
            
            # Run migrations for existing databases
            self._run_migrations(cursor, conn)
            
            # Create default admin user if it doesn't exist
            self._create_default_admin()
            
        except mysql.connector.Error as e:
            print(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def _run_migrations(self, cursor, conn):
        """Run database migrations for schema updates."""
        try:
            # Check if user_type column exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'users' 
                AND column_name = 'user_type'
            """)
            result = cursor.fetchone()
            
            if result[0] == 0:
                print("Running migration: Adding user_type column...")
                # Add user_type column
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN user_type ENUM('regular', 'qvp', 'admin') DEFAULT 'regular'
                    AFTER is_approved
                """)
                
                # Migrate existing data: is_admin=true -> user_type='admin'
                cursor.execute("""
                    UPDATE users SET user_type = 'admin' WHERE is_admin = TRUE
                """)
                
                conn.commit()
                print("Migration completed: user_type column added and data migrated")
        except mysql.connector.Error as e:
            print(f"Migration warning (may be safe to ignore): {e}")

    def _create_default_admin(self):
        """Create default admin user if it doesn't exist."""
        from .user_repository import UserRepository
        import hashlib
        
        user_repo = UserRepository()
        admin_user = user_repo.get_user_by_username('admin')
        if not os.path.exists("admin.env"):
            raise Exception("admin.env file not found")

        from dotenv import load_dotenv
        load_dotenv("admin.env")

        if not admin_user:
            print("Creating default admin user...")
            admin_data = {
                'username': os.getenv('ADMIN_USERNAME'),
                'password': hashlib.sha256(os.getenv('ADMIN_PASSWORD').encode()).hexdigest(),
                'email': os.getenv('ADMIN_EMAIL'),
                'is_admin': True,
                'is_approved': True,
                'user_type': 'admin'
            }
            user_repo.create_user(admin_data)
            print("Default admin user created successfully")

