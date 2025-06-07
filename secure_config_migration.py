#!/usr/bin/env python3
"""
Secure Configuration Migration Tool
Safely transfer sensitive configuration data between environments
"""

import os
import sys
import json
import base64
import getpass
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
import argparse
import shutil
from typing import Dict, Optional

class SecureConfigMigration:
    def __init__(self):
        self.config_keys = [
            # Database
            "DATABASE_URL",
            "REDIS_URL", 
            "WEAVIATE_URL",
            
            # API Keys
            "OPENAI_API_KEY",
            "GITHUB_TOKEN",
            "SLACK_BOT_TOKEN",
            "HUBSPOT_API_KEY",
            "GONG_API_KEY",
            "LOOKER_API_KEY",
            "LINKEDIN_API_KEY",
            "NETSUITE_API_KEY",
            "APOLLO_API_KEY",
            "ASANA_API_KEY",
            "LINEAR_API_KEY",
            "SHAREPOINT_API_KEY",
            "LATTICE_API_KEY",
            
            # Security
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            
            # Optional
            "SENTRY_DSN",
            "ALERT_WEBHOOK_URL"
        ]
        
    def generate_encryption_key(self, password: str, salt: bytes) -> bytes:
        """Generate encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
        
    def export_config(self, source_env_file: str, output_file: str):
        """Export configuration to encrypted file"""
        print("🔐 SECURE CONFIGURATION EXPORT")
        print("="*50)
        
        # Check if source file exists
        if not os.path.exists(source_env_file):
            print(f"❌ Source file not found: {source_env_file}")
            return False
            
        # Read configuration
        config = {}
        with open(source_env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key in self.config_keys:
                        config[key] = value
                        
        if not config:
            print("❌ No configuration values found")
            return False
            
        print(f"📦 Found {len(config)} configuration values to export")
        
        # Get encryption password
        password = getpass.getpass("🔑 Enter encryption password: ")
        confirm = getpass.getpass("🔑 Confirm encryption password: ")
        
        if password != confirm:
            print("❌ Passwords don't match")
            return False
            
        # Generate salt and encrypt
        salt = secrets.token_bytes(16)
        key = self.generate_encryption_key(password, salt)
        fernet = Fernet(key)
        
        # Prepare export data
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "config_count": len(config),
            "checksum": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            "salt": base64.b64encode(salt).decode(),
            "encrypted_config": base64.b64encode(
                fernet.encrypt(json.dumps(config).encode())
            ).decode()
        }
        
        # Write encrypted file
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        print(f"✅ Configuration exported to: {output_file}")
        print(f"📊 Checksum: {export_data['checksum'][:16]}...")
        print("\n⚠️  IMPORTANT:")
        print("   - Share the password separately via secure channel")
        print("   - Delete the export file after import")
        print("   - This file expires in 24 hours")
        
        return True
        
    def import_config(self, import_file: str, target_env_file: str):
        """Import configuration from encrypted file"""
        print("🔐 SECURE CONFIGURATION IMPORT")
        print("="*50)
        
        # Check if import file exists
        if not os.path.exists(import_file):
            print(f"❌ Import file not found: {import_file}")
            return False
            
        # Read encrypted data
        with open(import_file, 'r') as f:
            export_data = json.load(f)
            
        # Check timestamp (24 hour expiry)
        export_time = datetime.fromisoformat(export_data['timestamp'])
        if (datetime.now() - export_time).total_seconds() > 86400:
            print("❌ Export file has expired (>24 hours old)")
            return False
            
        print(f"📦 Import file contains {export_data['config_count']} values")
        print(f"📅 Exported: {export_data['timestamp']}")
        
        # Get decryption password
        password = getpass.getpass("🔑 Enter decryption password: ")
        
        try:
            # Decrypt configuration
            salt = base64.b64decode(export_data['salt'])
            key = self.generate_encryption_key(password, salt)
            fernet = Fernet(key)
            
            decrypted_config = json.loads(
                fernet.decrypt(base64.b64decode(export_data['encrypted_config']))
            )
            
            # Verify checksum
            checksum = hashlib.sha256(
                json.dumps(decrypted_config, sort_keys=True).encode()
            ).hexdigest()
            
            if checksum != export_data['checksum']:
                print("❌ Checksum verification failed - data may be corrupted")
                return False
                
        except Exception as e:
            print(f"❌ Decryption failed: {str(e)}")
            return False
            
        # Backup existing config if it exists
        if os.path.exists(target_env_file):
            backup_file = f"{target_env_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(target_env_file, backup_file)
            print(f"📋 Backed up existing config to: {backup_file}")
            
        # Write new configuration
        with open(target_env_file, 'w') as f:
            f.write("# AI Orchestration Configuration\n")
            f.write(f"# Imported: {datetime.now().isoformat()}\n")
            f.write("# WARNING: Contains sensitive data - do not commit to version control\n\n")
            
            # Group by category
            categories = {
                "Database": ["DATABASE_URL", "REDIS_URL", "WEAVIATE_URL"],
                "AI Services": ["OPENAI_API_KEY"],
                "Integrations": ["GITHUB_TOKEN", "SLACK_BOT_TOKEN", "HUBSPOT_API_KEY", 
                               "GONG_API_KEY", "LOOKER_API_KEY", "LINKEDIN_API_KEY",
                               "NETSUITE_API_KEY", "APOLLO_API_KEY", "ASANA_API_KEY",
                               "LINEAR_API_KEY", "SHAREPOINT_API_KEY", "LATTICE_API_KEY"],
                "Security": ["SECRET_KEY", "JWT_SECRET_KEY"],
                "Monitoring": ["SENTRY_DSN", "ALERT_WEBHOOK_URL"]
            }
            
            for category, keys in categories.items():
                f.write(f"# {category}\n")
                for key in keys:
                    if key in decrypted_config:
                        f.write(f"{key}={decrypted_config[key]}\n")
                f.write("\n")
                
        print(f"✅ Configuration imported to: {target_env_file}")
        
        # Secure cleanup
        if input("\n🗑️  Delete import file? (recommended) [y/N]: ").lower() == 'y':
            os.remove(import_file)
            print("✅ Import file deleted")
            
        return True
        
    def manual_setup_guide(self):
        """Generate manual setup guide"""
        print("\n📋 MANUAL CONFIGURATION SETUP GUIDE")
        print("="*50)
        
        print("\n1️⃣  COPY TEMPLATE:")
        print("   cp .env.example .env")
        
        print("\n2️⃣  REQUIRED CONFIGURATIONS:")
        
        print("\n   🗄️  DATABASE CONNECTIONS:")
        print("   DATABASE_URL=postgresql://user:pass@host:5432/dbname")
        print("   REDIS_URL=redis://localhost:6379/0")
        print("   WEAVIATE_URL=http://localhost:8080")
        
        print("\n   🔑 API KEYS (obtain from respective services):")
        for key in ["OPENAI_API_KEY", "GITHUB_TOKEN", "SLACK_BOT_TOKEN"]:
            print(f"   {key}=your_{key.lower()}_here")
            
        print("\n   🔐 SECURITY KEYS (generate new ones):")
        print("   SECRET_KEY=" + secrets.token_urlsafe(32))
        print("   JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
        
        print("\n3️⃣  SECURITY BEST PRACTICES:")
        print("   ✓ Never commit .env files to version control")
        print("   ✓ Use different keys for each environment")
        print("   ✓ Rotate keys regularly")
        print("   ✓ Use strong, unique passwords")
        print("   ✓ Enable 2FA on all service accounts")
        
        print("\n4️⃣  VERIFICATION:")
        print("   python3 deployment_ready_check.py")

def main():
    parser = argparse.ArgumentParser(description="Secure Configuration Migration Tool")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export configuration')
    export_parser.add_argument('--source', default='.env', help='Source env file')
    export_parser.add_argument('--output', default='config_export.enc', help='Output file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import configuration')
    import_parser.add_argument('--input', default='config_export.enc', help='Input file')
    import_parser.add_argument('--target', default='.env', help='Target env file')
    
    # Manual guide
    subparsers.add_parser('guide', help='Show manual setup guide')
    
    args = parser.parse_args()
    
    migrator = SecureConfigMigration()
    
    if args.command == 'export':
        migrator.export_config(args.source, args.output)
    elif args.command == 'import':
        migrator.import_config(args.input, args.target)
    elif args.command == 'guide':
        migrator.manual_setup_guide()
    else:
        print("🔐 SECURE CONFIGURATION MIGRATION TOOL")
        print("="*50)
        print("\nOPTIONS:")
        print("\n1️⃣  ENCRYPTED EXPORT/IMPORT (Recommended)")
        print("   Export: python3 secure_config_migration.py export")
        print("   Import: python3 secure_config_migration.py import")
        print("\n2️⃣  MANUAL SETUP GUIDE")
        print("   Guide:  python3 secure_config_migration.py guide")
        print("\n3️⃣  SECURE CREDENTIAL SHARING")
        print("   - Use password managers (1Password, Bitwarden)")
        print("   - Use secure messaging (Signal, Keybase)")
        print("   - Use encrypted file transfer (age, gpg)")
        print("\nChoose based on your security requirements.")

if __name__ == "__main__":
    main()