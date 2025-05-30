# Vector Droplet SSH Configuration Issue

## Current Status
- ✅ **App Droplet (159.65.79.26)**: SSH key successfully added, accessible
- ❌ **Vector Droplet (68.183.170.81)**: Password authentication disabled, requires manual intervention

## Quick Solution

### Option 1: Use DigitalOcean Console (Recommended)
1. Log into [DigitalOcean Control Panel](https://cloud.digitalocean.com)
2. Find droplet: `superagi-dev-sfo2-01`
3. Click "Access" → "Launch Droplet Console"
4. In the browser console, run:
```bash
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra" >> ~/.ssh/authorized_keys
```

### Option 2: Enable Password Authentication Temporarily
From the DigitalOcean console:
```bash
# Edit SSH config
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Then from Paperspace, run:
sshpass -p 'xTD.8HBd?-+Bib' ssh root@68.183.170.81 "echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICq38OXXQVPAqVHzP99JvpDJBw+Myl8kItDGXOrurNYB paperspace@ai-cherry-orchestra' >> ~/.ssh/authorized_keys"

# Disable password auth again
ssh root@68.183.170.81 "sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && systemctl restart sshd"
```

## Workaround: Deploy Through App Droplet

Since the App droplet is accessible, we can:
1. Deploy all services to the App droplet first
2. Use the App droplet as a jump host to configure the Vector droplet
3. Or temporarily run Weaviate on the App droplet

## Test After Adding Key
```bash
ssh -i ~/.ssh/id_ed25519 root@68.183.170.81 "echo 'Vector droplet connected'"
```
