#!/usr/bin/env python3
"""
Nginx User Routing Test Suite

Comprehensive test suite for the nginx user management system.
Tests both the Python script functionality and the actual nginx routing.
"""

import subprocess
import time
import requests
import sys
import os
import tempfile
import shutil
import unittest
from pathlib import Path

# Add the nginx directory to the path to import the add_user module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from add_user import NginxUserManager

def run_command(command, description):
    """Run a shell command and return the result"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("  Success")
            return True, result.stdout
        else:
            print(f"  Failed: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"  Error: {e}")
        return False, str(e)

def start_dummy_services():
    """Start the dummy services"""
    print("Starting dummy VSCode and Jupyter services...")
    # Start the dummy services in the background
    result = subprocess.Popen([sys.executable, "dummy_services.py"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)  # Give services time to start
    return result

def stop_dummy_services(process):
    """Stop the dummy services"""
    print("Stopping dummy services...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def remove_test_user():
    """Remove testuser from nginx configuration if it exists"""
    manager = NginxUserManager()
    
    try:
        if manager.check_user_exists("testuser"):
            print("Removing existing testuser configuration")
            success = manager.remove_user("testuser")
            if not success:
                print("Warning: Failed to remove existing testuser configuration")
        else:
            print("No existing testuser configuration found")
            
    except Exception as e:
        print(f"Error removing testuser: {e}")
        return False

def add_test_user():
    """Add a test user using the add_user.py script"""
    # First remove existing testuser if present
    remove_test_user()
    
    command = "python3 ../add_user.py testuser 127.0.0.1:8080 127.0.0.1:8088"
    success, output = run_command(command, "Add test user")
    return success

def test_service_access():
    """Test accessing the services through NGINX"""
    print("Testing service access through NGINX...")
    
    tests = [
        ("http://localhost/testuser/vscode/", "VSCode service for testuser"),
        ("http://localhost/testuser/jupyter/", "Jupyter service for testuser")
    ]
    
    results = []
    for url, description in tests:
        try:
            print(f"  Testing {description}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and "Dummy" in response.text:
                print(f"    Success: {description}")
                results.append(True)
            else:
                print(f"    Failed: {description} - Status {response.status_code}")
                results.append(False)
        except requests.exceptions.RequestException as e:
            print(f"    Error: {description} - {e}")
            results.append(False)
    
    return all(results)

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
    
    def test_validate_server_address(self):
        """Test server address validation."""
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
    
    def test_check_user_exists(self):
        """Test user existence checking."""
        # Existing user
        self.assertTrue(self.manager.check_user_exists("user1"))
        
        # Non-existing user
        self.assertFalse(self.manager.check_user_exists("nonexistent"))
    
    def test_create_upstream_block(self):
        """Test upstream block creation."""
        block = self.manager.create_upstream_block("vscode", "testuser", "192.168.1.10:8080")
        
        self.assertIn("upstream vscode_testuser", block)
        self.assertIn("server 192.168.1.10:8080", block)
        self.assertIn("least_conn", block)
        self.assertIn("zone vscode_testuser", block)


def main():
    """Main test execution function."""
    print("Starting NGINX user routing comprehensive test suite...")
    
    # Run unit tests first
    print("\n=== Running Unit Tests ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    print("\n=== Running Integration Tests ===")
    
    # Start dummy services
    dummy_process = start_dummy_services()
    
    try:
        # Wait a moment for services to fully start
        time.sleep(2)
        
        # Test the actual script functionality
        success = test_script_integration()
        
        if success:
            print("\nAll integration tests passed! NGINX user routing is working correctly.")
        else:
            print("\nSome integration tests failed. Check the output above for details.")
            
        return success
        
    finally:
        # Stop dummy services
        stop_dummy_services(dummy_process)
        
        # Clean up test user
        remove_test_user()


def test_script_integration():
    """Test the actual script integration with nginx."""
    print("Testing script integration...")
    
    # Add test user
    if not add_test_user():
        print("Failed to add test user. Exiting.")
        return False
    
    # Wait for NGINX to reload
    time.sleep(3)
    
    # Test service access
    success = test_service_access()
    
    # Test additional functionality
    if success:
        success = test_user_management_features()
    
    return success


def test_user_management_features():
    """Test additional user management features."""
    print("Testing user management features...")
    
    # Test list users functionality
    command = "python3 ./add_user.py --list"
    success, output = run_command(command, "List users")
    
    if success and "testuser" in output:
        print("  List users: Success")
    else:
        print("  List users: Failed")
        return False
    
    # Test validation (should fail with invalid input)
    command = "python3 ./add_user.py invalid@user 192.168.1.10:8080 192.168.1.10:8088"
    success, output = run_command(command, "Test validation (should fail)")
    
    if not success:  # Should fail due to invalid username
        print("  Validation test: Success (correctly rejected invalid input)")
    else:
        print("  Validation test: Failed (should have rejected invalid input)")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)