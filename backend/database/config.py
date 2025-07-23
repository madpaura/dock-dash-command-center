"""Database configuration management."""

import os
from typing import Dict


class DatabaseConfig:
    """Database configuration class that loads settings from environment variables."""
    
    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.config = {
            'host': os.getenv('DB_HOST', '0.0.0.0'),
            'database': os.getenv('DB_NAME', 'user_auth_db'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', '12qwaszx'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'pool_name': 'mypool',
            'pool_size': 5
        }
    
    def get_config(self) -> Dict:
        """Get database configuration dictionary."""
        return self.config.copy()
