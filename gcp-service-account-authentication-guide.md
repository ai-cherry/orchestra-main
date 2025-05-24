# Google Cloud Authentication with Service Account Key

This guide provides step-by-step instructions for authenticating the gcloud command-line tool and Google Cloud SDKs using a service account JSON key for user `scoobyjava@cherry-ai.me`.

## Method 1: Using gcloud auth activate-service-account

### Step 1: Save the JSON key to a file

1. Create a new file named `service-account-key.json`:

   ```bash
   nano service-account-key.json
   ```

   Or use any text editor of your choice.

2. Copy and paste the entire JSON content below into this file:

   ```json
   {
     "type": "service_account",
     "project_id": "cherry-ai-project",
     "private_key_id": "216e545f19f380c72ad7eb704a15041621503f03",
     "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDi3y+r4sY+2Jyj\ngdG/N5OrTNMKdhY2nndtxk4V4NVkRdSXKSGE3WEz6bLBaT0iVBXjDhuGyT1IzjiS\nCmkWjQ6CaGCwThjvHjkioHTIsgNO6/7FjCh0YRXJIz+gkY9O2P2UMKDMetlDz6la\nVdaFWHCro/ipoC9dZtiWxX7JoDw6+ZqoYct20qtrRDlh2trF+RT9QzxLJmeWoZxB\nvHU1oU1PsbGPDHyts/iXHqISyjEsUUtvOG/IsvMIWPVWvRCbnweQkktsATqzD7bH\nXZOj4cSqO2imAEPFkK/TZ+56JdjtHoZEaVyxzmXB4Pr9sde6KfuesdXjykufztMR\nwULU1B0fAgMBAAECggEASUsqVwD94+rN/ALiNMDrO5Gnsn8A4Sdj1PqWWnoW5nyq\n2CTpF8f/caqD3fk2T2NT6NUzbmGQI3fADepAFhF/CQFYj0zDwGiGs9mbsQTVjccv\nOTn1DdgZljAFi8XKwwHWNmxZXoYnr8EkaLNHiS/PwpvIJ2DBPI8P1PG76r6SBsjl\n7++ShV9r+m577erGvXUxk80dgYoHfBemwYBLSSm5LW0frSmEKHI7vBIT231YslTy\nYFODMOQQ0t+1MtX+7uNVyYOx+GdERkp9XfB3sgYVxZwdZ2pXha0pOZ2UieAm0Za6\nTNoUvhSYECXBfkMyXz89OaWI+4ycizvW9JziZeLk+QKBgQD5Znm9iYmdmvUYmI6T\nK7nBHDk3IXsJ+rwLOEDLHp0c1dhdgimgzFN81mKibDQ4jefRvTlDqSWbZ7Hn4YMF\nCTyZXgJKlU7A0qlufGWd3gfLGkwlDlzyi209mw7yE4W70sQpasea2e3cVWWYtxy9\nwSYQmxObgVZU5L7feVt1xmOIaQKBgQDo4BhN/6PzdnpyQfow4WLxFRCnjRnAZ4Ka\nLqHt8KB4L9K/3qjLFhJLNAUPcOL0C9K581CFfXqqN4gauKzGYa8id2RB9d8Q7LSE\nLNblKOMA3OoSGlWXDaWXLGLA9IsHyIgUqK6oRkoaW4a8XFN5ntgbJoEDpydfCXTs\nKOnAbIYIRwKBgQCB7U7y3RoiTz3siF2OcjMdVXTBMeIFeuhH+BBZQSOciBNl8494\nQ7oiyRUthK1X4SWp8KhKhW4gHc9i++rjzsIRLBaJgGs8rQKzmn7d1XO97X9JtsfZ\nW6WXeJY6qsz64nxrD0PZejselCaPfqWsfVk1QXTfiGvPYjPF/FUXcDkeMQKBgEOY\nYJWrYZyWxF4L9qJfmceetLHdzB7ELO2yIYCeewXH4+WbrOUeJ/s6Q0nDG615DRa6\noKHO1V85NUGEX2pKCnr3qttWkgQooRFIrqvf3Vxvw2WzzSpGZM1nrdaSZRTCSXWt\nrNzdYj8aWBauufAwgkwHNiWoTE5SwWSXT5pyJcmbAoGBALODSSlDnCtXqMry+lKx\nywyhRlYIk2QsmUjrJdYd74o6C8Q7D6o/p1Ah3uNl5fKvN+0QeNvpJB9yqiauS+w2\nlEMmVdcqYKwdmjkPxGiLKHhJcXiB62Nd5jUtVvGv9lz1c74bJdmhYjUOGuUtR5Ll\nxFFGN62B4+ed1wDppnemICJV\n-----END PRIVATE KEY-----\n",
     "client_email": "orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com",
     "client_id": "103717197419391442785",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/orchestra-project-admin-sa%40cherry-ai-project.iam.gserviceaccount.com",
     "universe_domain": "googleapis.com"
   }
   ```

