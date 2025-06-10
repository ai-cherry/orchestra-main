# 🍒 Mockup Management Best Practices

## Quick Start - Zero Hassle Mockup Access

### **Instant Access (No Setup Required)**
```bash
cd orchestra-main/admin-interface
./mockup-automation.sh serve
```
Then open: **http://localhost:8001/mockups-index.html**

### **What You Get Immediately**
- ✅ **8 ready-to-view mockups** in a beautiful gallery
- ✅ **Organized by purpose**: Production, Enhanced, Development, Tools
- ✅ **File sizes and status** for each mockup
- ✅ **One-click access** to any interface version
- ✅ **Auto-refresh** every 30 seconds

---

## 🎯 Best Practices for Always Updated Mockups

### 1. **Automated Daily Builds**
Set up a cron job to automatically rebuild mockups:

```bash
# Add to your crontab (crontab -e)
0 2 * * * cd /path/to/orchestra-main/admin-interface && ./mockup-automation.sh all
```

### 2. **Development Workflow**
```bash
# When starting work
./mockup-automation.sh dev        # Live development server

# When testing changes  
./mockup-automation.sh build      # Create new mockup
./mockup-automation.sh serve      # View in gallery

# When ready to commit
./mockup-automation.sh screenshots  # Generate PNGs for documentation
```

### 3. **Watch Mode for Continuous Updates**
```bash
# Install entr for file watching
sudo apt install entr  # or brew install entr

# Auto-rebuild on file changes
./mockup-automation.sh watch
```

---

## 🚀 Advanced Automation Options

### **Option A: GitHub Actions (Recommended)**
Automatically builds mockups on every commit:

```yaml
# .github/workflows/mockups.yml
name: Auto-Generate Mockups
on: [push]
jobs:
  mockups:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install
      - run: npm run build
      - run: ./mockup-automation.sh screenshots
      - uses: actions/upload-artifact@v3
        with:
          name: mockups
          path: |
            *.html
            screenshots/
```

### **Option B: Docker Development Environment**
```dockerfile
# Dockerfile.mockups
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8001
CMD ["./mockup-automation.sh", "all"]
```

```bash
# Build and run
docker build -f Dockerfile.mockups -t cherry-mockups .
docker run -p 8001:8001 cherry-mockups
```

### **Option C: Vercel/Netlify Auto-Deploy**
```json
// vercel.json
{
  "builds": [
    { "src": "package.json", "use": "@vercel/static-build" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "/$1" }
  ]
}
```

---

## 📱 Mobile & Responsive Testing

### **Browser Stack Automation**
```javascript
// browser-testing.js
const browsers = [
  { device: 'iPhone 12 Pro', viewport: { width: 390, height: 844 } },
  { device: 'iPad Pro', viewport: { width: 1024, height: 1366 } },
  { device: 'Desktop', viewport: { width: 1920, height: 1080 } }
];

// Generate responsive screenshots
./mockup-automation.sh screenshots
```

### **Quick Mobile Preview**
```bash
# Start server accessible on local network
python3 -m http.server 8001 --bind 0.0.0.0

# Access from phone: http://YOUR_IP:8001/mockups-index.html
```

---

## 🔧 Troubleshooting-Free Setup

### **Common Issues & Solutions**

| Issue | Solution | Prevention |
|-------|----------|------------|
| Port 8001 in use | `./mockup-automation.sh serve` (auto-kills old) | Use automation script |
| Build fails | `rm -rf node_modules && npm install` | Regular dependency updates |
| Mockups outdated | `./mockup-automation.sh build` | Set up watch mode |
| No screenshots | `npm install puppeteer` | Include in package.json |

### **Health Check Script**
```bash
# Quick system check
./mockup-automation.sh list    # Show all mockups
curl -s http://localhost:8001/mockups-index.html > /dev/null && echo "✅ Server OK"
```

---

## 📊 Automated Quality Assurance

### **Lighthouse CI Integration**
```json
// .lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:8001/enhanced-production-interface.html'],
      numberOfRuns: 3
    },
    assert: {
      assertions: {
        'categories:performance': ['error', {minScore: 0.9}],
        'categories:accessibility': ['error', {minScore: 0.9}]
      }
    }
  }
}
```

### **Visual Regression Testing**
```bash
# Install Percy CLI
npm install --save-dev @percy/cli @percy/puppeteer

# Add to package.json scripts
"visual-test": "percy exec -- node screenshot-generator.js"
```

---

## 🎨 Design System Integration

### **Storybook Integration**
```bash
# Install Storybook
npx storybook init

# Configure for mockup generation
# .storybook/main.js
module.exports = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: ['@storybook/addon-docs']
}
```

### **Component Documentation**
```typescript
// src/components/Header/Header.stories.tsx
export default {
  title: 'Layout/Header',
  component: Header,
  parameters: {
    docs: {
      description: {
        component: 'Primary navigation header for admin interface'
      }
    }
  }
}
```

---

## 🔄 Continuous Integration Workflow

### **Complete CI/CD Pipeline**
```yaml
# .github/workflows/complete-mockups.yml
name: Complete Mockup Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-and-mockup:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: npm test
        
      - name: Build application
        run: npm run build
        
      - name: Generate mockups
        run: |
          chmod +x ./mockup-automation.sh
          ./mockup-automation.sh build
          ./mockup-automation.sh screenshots
          
      - name: Deploy to Preview
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
          destination_dir: previews/${{ github.sha }}
          
      - name: Comment PR with Preview
        uses: actions/github-script@v6
        if: github.event_name == 'pull_request'
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `🍒 **Mockup Preview Ready!**
              
              📱 [View Mockup Gallery](https://YOUR_USERNAME.github.io/orchestra-main/previews/${{ github.sha }}/admin-interface/mockups-index.html)
              
              🖼️ Screenshots generated and ready for review.`
            })
```

---

## 📈 Analytics & Monitoring

### **Mockup Usage Analytics**
```javascript
// Add to mockup-index.html
<script>
// Track which mockups are viewed most
function trackMockupView(mockupName) {
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({ mockup: mockupName, timestamp: Date.now() })
  });
}
</script>
```

### **Performance Monitoring**
```bash
# Monitor build times
time ./mockup-automation.sh build

# Monitor file sizes
du -sh *.html | sort -hr
```

---

## 🎯 Summary: Zero-Friction Mockup Workflow

### **Daily Developer Workflow**
1. **Morning**: `./mockup-automation.sh serve` (1 command, bookmark the URL)
2. **Development**: Use live dev server (`npm run dev`)
3. **Testing**: `./mockup-automation.sh build` (creates new mockup automatically)
4. **Review**: Refresh gallery page (auto-updates)
5. **Deploy**: Commit triggers automatic mockup generation

### **Key Benefits**
- ✅ **No troubleshooting** - automation handles everything
- ✅ **Always current** - builds on every change
- ✅ **One URL** - bookmark the gallery for instant access
- ✅ **Visual history** - keep all versions for comparison
- ✅ **Team sharing** - send one link to stakeholders
- ✅ **Mobile friendly** - responsive gallery works on all devices

### **The Golden Rule**
> **Never manually serve files or troubleshoot again.** 
> Use `./mockup-automation.sh serve` and bookmark `http://localhost:8001/mockups-index.html` 