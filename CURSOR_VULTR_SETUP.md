# Setting Up Cursor IDE with Vultr Server

## Method 1: Remote SSH Development (Recommended)

1. **Open Cursor IDE**
2. **Install Remote-SSH Extension** (if not already installed)
3. **Connect to Vultr**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Remote-SSH: Connect to Host"
   - Add new SSH Host: `root@45.32.69.157`
   - Select SSH config file to save
   - Connect using your SSH key

4. **Open the project**:
   - Once connected, open folder: `/root/orchestra-main`
   - Cursor will run on the server, giving you full speed

## Method 2: Local Development + Push

1. **Clone on your local machine**:
   ```bash
   git clone https://github.com/ai-cherry/orchestra-main.git
   cd orchestra-main
   ```

2. **Make changes locally in Cursor**

3. **Push and deploy**:
   ```bash
   git add -A && git commit -m "your changes"
   git push origin main

   # Then SSH to deploy
   ssh root@45.32.69.157 "cd /root/orchestra-main && git pull && systemctl restart orchestra-api"
   ```

## Transitioning from Paperspace

1. **Backup any local changes**:
   ```bash
   # On Paperspace
   cd ~/orchestra-main
   git stash
   git stash show -p > ~/paperspace-changes.patch
   ```

2. **Transfer to Vultr** (if needed):
   ```bash
   scp ~/paperspace-changes.patch root@45.32.69.157:~/
   ```

3. **Stop using Paperspace**:
   - Cancel Paperspace subscription
   - All development moves to Vultr

## Benefits of Vultr-only Development
- Single source of truth
- No sync issues
- Test in production environment
- Immediate deployment
- Lower costs (one server instead of two)
