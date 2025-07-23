"""
SSH service for managing SSH connections and command execution.
"""
import paramiko
import threading
import uuid
import queue
import os
from typing import Dict, Any, Optional, List
from loguru import logger

from database import UserDatabase
from models.ssh import SSHConnectionInfo, SSHSessionStatus, SSHCommandRequest, SSHCommandResponse, SSHConnectRequest


class SSHSession:
    """SSH session management class."""
    
    def __init__(self, session_id: str, host: str, port: int, username: str, 
                 password: Optional[str] = None, key_path: Optional[str] = None):
        self.session_id = session_id
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
        self.shell = None
        self.output_queue = queue.Queue()
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish SSH connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path and os.path.exists(self.key_path):
                # Use SSH key authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=10
                )
            elif self.password:
                # Use password authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            else:
                raise Exception("No authentication method provided")
            
            # Create interactive shell
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(0.1)
            self.connected = True
            
            # Start output reader thread
            threading.Thread(target=self._read_output, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return False
    
    def _read_output(self):
        """Read output from SSH shell in background thread."""
        while self.connected and self.shell:
            try:
                if self.shell.recv_ready():
                    output = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    self.output_queue.put(output)
            except Exception as e:
                if self.connected:
                    logger.error(f"Error reading SSH output: {e}")
                break
    
    def execute_command(self, command: str) -> bool:
        """
        Execute command in SSH shell.
        
        Args:
            command: Command to execute
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.connected or not self.shell:
            return False
        try:
            self.shell.send(command + '\n')
            return True
        except Exception as e:
            logger.error(f"Error executing SSH command: {e}")
            return False
    
    def get_output(self) -> str:
        """
        Get accumulated output from SSH session.
        
        Returns:
            str: Output from SSH session
        """
        output_lines = []
        try:
            while not self.output_queue.empty():
                output_lines.append(self.output_queue.get_nowait())
        except queue.Empty:
            pass
        return ''.join(output_lines)
    
    def disconnect(self):
        """Disconnect SSH session."""
        self.connected = False
        if self.shell:
            self.shell.close()
        if self.client:
            self.client.close()


class SSHService:
    """Service for managing SSH connections and operations."""
    
    def __init__(self, db: UserDatabase):
        self.db = db
        self.ssh_sessions: Dict[str, SSHSession] = {}
        self.ssh_session_outputs: Dict[str, str] = {}
    
    def create_ssh_connection(self, server_id: str, ssh_config: Dict[str, Any], 
                            admin_username: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Establish SSH connection to server.
        
        Args:
            server_id: Server ID
            ssh_config: SSH configuration
            admin_username: Username of admin establishing connection
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Connection result
        """
        try:
            logger.info(f"SSH connection requested for server {ssh_config}")
            
            # Extract server IP from server_id
            server_ip = server_id.replace('server-', '').replace('-', '.')
            
            # Create SSH session
            session_id = str(uuid.uuid4())
            ssh_session = SSHSession(
                session_id=session_id,
                host=ssh_config.get('host', server_ip),
                port=int(ssh_config.get('port', 22)),
                username=ssh_config.get('username', 'root'),
                password=ssh_config.get('password'),
                key_path=ssh_config.get('key_path')
            )
            
            if ssh_session.connect():
                self.ssh_sessions[session_id] = ssh_session
                
                # Log SSH connection
                self.db.log_audit_event(
                    username=admin_username,
                    action_type='ssh_connect',
                    action_details={
                        'message': f'SSH connection established to server {server_ip}',
                        'server_id': server_id,
                        'server_ip': server_ip,
                        'ssh_user': ssh_config.get('username', 'root')
                    },
                    ip_address=ip_address
                )
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'message': f'SSH connection established to {server_ip}'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to establish SSH connection'
                }
                
        except Exception as e:
            logger.error(f"Error creating SSH connection: {e}")
            return {'success': False, 'error': 'Failed to create SSH connection'}
    
    def execute_ssh_command(self, session_id: str, command: str, admin_username: str, 
                          ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute command via SSH.
        
        Args:
            session_id: SSH session ID
            command: Command to execute
            admin_username: Username of admin executing command
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Execution result
        """
        try:
            if session_id not in self.ssh_sessions:
                return {'success': False, 'error': 'SSH session not found'}
            
            ssh_session = self.ssh_sessions[session_id]
            
            if ssh_session.execute_command(command):
                # Log command execution
                self.db.log_audit_event(
                    username=admin_username,
                    action_type='ssh_command',
                    action_details={
                        'message': f'SSH command executed: {command}',
                        'command': command,
                        'session_id': session_id,
                        'server_ip': ssh_session.host
                    },
                    ip_address=ip_address
                )
                
                return {
                    'success': True,
                    'message': 'Command executed'
                }
            else:
                return {'success': False, 'error': 'Failed to execute command'}
                
        except Exception as e:
            logger.error(f"Error executing SSH command: {e}")
            return {'success': False, 'error': 'Failed to execute command'}
    
    def get_ssh_output(self, session_id: str) -> Dict[str, Any]:
        """
        Get SSH session output.
        
        Args:
            session_id: SSH session ID
            
        Returns:
            Dict[str, Any]: Output result
        """
        try:
            if session_id not in self.ssh_sessions:
                return {'success': False, 'error': 'SSH session not found'}
            
            ssh_session = self.ssh_sessions[session_id]
            output = ssh_session.get_output()
            
            # Store output for session
            if session_id not in self.ssh_session_outputs:
                self.ssh_session_outputs[session_id] = ""
            
            self.ssh_session_outputs[session_id] += output
            
            return {
                'success': True,
                'output': output,
                'full_output': self.ssh_session_outputs[session_id]
            }
            
        except Exception as e:
            logger.error(f"Error getting SSH output: {e}")
            return {'success': False, 'error': 'Failed to get SSH output'}
    
    def disconnect_ssh_session(self, session_id: str, admin_username: str, 
                             ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Disconnect SSH session.
        
        Args:
            session_id: SSH session ID
            admin_username: Username of admin disconnecting session
            ip_address: Client IP address
            
        Returns:
            Dict[str, Any]: Disconnection result
        """
        try:
            if session_id not in self.ssh_sessions:
                return {'success': False, 'error': 'SSH session not found'}
            
            ssh_session = self.ssh_sessions[session_id]
            server_ip = ssh_session.host
            
            # Disconnect session
            ssh_session.disconnect()
            
            # Clean up
            del self.ssh_sessions[session_id]
            if session_id in self.ssh_session_outputs:
                del self.ssh_session_outputs[session_id]
            
            # Log SSH disconnection
            self.db.log_audit_event(
                username=admin_username,
                action_type='ssh_disconnect',
                action_details={
                    'message': f'SSH session disconnected from server {server_ip}',
                    'session_id': session_id,
                    'server_ip': server_ip
                },
                ip_address=ip_address
            )
            
            return {
                'success': True,
                'message': f'SSH session disconnected from {server_ip}'
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting SSH session: {e}")
            return {'success': False, 'error': 'Failed to disconnect SSH session'}
    
    def get_ssh_sessions(self) -> List[Dict[str, Any]]:
        """
        Get list of active SSH sessions.
        
        Returns:
            List[Dict[str, Any]]: List of active SSH sessions
        """
        try:
            sessions = []
            for session_id, ssh_session in self.ssh_sessions.items():
                sessions.append({
                    'session_id': session_id,
                    'host': ssh_session.host,
                    'port': ssh_session.port,
                    'username': ssh_session.username,
                    'connected': ssh_session.connected
                })
            return sessions
        except Exception as e:
            logger.error(f"Error getting SSH sessions: {e}")
            return []
