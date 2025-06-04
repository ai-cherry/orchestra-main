# Official Changeover Plan: Paperspace → Vultr

## When: NOW (Everything is ready)

## Step 1: Final Sync (5 minutes)
```bash
# Check for uncommitted changes on Paperspace
cd ~/cherry_ai-main
git status
git add -A && git commit -m "Final Paperspace changes" && git push
```

## Step 2: Verify Vultr is Ready (2 minutes)
```bash
# Test from your local machine
ssh -i ~/.ssh/vultr_cherry_ai root@45.32.69.157 "cd /root/cherry_ai-main && git pull && echo 'Vultr ready!'"
```

## Step 3: Update Cursor IDE (10 minutes)
Choose one:
- **Option A**: Set up Remote-SSH to Vultr (see CURSOR_VULTR_SETUP.md)
- **Option B**: Clone fresh on your local machine and push to deploy

## Step 4: Fix the Website Cache Issue (15 minutes)
```bash
# SSH to Vultr
ssh -i ~/.ssh/vultr_cherry_ai root@45.32.69.157

# Apply the new build configuration
cd /root/cherry_ai-main
git pull
cd admin-ui
npm run build

# Update nginx to prevent caching
sudo cp /root/cherry_ai-main/scripts/nginx_cherry_ai_admin_nocache.conf /etc/nginx/sites-available/cherry_ai
sudo nginx -t && sudo systemctl reload nginx

# Deploy the fresh build
sudo rm -rf /var/www/cherry_ai-admin/*
sudo cp -r dist/* /var/www/cherry_ai-admin/
```

## Step 5: Verify Everything Works
1. Open https://cherry-ai.me in an incognito/private window
2. Login with:
   - Email: any email
   - Password: `4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd`
3. Confirm you see real agent data

## Step 6: Clean Up Paperspace
```bash
# Optional: Download any personal files
# Then cancel Paperspace subscription to save money
```

## You're Done! 🎉

From now on:
- All development happens on Vultr (via SSH or Cursor Remote)
- No more server confusion
- Website updates immediately without cache issues
- One server, one bill, one source of truth
