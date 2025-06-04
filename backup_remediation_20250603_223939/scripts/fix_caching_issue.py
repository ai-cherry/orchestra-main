#!/usr/bin/env python3
"""Fix the caching issue by rebuilding with proper cache busting."""

import subprocess
import os
import time
import shutil

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result

def main():
    print("=== Fixing Caching Issue ===")
    
    # Step 1: Clean the build directory completely
    print("\n1. Cleaning build directory...")
    if os.path.exists("/root/cherry_ai-main/admin-ui/dist"):
        shutil.rmtree("/root/cherry_ai-main/admin-ui/dist")
    if os.path.exists("/root/cherry_ai-main/admin-ui/node_modules/.vite"):
        shutil.rmtree("/root/cherry_ai-main/admin-ui/node_modules/.vite")
    
    # Step 2: Update vite config to use timestamp-based hashing
    print("\n2. Updating vite config for better cache busting...")
    vite_config = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { TanStackRouterVite } from '@tanstack/router-plugin/vite';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    TanStackRouterVite({
      routesDirectory: './src/routes',
      generatedRouteTree: './src/routeTree.gen.ts',
    }),
    react(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Use timestamp in filename for cache busting
        entryFileNames: `assets/[name]-${Date.now()}.js`,
        chunkFileNames: `assets/[name]-${Date.now()}.js`,
        assetFileNames: `assets/[name]-${Date.now()}.[ext]`
      }
    }
  }
});
"""
    
    with open("/root/cherry_ai-main/admin-ui/vite.config.ts", "w") as f:
        f.write(vite_config)
    
    # Step 3: Rebuild the application
    print("\n3. Rebuilding application...")
    result = run_command("cd /root/cherry_ai-main/admin-ui && npm run build")
    if not result:
        print("Build failed!")
        return
    
    # Step 4: Clear web directory
    print("\n4. Clearing web directory...")
    run_command("sudo rm -rf /var/www/cherry_ai-admin/*")
    
    # Step 5: Copy new build
    print("\n5. Copying new build...")
    run_command("sudo cp -r /root/cherry_ai-main/admin-ui/dist/* /var/www/cherry_ai-admin/")
    run_command("sudo chown -R www-data:www-data /var/www/cherry_ai-admin/")
    
    # Step 6: Update Nginx to prevent caching of HTML
    print("\n6. Updating Nginx configuration...")
    nginx_config = """server {
    listen 80;
    server_name cherry-ai.me www.cherry-ai.me;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name cherry-ai.me www.cherry-ai.me;
    
    ssl_certificate /etc/letsencrypt/live/cherry-ai.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cherry-ai.me/privkey.pem;
    
    root /var/www/cherry_ai-admin;
    index index.html;
    
    # Prevent caching of HTML files
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
    
    # Prevent caching of index.html specifically
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
        add_header Last-Modified $date_gmt;
        if_modified_since off;
        etag off;
    }
    
    # Allow caching for assets with hash in filename
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Disable caching for API
        proxy_no_cache 1;
        proxy_cache_bypass 1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}"""
    
    with open('/tmp/cherry_ai-admin-fixed.conf', 'w') as f:
        f.write(nginx_config)
    
    run_command("sudo cp /tmp/cherry_ai-admin-fixed.conf /etc/nginx/sites-available/cherry_ai-admin")
    
    # Step 7: Test and reload Nginx
    print("\n7. Testing and reloading Nginx...")
    result = run_command("sudo nginx -t", check=False)
    if result.returncode == 0:
        run_command("sudo nginx -s reload")
        print("✓ Nginx reloaded successfully")
    else:
        print("✗ Nginx configuration test failed")
        return
    
    # Step 8: Clear any CDN/proxy caches
    print("\n8. Sending cache purge headers...")
    run_command("curl -X PURGE https://cherry-ai.me/", check=False)
    run_command("curl -X PURGE https://cherry-ai.me/assets/*", check=False)
    
    print("\n=== Fix Complete ===")
    print("The caching issue should now be resolved.")
    print("Users may need to:")
    print("1. Hard refresh (Ctrl+F5 or Cmd+Shift+R)")
    print("2. Clear browser cache")
    print("3. Open in incognito/private mode to verify")
    
    # Verify the new build
    print("\n9. Verifying new build...")
    result = run_command("ls -la /var/www/cherry_ai-admin/assets/")
    if result:
        print(result.stdout)

if __name__ == "__main__":
    main()