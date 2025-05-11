#!/usr/bin/env python3
"""
test_gcp_key.py - Test a GCP service account key by making direct API calls

This script tests a GCP service account key by:
1. Parsing the key file
2. Creating a JWT token
3. Exchanging the JWT for an access token
4. Making a test API call

This can help identify if the issue is with the key itself or with how it's being used.
"""

import json
import time
import base64
import datetime
import sys
import argparse
import http.client
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def parse_key_file(key_file: str) -> Dict[str, Any]:
    """Parse a GCP service account key file."""
    try:
        with open(key_file, 'r') as f:
            key_data = json.load(f)
        
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri',
            'auth_provider_x509_cert_url', 'client_x509_cert_url'
        ]
        
        for field in required_fields:
            if field not in key_data:
                print(f"Error: Key file is missing required field: {field}")
                sys.exit(1)
        
        return key_data
    except json.JSONDecodeError:
        print(f"Error: Key file is not valid JSON: {key_file}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Key file not found: {key_file}")
        sys.exit(1)

def create_jwt(key_data: Dict[str, Any], scope: str) -> str:
    """Create a JWT token from a service account key."""
    try:
        # Parse the private key
        private_key_str = key_data['private_key']
        private_key = load_pem_private_key(
            private_key_str.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        
        # Create JWT header
        header = {
            'alg': 'RS256',
            'typ': 'JWT',
            'kid': key_data['private_key_id']
        }
        
        # Create JWT payload
        now = int(time.time())
        payload = {
            'iss': key_data['client_email'],
            'aud': key_data['token_uri'],
            'scope': scope,
            'iat': now,
            'exp': now + 3600  # 1 hour expiration
        }
        
        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).rstrip(b'=').decode('utf-8')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode('utf-8')).rstrip(b'=').decode('utf-8')
        
        # Create signature
        to_sign = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = private_key.sign(
            to_sign,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')
        
        # Create JWT
        jwt = f"{header_b64}.{payload_b64}.{signature_b64}"
        return jwt
    except Exception as e:
        print(f"Error creating JWT: {e}")
        sys.exit(1)

def exchange_jwt_for_token(key_data: Dict[str, Any], jwt: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Exchange a JWT for an access token."""
    try:
        # Parse the token URI
        token_uri = key_data['token_uri']
        parsed_uri = urllib.parse.urlparse(token_uri)
        
        # Create the request
        params = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': jwt
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Make the request
        conn = http.client.HTTPSConnection(parsed_uri.netloc)
        conn.request(
            'POST',
            parsed_uri.path,
            urllib.parse.urlencode(params),
            headers
        )
        
        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        conn.close()
        
        # Parse the response
        if response.status == 200:
            response_json = json.loads(response_data)
            access_token = response_json.get('access_token')
            return True, access_token, None
        else:
            return False, None, response_data
    except Exception as e:
        return False, None, str(e)

def test_api_call(key_data: Dict[str, Any], access_token: str) -> Tuple[bool, Optional[str]]:
    """Make a test API call to verify the access token."""
    try:
        # Create the request
        project_id = key_data['project_id']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Make the request to list service accounts (a simple API call)
        conn = http.client.HTTPSConnection('iam.googleapis.com')
        conn.request(
            'GET',
            f'/v1/projects/{project_id}/serviceAccounts',
            None,
            headers
        )
        
        # Get the response
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        conn.close()
        
        # Parse the response
        if response.status == 200:
            return True, response_data
        else:
            return False, response_data
    except Exception as e:
        return False, str(e)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test a GCP service account key')
    parser.add_argument('--key-file', default='credentials.json', help='Path to the service account key file')
    parser.add_argument('--scope', default='https://www.googleapis.com/auth/cloud-platform', help='OAuth scope to request')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    print(f"Testing service account key: {args.key_file}")
    print(f"Using scope: {args.scope}")
    print()
    
    # Step 1: Parse the key file
    print("Step 1: Parsing key file...")
    key_data = parse_key_file(args.key_file)
    print(f"  Service account: {key_data['client_email']}")
    print(f"  Project ID: {key_data['project_id']}")
    print(f"  Private key ID: {key_data['private_key_id']}")
    print("  Key file parsed successfully")
    print()
    
    # Step 2: Create a JWT token
    print("Step 2: Creating JWT token...")
    jwt = create_jwt(key_data, args.scope)
    if args.verbose:
        print(f"  JWT: {jwt}")
    else:
        print(f"  JWT: {jwt[:20]}...{jwt[-20:]}")
    print("  JWT created successfully")
    print()
    
    # Step 3: Exchange the JWT for an access token
    print("Step 3: Exchanging JWT for access token...")
    success, access_token, error = exchange_jwt_for_token(key_data, jwt)
    if success:
        if args.verbose:
            print(f"  Access token: {access_token}")
        else:
            print(f"  Access token: {access_token[:20]}...{access_token[-20:]}")
        print("  Token exchange successful")
    else:
        print(f"  Token exchange failed: {error}")
        print("  This indicates an issue with the service account key or JWT")
        print("  Common issues include:")
        print("    - Invalid private key format")
        print("    - Service account is disabled")
        print("    - Service account key has been revoked")
        print("    - Clock skew between your system and Google's servers")
        sys.exit(1)
    print()
    
    # Step 4: Make a test API call
    print("Step 4: Making test API call...")
    success, response = test_api_call(key_data, access_token)
    if success:
        print("  API call successful")
        if args.verbose:
            print(f"  Response: {response}")
        else:
            print(f"  Response: {response[:100]}...")
    else:
        print(f"  API call failed: {response}")
        print("  This indicates an issue with the access token or permissions")
        print("  Common issues include:")
        print("    - Service account doesn't have required permissions")
        print("    - Project has been disabled")
        sys.exit(1)
    print()
    
    print("All tests passed! The service account key is valid and working.")

if __name__ == "__main__":
    main()