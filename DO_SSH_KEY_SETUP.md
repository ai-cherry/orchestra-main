# DigitalOcean SSH Key Setup Guide

## Your SSH Public Key
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra
```

## Steps to Add SSH Key via DigitalOcean Control Panel:

### Method 1: Via Droplet Console (Recommended)
1. Log into [DigitalOcean Control Panel](https://cloud.digitalocean.com)
2. Click on your droplet name
3. Click "Access" → "Launch Droplet Console"
4. In the console, run:
   ```bash
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra" >> ~/.ssh/authorized_keys
   ```
5. Repeat for both droplets:
   - `superagi-dev-sfo2-01` (68.183.170.81)
   - `ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01` (159.65.79.26)

### Method 2: Via Recovery Console
1. Log into DigitalOcean Control Panel
2. Click on your droplet
3. Click "Access" → "Reset root password"
4. Check your email for the new password
5. Click "Access" → "Launch Recovery Console"
6. Login with the new password
7. Add the SSH key as shown above

### Method 3: Using DigitalOcean CLI (doctl)
```bash
# Install doctl if not already installed
# Then:
doctl compute ssh-key create paperspace-key --public-key "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra"

# Add to existing droplets
doctl compute droplet-action add-ssh-keys <droplet-id> --ssh-keys <key-id>
```

## After Adding the Key

Test the connection:
```bash
ssh -i ~/.ssh/id_ed25519 root@68.183.170.81 "echo 'Vector droplet connected'"
ssh -i ~/.ssh/id_ed25519 root@159.65.79.26 "echo 'App droplet connected'"
```

If successful, you can proceed with:
```bash
./setup_do_dev_environment.sh
```
