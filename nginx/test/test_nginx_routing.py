#!/usr/bin/env python3

import subprocess
import time
import requests
import sys
import os

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
    config_file = "/home/vishwa/gpu/dock-dash-command-center/nginx/sites-available/dev-services"
    
    try:
        # Read the current config
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Filter out testuser blocks
        filtered_lines = []
        skip_block = False
        brace_count = 0
        
        for line in lines:
            if '# testuser' in line:
                skip_block = True
                continue
            
            if skip_block:
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                    if brace_count <= 0:
                        skip_block = False
                        brace_count = 0
                continue
            
            filtered_lines.append(line)
        
        # Write back the filtered config
        command = f"sudo tee {config_file} > /dev/null"
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, text=True)
        process.communicate(''.join(filtered_lines))
        
        if process.returncode == 0:
            print("  Success: Removed existing testuser")
            return True
        else:
            print("  Failed: Could not write config file")
            return False
            
    except Exception as e:
        print(f"  Error removing testuser: {e}")
        return False

def add_test_user():
    """Add a test user using the add_user.sh script"""
    # First remove existing testuser if present
    remove_test_user()
    
    command = "sudo ./add_user.sh testuser 127.0.0.1:8080 127.0.0.1:8088"
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

def main():
    print("Starting NGINX user routing unit test...")
    
    # Start dummy services
    dummy_process = start_dummy_services()
    
    try:
        # Wait a moment for services to fully start
        time.sleep(2)
        
        # Add test user
        if not add_test_user():
            print("Failed to add test user. Exiting.")
            return False
        
        # Wait for NGINX to reload
        time.sleep(3)
        
        # Test service access
        success = test_service_access()
        
        if success:
            print("\nAll tests passed! NGINX user routing is working correctly.")
        else:
            print("\nSome tests failed. Check the output above for details.")
            
        return success
        
    finally:
        # Stop dummy services
        stop_dummy_services(dummy_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)