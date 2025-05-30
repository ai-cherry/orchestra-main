# Fix cherry-ai.me Domain Configuration

## Current Problem
- cherry-ai.me → 34.160.252.197 (WRONG)
- Should point to → 45.32.69.157 (Your Vultr server)

## Step 1: Update DNS Records

Go to your domain registrar/DNS provider and update:

### A Records:
```
cherry-ai.me        → 45.32.69.157
admin.cherry-ai.me  → 45.32.69.157
api.cherry-ai.me    → 45.32.69.157
www.cherry-ai.me    → 45.32.69.157
```

### OR use CNAME (if preferred):
```
admin.cherry-ai.me  → cherry-ai.me
api.cherry-ai.me    → cherry-ai.me
www.cherry-ai.me    → cherry-ai.me
```

## Step 2: Configure Nginx on Server (if needed)

Once DNS propagates, you may need to configure Nginx to handle the domains:

```bash
# SSH into your server
ssh -i ~/.ssh/vultr_orchestra root@45.32.69.157

# Edit Nginx config
nano /etc/nginx/sites-available/orchestra

# Add server blocks for your domains
```

## Step 3: Test After DNS Propagation

DNS changes can take 5 minutes to 48 hours. Test with:

```bash
# Check DNS
dig cherry-ai.me +short

# Should return: 45.32.69.157
```

## Current Working URLs (Use these now):

- **API**: http://45.32.69.157:8000
- **API Docs**: http://45.32.69.157:8000/docs
- **Swagger UI**: http://45.32.69.157:8000/redoc

## Need SSL/HTTPS?

Once DNS is fixed, you can set up Let's Encrypt:

```bash
# On the server
sudo certbot --nginx -d cherry-ai.me -d admin.cherry-ai.me -d api.cherry-ai.me
```
