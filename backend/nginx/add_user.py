#!/usr/bin/env python3
"""
Nginx User Management Script

This script adds a new user with their VSCode and Jupyter server configurations
to the nginx configuration file. It provides structured error handling, validation,
and configuration management.

Usage: python3 add_user.py [username] [vscode_ip:port] [jupyter_ip:port]
Example: python3 add_user.py user3 192.168.1.10:8082 192.168.1.30:8090
"""

import argparse
import re
import sys
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NginxUserManager:
    """Manages nginx user configuration for VSCode and Jupyter services."""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "sites-available/dev-services"
        self.temp_file = None
        print(config_file, self.config_file)
        
    def validate_username(self, username: str) -> bool:
        if not username:
            return False
        
        # Only alphanumeric characters, hyphens, and underscores allowed
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))
    
    def validate_server_address(self, server_address: str) -> bool:
        if not server_address:
            return False
        
        # Pattern for ip:port format
        pattern = r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$'
        if not re.match(pattern, server_address):
            return False
        
        # Validate IP address components
        try:
            ip, port = server_address.split(':')
            ip_parts = ip.split('.')
            
            # Check IP address range (0-255 for each octet)
            for part in ip_parts:
                if not (0 <= int(part) <= 255):
                    return False
            
            # Check port range (1-65535)
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                return False
                
            return True
        except (ValueError, IndexError):
            return False
    
    def validate_inputs(self, username: str, vscode_server: str, jupyter_server: str) -> Tuple[bool, str]:
        if not self.validate_username(username):
            return False, "Invalid username. Only alphanumeric characters, hyphens, and underscores are allowed."
        
        if not self.validate_server_address(vscode_server):
            return False, "VSCode server must be in format ip:port (e.g., 192.168.1.10:8080)"
        
        if not self.validate_server_address(jupyter_server):
            return False, "Jupyter server must be in format ip:port (e.g., 192.168.1.10:8088)"
        
        return True, ""
    
    def check_user_exists(self, username: str) -> bool:
        print(self.config_file)
        if not os.path.exists(self.config_file):
            logger.error(f"Configuration file not found: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()
                
            # Check for upstream blocks
            vscode_upstream = f"upstream vscode_{username}"
            jupyter_upstream = f"upstream jupyter_{username}"
            
            return vscode_upstream in content or jupyter_upstream in content
            
        except IOError as e:
            logger.error(f"Error reading configuration file: {e}")
            return False
    
    def create_upstream_block(self, service_type: str, username: str, server_address: str) -> str:
        return f"""
# {username}
upstream {service_type}_{username} {{
    server {server_address} max_fails=3 fail_timeout=30s;
    # Use least_conn for better load distribution
    least_conn;
    
    # Enable health checks
    zone {service_type}_{username} 64k;
    keepalive 32;
}}"""
    
    def add_routing_rule(self, content: str, service_type: str, username: str) -> str:
        if service_type == "vscode":
            # Find the VSCode routing section and add new rule
            # Look for the comment "# Map users to their upstreams" in VSCode section
            pattern = r'(# Map users to their upstreams\s*\n\s*)'
            replacement = f'\\1        if ($user = "{username}") {{\n            proxy_pass http://vscode_{username}/$path$is_args$args;\n        }}\n        \n'
        else:  # jupyter
            # Find the Jupyter routing section and add new rule
            # Look for the comment "# Map users to their upstreams" in Jupyter section
            # We need to find the second occurrence (Jupyter section)
            lines = content.split('\n')
            vscode_section_found = False
            for i, line in enumerate(lines):
                if '# Map users to their upstreams' in line:
                    if vscode_section_found:
                        # This is the Jupyter section
                        lines.insert(i + 1, f'        if ($user = "{username}") {{')
                        lines.insert(i + 2, f'            proxy_pass http://jupyter_{username}/$path$is_args$args;')
                        lines.insert(i + 3, '        }')
                        lines.insert(i + 4, '        ')
                        return '\n'.join(lines)
                    else:
                        vscode_section_found = True
            return content
        
        return re.sub(pattern, replacement, content, count=1)
    
    def add_user_to_config(self, username: str, vscode_server: str, jupyter_server: str) -> bool:
        logger.info(f"Adding user {username} with VSCode server {vscode_server} and Jupyter server {jupyter_server}")
        
        try:
            # Create backup and temporary file
            backup_file = f"{self.config_file}.backup"
            shutil.copy2(self.config_file, backup_file)
            logger.info(f"Created backup: {backup_file}")
            
            # Read current configuration
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Add upstream blocks
            vscode_upstream = self.create_upstream_block("vscode", username, vscode_server)
            jupyter_upstream = self.create_upstream_block("jupyter", username, jupyter_server)
            
            # Append upstream blocks to the content
            content += vscode_upstream + "\n"
            content += jupyter_upstream + "\n"
            
            # Add routing rules
            content = self.add_routing_rule(content, "vscode", username)
            content = self.add_routing_rule(content, "jupyter", username)
            
            # Write updated configuration
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as temp_f:
                temp_f.write(content)
                self.temp_file = temp_f.name
            
            # Move temporary file to original location
            shutil.move(self.temp_file, self.config_file)
            
            logger.info(f"User {username} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to configuration: {e}")
            # Restore backup if something went wrong
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.config_file)
                logger.info("Configuration restored from backup")
            return False
    
    def test_nginx_config(self) -> bool:
        try:
            result = subprocess.run(
                ['sudo', '/usr/sbin/nginx', '-t'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Nginx configuration test passed")
                return True
            else:
                logger.error(f"Nginx configuration test failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Nginx configuration test timed out")
            return False
        except Exception as e:
            logger.error(f"Error testing nginx configuration: {e}")
            return False
    
    def reload_nginx(self) -> bool:
        logger.info("Reloading Nginx configuration...")
        
        # First test the configuration
        if not self.test_nginx_config():
            logger.error("Nginx configuration test failed. Not reloading.")
            return False
        
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'reload', 'nginx'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("Nginx reloaded successfully")
                return True
            else:
                logger.error(f"Error reloading Nginx: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Nginx reload timed out")
            return False
        except Exception as e:
            logger.error(f"Error reloading Nginx: {e}")
            return False
    
    def add_user(self, username: str, vscode_server: str, jupyter_server: str) -> bool:
        """Add a new user with complete validation and configuration."""
        # Validate inputs
        is_valid, error_msg = self.validate_inputs(username, vscode_server, jupyter_server)
        if not is_valid:
            logger.error(f"Validation error: {error_msg}")
            return False
            
        # Check if user already exists
        if self.check_user_exists(username):
            logger.error(f"User {username} already exists in the configuration")
            return False
        
        # Add user to configuration
        if not self.add_user_to_config(username, vscode_server, jupyter_server):
            return False
        
        # Reload nginx
        if not self.reload_nginx():
            logger.error("Failed to reload nginx. User configuration may not be active.")
            return False
        
        logger.info(f"User {username} can now access:")
        logger.info(f"  VSCode: http://your-server-ip/{username}/vscode/")
        logger.info(f"  Jupyter: http://your-server-ip/{username}/jupyter/")
        
        return True
    
    def remove_user(self, username: str) -> bool:
        logger.info(f"Removing user {username} from configuration")
        
        try:
            # Create backup
            backup_file = f"{self.config_file}.backup"
            shutil.copy2(self.config_file, backup_file)
            
            # Read current configuration
            with open(self.config_file, 'r') as f:
                lines = f.readlines()
            
            # Remove upstream blocks and routing rules
            new_lines = []
            skip_block = False
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Check for upstream block start
                if f"upstream vscode_{username}" in line or f"upstream jupyter_{username}" in line:
                    skip_block = True
                    # Skip comment line before upstream if it matches username
                    if i > 0 and lines[i-1].strip() == f"# {username}":
                        new_lines.pop()  # Remove the comment line
                elif skip_block and line.strip() == "}":
                    skip_block = False
                    i += 1
                    continue
                elif not skip_block:
                    # Check for routing rules
                    if f'if ($user = "{username}")' in line:
                        # Skip this if block (3 lines)
                        i += 3
                        continue
                    new_lines.append(line)
                
                i += 1
            
            # Write updated configuration
            with open(self.config_file, 'w') as f:
                f.writelines(new_lines)
            
            logger.info(f"User {username} removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error removing user: {e}")
            # Restore backup if something went wrong
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, self.config_file)
                logger.info("Configuration restored from backup")
            return False


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Add or remove users from nginx configuration for VSCode and Jupyter services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Add user:    python3 add_user.py user3 192.168.1.10:8082 192.168.1.30:8090
  Remove user: python3 add_user.py --remove user3
  List users:  python3 add_user.py --list
        """
    )
    
    parser.add_argument(
        'username',
        nargs='?',
        help='Username to add or remove'
    )
    
    parser.add_argument(
        'vscode_server',
        nargs='?',
        help='VSCode server address (ip:port)'
    )
    
    parser.add_argument(
        'jupyter_server',
        nargs='?',
        help='Jupyter server address (ip:port)'
    )
    
    parser.add_argument(
        '--remove',
        action='store_true',
        help='Remove user instead of adding'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing users'
    )
    
    parser.add_argument(
        '--config',
        help='Path to nginx configuration file',
        default="sites-available/dev-services"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def list_users(manager: NginxUserManager) -> None:
    try:
        with open(manager.config_file, 'r') as f:
            content = f.read()
        
        # Find all upstream blocks
        vscode_pattern = r'upstream vscode_(\w+)'
        jupyter_pattern = r'upstream jupyter_(\w+)'
        
        vscode_users = set(re.findall(vscode_pattern, content))
        jupyter_users = set(re.findall(jupyter_pattern, content))
        
        all_users = vscode_users.union(jupyter_users)
        
        if all_users:
            print("Existing users:")
            for user in sorted(all_users):
                has_vscode = user in vscode_users
                has_jupyter = user in jupyter_users
                services = []
                if has_vscode:
                    services.append("VSCode")
                if has_jupyter:
                    services.append("Jupyter")
                print(f"  {user}: {', '.join(services)}")
        else:
            print("No users found in configuration")
            
    except Exception as e:
        logger.error(f"Error listing users: {e}")


def main() -> int:
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create manager
    manager = NginxUserManager(args.config)
    
    # Handle list command
    if args.list:
        list_users(manager)
        return 0
    
    # Handle remove command
    if args.remove:
        if not args.username:
            logger.error("Username required for remove operation")
            return 1
        
        if manager.remove_user(args.username):
            if manager.reload_nginx():
                return 0
            else:
                logger.error("User removed but nginx reload failed")
                return 1
        else:
            return 1
    
    # Handle add command (default)
    if not all([args.username, args.vscode_server, args.jupyter_server]):
        logger.error("Username, VSCode server, and Jupyter server are required")
        parser.print_help()
        return 1
    
    if manager.add_user(args.username, args.vscode_server, args.jupyter_server):
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
