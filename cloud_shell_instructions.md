# Using Diagnostic Tools in Google Cloud Shell

To use the diagnostic scripts in Google Cloud Shell, you need to copy them from GitHub Codespaces to your Cloud Shell environment. Here's how:

## Step 1: Create the Service Account Key File

First, make sure you have your service account key file in Cloud Shell:

```bash
# Create the credentials.json file with your service account key
nano credentials.json
# Paste your service account key JSON and save (Ctrl+O, Enter, Ctrl+X)
```

## Step 2: Create the Diagnostic Scripts

### GCP Authentication Diagnostics Script

```bash
# Create the script
nano gcp_auth_diagnostics.sh

# Make it executable
chmod +x gcp_auth_diagnostics.sh
```

Paste the content of the `gcp_auth_diagnostics.sh` script from GitHub Codespaces into the editor.

### Service Account Key Tester

```bash
# Install required dependency
pip install cryptography

# Create the script
nano test_gcp_key.py

# Make it executable
chmod +x test_gcp_key.py
```

Paste the content of the `test_gcp_key.py` script from GitHub Codespaces into the editor.

### Key Format Fixer

```bash
# Create the script
nano fix_key_format.py

# Make it executable
chmod +x fix_key_format.py
```

Paste the content of the `fix_key_format.py` script from GitHub Codespaces into the editor.

## Step 3: Run the Diagnostic Tools

### Run the Shell Script Diagnostics

```bash
./gcp_auth_diagnostics.sh
```

### Test the Service Account Key

```bash
python test_gcp_key.py --key-file credentials.json --verbose
```

### Fix Key Format Issues

```bash
python fix_key_format.py --input credentials.json --output fixed_credentials.json
```

## Common Issues and Solutions

1. **Escaped Newlines**: If the private key contains `\n` instead of actual newlines, the `fix_key_format.py` script can fix this.

2. **Key Revocation**: If the key has been revoked, you'll need to create a new key in the Google Cloud Console.

3. **Service Account Disabled**: Check if the service account is enabled in the Google Cloud Console.

4. **Permissions**: Ensure the service account has the necessary permissions for the operations you're trying to perform.

## Alternative: Direct Copy-Paste Method

If you prefer, you can copy the entire script content from GitHub Codespaces and create the files in Cloud Shell using a single command for each script:

```bash
cat > gcp_auth_diagnostics.sh << 'EOF'
# Paste the entire script content here
EOF
chmod +x gcp_auth_diagnostics.sh
```

Repeat this process for each script.