3. Save the file and exit the editor.

4. Secure the file with appropriate permissions:
   ```bash
   chmod 600 service-account-key.json
   ```

### Step 2: Authenticate using the service account key

Run the following command to authenticate:

```bash
gcloud auth activate-service-account orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com --key-file=service-account-key.json
```

### Step 3: Verify authentication

To verify that the authentication was successful, you can run:

```bash
gcloud auth list
```

This will show the active account. You should see `orchestra-project-admin-sa@cherry-ai-project.iam.gserviceaccount.com` listed as the active account.

You can also verify by listing projects you have access to:

```bash
gcloud projects list
```

### Step 4: Set the project context

Set the current project to match the service account's project:

```bash
gcloud config set project cherry-ai-project
```

Verify the project is set correctly:

```bash
gcloud config get-value project
```

This should output `cherry-ai-project`.

## Method 2: Using the GOOGLE_APPLICATION_CREDENTIALS environment variable

### Step 1: Save the JSON key to a file

Follow the same steps as in Method 1 to create and secure the `service-account-key.json` file.

### Step 2: Set the GOOGLE_APPLICATION_CREDENTIALS environment variable

#### For Linux/macOS:

For temporary use in the current terminal session:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/service-account-key.json"
```

For persistent use, add to your shell profile file (e.g., ~/.bashrc, ~/.zshrc):

```bash
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/service-account-key.json"' >> ~/.bashrc
source ~/.bashrc
```

#### For Windows (Command Prompt):

```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json
```

#### For Windows (PowerShell):

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account-key.json"
```

For persistent use in Windows, set it as a system environment variable through the System Properties dialog.

### Step 3: Understanding this method

This method is primarily used by Google Cloud client libraries and SDKs. When you set this environment variable, any Google Cloud client library that supports Application Default Credentials (ADC) will automatically use this service account for authentication.

This is particularly useful for:

- Running applications locally that use Google Cloud services
- Testing code that will eventually run in a Google Cloud environment
- Using Google Cloud SDKs and libraries in scripts and applications

### Step 4: Verify the authentication

You can verify that the credentials are working by running a simple command that uses the gcloud CLI with ADC:

```bash
gcloud auth application-default print-access-token
```

This should print an access token if the credentials are valid.

For a more comprehensive test, you can run a simple Python script that uses a Google Cloud client library:

```python
from google.cloud import storage

# Create a client
storage_client = storage.Client()

# List buckets
buckets = list(storage_client.list_buckets())
print(f"Buckets in project {storage_client.project}:")
for bucket in buckets:
    print(bucket.name)
```

Save this as `test_gcp_auth.py` and run it with:

```bash
python test_gcp_auth.py
```

If it runs without authentication errors and lists the buckets in your project, the authentication is working correctly.

Note: For the Python example, you'll need to install the Google Cloud Storage library first:

```bash
pip install google-cloud-storage
```

## Security Considerations

1. Keep your service account key secure and never commit it to version control systems.
2. The key provides access to your Google Cloud resources according to the permissions granted to the service account.
3. Consider using more secure authentication methods like Workload Identity Federation for production environments.
4. Regularly rotate service account keys as part of your security practices.
5. Set appropriate file permissions (chmod 600) to ensure only the intended user can read the key file.
