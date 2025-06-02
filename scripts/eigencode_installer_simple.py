#!/usr/bin/env python3
"""
Simplified EigenCode Installer - Attempts to install EigenCode without dependencies
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path
from datetime import datetime

def log_message(message, level="INFO"):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_url(url):
    """Check if a URL is accessible"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code, response.headers.get('content-type', '')
    except:
        return None, None

def download_file(url, destination):
    """Download a file from URL"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(destination, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        log_message(f"Download failed: {e}", "ERROR")
    return False

def main():
    log_message("Starting EigenCode installation attempts...")
    
    # Installation directory
    install_dir = os.path.expanduser("~/.eigencode/bin")
    os.makedirs(install_dir, exist_ok=True)
    
    # Try different URLs
    base_urls = [
        "https://www.eigencode.dev",
        "https://api.eigencode.dev",
        "https://download.eigencode.dev",
        "https://github.com/eigencode/eigencode/releases"
    ]
    
    # Common download patterns
    patterns = [
        "/stable/latest/linux/eigencode.tar.gz",
        "/download/latest/eigencode-linux-amd64.tar.gz",
        "/releases/latest/download/eigencode-linux-amd64",
        "/v1/download/linux/eigencode"
    ]
    
    success = False
    
    # Try direct downloads
    log_message("Attempting direct downloads...")
    for base_url in base_urls:
        for pattern in patterns:
            url = base_url + pattern
            log_message(f"Trying: {url}")
            
            status, content_type = check_url(url)
            if status == 200:
                log_message(f"Found valid URL: {url} (status: {status})")
                
                # Download file
                temp_file = f"/tmp/eigencode_download_{datetime.now().timestamp()}"
                if download_file(url, temp_file):
                    log_message(f"Downloaded to: {temp_file}")
                    
                    # Determine file type and extract/install
                    file_info = subprocess.run(['file', temp_file], capture_output=True, text=True)
                    log_message(f"File type: {file_info.stdout}")
                    
                    if 'gzip' in file_info.stdout or 'tar' in file_info.stdout:
                        # Extract tar.gz
                        result = subprocess.run(['tar', '-xzf', temp_file, '-C', install_dir], capture_output=True)
                        if result.returncode == 0:
                            log_message("Extraction successful")
                            success = True
                            break
                    elif 'executable' in file_info.stdout or 'ELF' in file_info.stdout:
                        # Copy executable
                        eigencode_path = os.path.join(install_dir, 'eigencode')
                        subprocess.run(['cp', temp_file, eigencode_path])
                        subprocess.run(['chmod', '+x', eigencode_path])
                        log_message(f"Installed executable to: {eigencode_path}")
                        success = True
                        break
                    
                    # Clean up
                    os.remove(temp_file)
            elif status:
                log_message(f"URL returned status: {status}")
        
        if success:
            break
    
    # Check GitHub releases
    if not success:
        log_message("Checking GitHub releases...")
        try:
            # Try common GitHub organizations
            repos = ["eigencode/eigencode", "eigencode/cli", "eigencode-dev/eigencode"]
            
            for repo in repos:
                url = f"https://api.github.com/repos/{repo}/releases/latest"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    release_data = response.json()
                    log_message(f"Found GitHub release for {repo}")
                    
                    # Look for Linux binary
                    for asset in release_data.get('assets', []):
                        name = asset['name'].lower()
                        if 'linux' in name or 'amd64' in name or 'x86_64' in name:
                            download_url = asset['browser_download_url']
                            log_message(f"Found Linux asset: {name}")
                            
                            temp_file = f"/tmp/{asset['name']}"
                            if download_file(download_url, temp_file):
                                # Extract or install
                                if name.endswith('.tar.gz') or name.endswith('.tgz'):
                                    subprocess.run(['tar', '-xzf', temp_file, '-C', install_dir])
                                elif name.endswith('.zip'):
                                    subprocess.run(['unzip', '-o', temp_file, '-d', install_dir])
                                else:
                                    # Assume it's a binary
                                    eigencode_path = os.path.join(install_dir, 'eigencode')
                                    subprocess.run(['cp', temp_file, eigencode_path])
                                    subprocess.run(['chmod', '+x', eigencode_path])
                                
                                os.remove(temp_file)
                                success = True
                                break
                
                if success:
                    break
                    
        except Exception as e:
            log_message(f"GitHub check failed: {e}", "ERROR")
    
    # Check if installation was successful
    eigencode_path = os.path.join(install_dir, 'eigencode')
    if os.path.exists(eigencode_path):
        log_message(f"EigenCode found at: {eigencode_path}")
        
        # Try to run version command
        try:
            result = subprocess.run([eigencode_path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                log_message(f"EigenCode version: {result.stdout.strip()}")
                log_message("Installation successful!", "SUCCESS")
                
                # Add to PATH
                log_message("Add the following to your .bashrc or .zshrc:")
                log_message(f"export PATH={install_dir}:$PATH")
                
                return True
            else:
                log_message(f"Version command failed: {result.stderr}", "ERROR")
        except Exception as e:
            log_message(f"Failed to run eigencode: {e}", "ERROR")
    else:
        log_message("EigenCode installation failed", "ERROR")
        log_message("The EigenCode service appears to be unavailable (404 errors)")
        log_message("Please check https://www.eigencode.dev for updates")
    
    # Save installation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "install_dir": install_dir,
        "attempts": len(base_urls) * len(patterns),
        "eigencode_exists": os.path.exists(eigencode_path)
    }
    
    report_path = "eigencode_installation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_message(f"Installation report saved to: {report_path}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)