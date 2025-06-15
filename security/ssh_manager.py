"""
Orchestra AI - Secure SSH Connection Manager
Replaces insecure SSH practices with proper key validation and security
"""

import os
import subprocess
import tempfile
import stat
import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import paramiko
from security.secret_manager import secret_manager

logger = logging.getLogger(__name__)

class SecureSSHManager:
    """Secure SSH connection manager with proper key validation"""
    
    def __init__(self):
        self.connection_timeout = 30
        self.command_timeout = 300
        self.max_retries = 3
        self.retry_delay = 5
        
    def validate_ssh_key(self, key_content: str) -> bool:
        """Validate SSH private key format and security"""
        try:
            # Try to load the key to validate format
            if key_content.startswith('-----BEGIN OPENSSH PRIVATE KEY-----'):
                # OpenSSH format
                from cryptography.hazmat.primitives import serialization
                serialization.load_ssh_private_key(
                    key_content.encode(),
                    password=None
                )
                return True
            elif key_content.startswith('-----BEGIN RSA PRIVATE KEY-----'):
                # PEM format
                from cryptography.hazmat.primitives import serialization
                serialization.load_pem_private_key(
                    key_content.encode(),
                    password=None
                )
                return True
            else:
                logger.error("Unsupported SSH key format")
                return False
        except Exception as e:
            logger.error(f"SSH key validation failed: {e}")
            return False
    
    def create_secure_key_file(self, key_content: str) -> Optional[str]:
        """Create temporary SSH key file with secure permissions"""
        if not self.validate_ssh_key(key_content):
            return None
            
        try:
            # Create temporary file
            fd, key_file = tempfile.mkstemp(prefix='orchestra_ssh_', suffix='.key')
            
            # Write key content
            with os.fdopen(fd, 'w') as f:
                f.write(key_content)
            
            # Set secure permissions (600 - owner read/write only)
            os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
            
            return key_file
        except Exception as e:
            logger.error(f"Failed to create secure key file: {e}")
            return None
    
    def verify_host_key(self, hostname: str, port: int = 22) -> bool:
        """Verify SSH host key against known hosts"""
        try:
            # Use paramiko to check host key
            client = paramiko.SSHClient()
            
            # Load system host keys
            client.load_system_host_keys()
            
            # Load user host keys
            try:
                client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except FileNotFoundError:
                logger.warning("No known_hosts file found")
            
            # Set policy for unknown hosts
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            
            # Try to connect (this will verify the host key)
            client.connect(
                hostname=hostname,
                port=port,
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            
            client.close()
            return True
            
        except paramiko.AuthenticationException:
            # Authentication failed but host key is valid
            return True
        except paramiko.SSHException as e:
            if "not found in known_hosts" in str(e):
                logger.warning(f"Host {hostname} not in known_hosts")
                return False
            logger.error(f"SSH host key verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Host key verification error: {e}")
            return False
    
    def add_host_to_known_hosts(self, hostname: str, port: int = 22) -> bool:
        """Add host to known_hosts after manual verification"""
        try:
            # Get host key using ssh-keyscan
            result = subprocess.run(
                ['ssh-keyscan', '-p', str(port), hostname],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                # Append to known_hosts
                known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
                os.makedirs(os.path.dirname(known_hosts_path), exist_ok=True)
                
                with open(known_hosts_path, 'a') as f:
                    f.write(result.stdout)
                
                logger.info(f"Added {hostname} to known_hosts")
                return True
            else:
                logger.error(f"Failed to get host key for {hostname}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add host to known_hosts: {e}")
            return False
    
    def execute_ssh_command(
        self, 
        hostname: str, 
        command: str, 
        username: str = 'ubuntu',
        key_content: Optional[str] = None,
        port: int = 22,
        verify_host: bool = True
    ) -> Dict[str, Any]:
        """Execute SSH command with proper security"""
        
        # Verify host key if required
        if verify_host and not self.verify_host_key(hostname, port):
            return {
                'success': False,
                'error': f'Host key verification failed for {hostname}',
                'stdout': '',
                'stderr': ''
            }
        
        # Get SSH key
        if not key_content:
            key_content = secret_manager.get_secret('SSH_PRIVATE_KEY')
            if not key_content:
                return {
                    'success': False,
                    'error': 'No SSH private key available',
                    'stdout': '',
                    'stderr': ''
                }
        
        # Create secure key file
        key_file = self.create_secure_key_file(key_content)
        if not key_file:
            return {
                'success': False,
                'error': 'Failed to create secure SSH key file',
                'stdout': '',
                'stderr': ''
            }
        
        try:
            # Build secure SSH command
            ssh_options = [
                '-i', key_file,
                '-o', 'ConnectTimeout=30',
                '-o', 'ServerAliveInterval=60',
                '-o', 'ServerAliveCountMax=3',
                '-o', 'BatchMode=yes',  # No interactive prompts
                '-o', 'PasswordAuthentication=no',  # Key-only auth
                '-o', 'PubkeyAuthentication=yes',
                '-o', 'StrictHostKeyChecking=yes',  # SECURE: Always verify host keys
                '-o', 'UserKnownHostsFile=~/.ssh/known_hosts',
                '-p', str(port)
            ]
            
            ssh_command = ['ssh'] + ssh_options + [f'{username}@{hostname}', command]
            
            # Execute with retries
            for attempt in range(self.max_retries):
                try:
                    result = subprocess.run(
                        ssh_command,
                        capture_output=True,
                        text=True,
                        timeout=self.command_timeout
                    )
                    
                    return {
                        'success': result.returncode == 0,
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'command': ' '.join(ssh_command)
                    }
                    
                except subprocess.TimeoutExpired:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"SSH command timeout, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return {
                            'success': False,
                            'error': 'SSH command timeout after retries',
                            'stdout': '',
                            'stderr': ''
                        }
                        
        except Exception as e:
            logger.error(f"SSH command execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            }
        finally:
            # Clean up temporary key file
            try:
                os.unlink(key_file)
            except:
                pass
    
    def execute_ssh_script(
        self,
        hostname: str,
        script_content: str,
        username: str = 'ubuntu',
        key_content: Optional[str] = None,
        port: int = 22
    ) -> Dict[str, Any]:
        """Execute multi-line script over SSH"""
        
        # Create temporary script file
        try:
            fd, script_file = tempfile.mkstemp(prefix='orchestra_script_', suffix='.sh')
            with os.fdopen(fd, 'w') as f:
                f.write('#!/bin/bash\nset -e\n')  # Exit on error
                f.write(script_content)
            
            os.chmod(script_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            
            # Upload and execute script
            upload_command = f"cat > /tmp/orchestra_script.sh && chmod +x /tmp/orchestra_script.sh"
            
            # First upload the script
            with open(script_file, 'r') as f:
                script_data = f.read()
            
            upload_result = self.execute_ssh_command(
                hostname, 
                f"cat > /tmp/orchestra_script.sh << 'EOF'\n{script_data}\nEOF",
                username, 
                key_content, 
                port
            )
            
            if not upload_result['success']:
                return upload_result
            
            # Then execute the script
            return self.execute_ssh_command(
                hostname,
                "chmod +x /tmp/orchestra_script.sh && /tmp/orchestra_script.sh && rm -f /tmp/orchestra_script.sh",
                username,
                key_content,
                port
            )
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': ''
            }
        finally:
            try:
                os.unlink(script_file)
            except:
                pass
    
    def test_connection(self, hostname: str, username: str = 'ubuntu', port: int = 22) -> bool:
        """Test SSH connection without executing commands"""
        result = self.execute_ssh_command(hostname, 'echo "Connection test successful"', username, port=port)
        return result['success']

# Global instance
secure_ssh = SecureSSHManager()

