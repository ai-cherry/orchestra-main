# 🍒 Patrick Instructions - Critical Human Workflows

> **Protected Repository for Essential Commands & Workflows**  
> Search for "Patrick Instructions" to find this quickly  
> **DO NOT DELETE** - Contains critical human-operated processes

---

## 🚀 Instant Mockup Access (Copy & Paste Ready)

```bash
# === CHERRY AI MOCKUP SYSTEM ===
# 1. Navigate to admin interface
cd orchestra-main/admin-interface

# 2. Start mockup server (one command does everything)
./mockup-automation.sh serve

# 3. Bookmark this URL:
# http://localhost:8001/mockups-index.html
```

**⭐ BOOKMARK URL:** `http://localhost:8001/mockups-index.html`

---

## 📋 Essential Commands Reference

### **Daily Workflow Commands**
```bash
# Start mockup server
./mockup-automation.sh serve

# Build new mockup from React changes  
./mockup-automation.sh build

# Development server (live reload)
./mockup-automation.sh dev

# Generate screenshots
./mockup-automation.sh screenshots

# Full workflow (build + serve)
./mockup-automation.sh all

# List all available mockups
./mockup-automation.sh list
```

### **Emergency Recovery**
```bash
# If server won't start (port conflict)
pkill -f "python3 -m http.server 8001"
./mockup-automation.sh serve

# If build fails (dependency issues)
rm -rf node_modules package-lock.json
npm install
./mockup-automation.sh build

# If nothing works (nuclear option)
cd orchestra-main/admin-interface
git status
git stash  # save any changes
git pull origin main
npm install
./mockup-automation.sh all
```

### **Health Check Commands**
```bash
# Test server accessibility
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mockups-index.html

# Check what's running on port 8001
lsof -i :8001

# Verify all mockups exist
ls -la *.html | wc -l  # Should show 9+ files
```

---

## 🎯 Critical Human-Remember Tasks

### **Weekly Tasks**
- [ ] Check mockup server is still running
- [ ] Verify all 9 mockups load correctly
- [ ] Update screenshots if major UI changes

### **Monthly Tasks**  
- [ ] Run dependency updates: `npm update`
- [ ] Clean old build artifacts: `./mockup-automation.sh cleanup`
- [ ] Backup this Patrick Instructions folder

### **Before Major Releases**
- [ ] Generate fresh screenshots: `./mockup-automation.sh screenshots`
- [ ] Test all mockup variants load correctly
- [ ] Commit any new mockups to git

---

## 🔧 Server & Infrastructure Info

### **Local Development URLs**
- **Mockup Gallery:** http://localhost:8001/mockups-index.html
- **File Browser:** http://localhost:8001/
- **Development Server:** http://localhost:3000 (when running `npm run dev`)

### **Production URLs** (GitHub Pages)
- **Latest Mockups:** https://[USERNAME].github.io/orchestra-main/latest/admin-interface/mockups-index.html
- **PR Previews:** https://[USERNAME].github.io/orchestra-main/previews/[COMMIT]/admin-interface/

### **MCP Server Status** (For Reference)
```bash
# Check running MCP servers
ps aux | grep mcp | grep -v grep

# Sophia Pay Ready Server Status
curl -s http://localhost:3001/health || echo "Sophia server offline"
```

---

## 🎨 Available Mockup Interfaces

| **Mockup File** | **Purpose** | **Size** | **Status** |
|---|---|---|---|
| `enhanced-production-interface.html` | Enterprise production ready | 104KB | ✅ Primary |
| `enhanced-admin-interface.html` | Master admin interface | 55KB | ✅ Enhanced |
| `ai-tools-dashboard.html` | AI tool management | 37KB | ✅ Specialized |
| `production-admin-interface.html` | Standard production | 36KB | ✅ Production |
| `chat.html` | Conversational interface | 35KB | ✅ Chat-focused |
| `enhanced-index.html` | Advanced landing page | 50KB | ✅ Landing |
| `cherry-ai-working.html` | Development version | 17KB | 🔄 Development |
| `working-interface.html` | Active development | 13KB | 🔄 In Progress |
| `mockups-index.html` | Gallery overview | 12KB | ✅ Meta |

---

## 💡 Notion API Integration Ideas

### **What to Auto-Save to Notion**
- [ ] Daily mockup generation reports
- [ ] UI change screenshots (before/after)
- [ ] Performance metrics and build times
- [ ] User feedback on interface designs
- [ ] Design decision rationale and history

### **Notion Database Structure**
```javascript
// Proposed Notion database schema
{
  "title": "Cherry AI Mockup Log",
  "properties": {
    "Date": { "type": "date" },
    "Mockup Type": { "type": "select" },
    "Screenshot": { "type": "files" },
    "Notes": { "type": "rich_text" },
    "Performance": { "type": "number" },
    "Status": { "type": "select" }
  }
}
```

### **Auto-Upload Script Concept**
```bash
# Future enhancement: Auto-upload to Notion
./mockup-automation.sh screenshots --upload-notion
# Would generate screenshots AND save to Notion with metadata
```

---

## 🛡️ Backup & Protection Strategy

### **Files Protected from Cleanup**
- `.patrick/` directory (this instruction set)
- `mockup-automation.sh` (automation script)
- `mockups-index.html` (gallery page)
- `.github/workflows/auto-mockups.yml` (GitHub Actions)

### **Git Protection Commands**
```bash
# Make this directory read-only to prevent accidental deletion
chmod -R 444 .patrick/
# To edit later: chmod -R 644 .patrick/

# Add to .gitignore exceptions to ensure it's always committed
echo "!.patrick/**" >> .gitignore
```

### **Recovery Information**
If this file is accidentally deleted, recover with:
```bash
git log --oneline | grep -i "patrick"
git checkout [COMMIT_HASH] -- .patrick/
```

---

## 📞 Emergency Contact Info

**When mockups break and you need help:**
1. Check the error in terminal where server is running
2. Try the "Emergency Recovery" commands above  
3. Search project for "Patrick Instructions" to find this file
4. Check GitHub Actions for automated mockup builds
5. Use `./mockup-automation.sh help` for quick reference

---

**Last Updated:** January 31, 2025 - 20:05 UTC  
**Location:** `orchestra-main/.patrick/README.md`  
**Purpose:** Preserve critical human workflows and prevent knowledge loss 