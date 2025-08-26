#!/usr/bin/env python3
"""
Simple test script to verify the add_user.py functionality
"""

import sys
import os
import tempfile
import unittest

# Add the nginx directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_user import NginxUserManager


class TestNginxUserManager(unittest.TestCase):
    """Unit tests for NginxUserManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file for testing
        self.test_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf')
        self.test_config.write(self.get_sample_config())
        self.test_config.close()
        
        self.manager = NginxUserManager(self.test_config.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.test_config.name)
    
    def get_sample_config(self):
        """Get sample nginx configuration for testing."""
        return '''
# Sample nginx configuration for testing
upstream vscode_user1 {
    server 192.168.1.10:8080 max_fails=3 fail_timeout=30s;
    least_conn;
}

upstream jupyter_user1 {
    server 192.168.1.10:8088 max_fails=3 fail_timeout=30s;
    least_conn;
}

server {
    listen 80;
    
    location ~ ^/([^/]+)/vscode/(.*)$ {
        set $user $1;
        set $path $2;
        
        if ($user = "user1") {
            proxy_pass http://vscode_user1/$path$is_args$args;
        }
        if ($user = "user2") {
            proxy_pass http://vscode_user2/$path$is_args$args;
        }
    }
    
    location ~ ^/([^/]+)/jupyter/(.*)$ {
        set $user $1;
        set $path $2;
        
        if ($user = "user1") {
            proxy_pass http://jupyter_user1/$path$is_args$args;
        }
        proxy_pass http://jupyter_user2/$path$is_args$args;
    }
}
'''
    
    def test_validate_username(self):
        """Test username validation."""
        print("Testing username validation...")
        
        # Valid usernames
        self.assertTrue(self.manager.validate_username("user1"))
        self.assertTrue(self.manager.validate_username("test-user"))
        self.assertTrue(self.manager.validate_username("test_user"))
        self.assertTrue(self.manager.validate_username("user123"))
        
        # Invalid usernames
        self.assertFalse(self.manager.validate_username(""))
        self.assertFalse(self.manager.validate_username("user@test"))
        self.assertFalse(self.manager.validate_username("user.test"))
        self.assertFalse(self.manager.validate_username("user space"))
        
        print("  Username validation: PASSED")
    
    def test_validate_server_address(self):
        """Test server address validation."""
        print("Testing server address validation...")
        
        # Valid addresses
        self.assertTrue(self.manager.validate_server_address("192.168.1.10:8080"))
        self.assertTrue(self.manager.validate_server_address("127.0.0.1:3000"))
        self.assertTrue(self.manager.validate_server_address("10.0.0.1:65535"))
        
        # Invalid addresses
        self.assertFalse(self.manager.validate_server_address(""))
        self.assertFalse(self.manager.validate_server_address("192.168.1.10"))
        self.assertFalse(self.manager.validate_server_address("192.168.1.256:8080"))
        self.assertFalse(self.manager.validate_server_address("192.168.1.10:70000"))
        self.assertFalse(self.manager.validate_server_address("invalid:8080"))
        
        print("  Server address validation: PASSED")
    
    def test_check_user_exists(self):
        """Test user existence checking."""
        print("Testing user existence checking...")
        
        # Existing user
        self.assertTrue(self.manager.check_user_exists("user1"))
        
        # Non-existing user
        self.assertFalse(self.manager.check_user_exists("nonexistent"))
        
        print("  User existence checking: PASSED")
    
    def test_create_upstream_block(self):
        """Test upstream block creation."""
        print("Testing upstream block creation...")
        
        block = self.manager.create_upstream_block("vscode", "testuser", "192.168.1.10:8080")
        
        self.assertIn("upstream vscode_testuser", block)
        self.assertIn("server 192.168.1.10:8080", block)
        self.assertIn("least_conn", block)
        self.assertIn("zone vscode_testuser", block)
        
        print("  Upstream block creation: PASSED")
    
    def test_validate_inputs(self):
        """Test input validation."""
        print("Testing input validation...")
        
        # Valid inputs
        valid, msg = self.manager.validate_inputs("testuser", "192.168.1.10:8080", "192.168.1.10:8088")
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        # Invalid username
        valid, msg = self.manager.validate_inputs("invalid@user", "192.168.1.10:8080", "192.168.1.10:8088")
        self.assertFalse(valid)
        self.assertIn("Invalid username", msg)
        
        # Invalid vscode server
        valid, msg = self.manager.validate_inputs("testuser", "invalid:port", "192.168.1.10:8088")
        self.assertFalse(valid)
        self.assertIn("VSCode server", msg)
        
        # Invalid jupyter server
        valid, msg = self.manager.validate_inputs("testuser", "192.168.1.10:8080", "invalid:port")
        self.assertFalse(valid)
        self.assertIn("Jupyter server", msg)
        
        print("  Input validation: PASSED")


def main():
    """Run the tests."""
    print("Running NginxUserManager unit tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNginxUserManager)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("All tests PASSED!")
        return 0
    else:
        print("Some tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
