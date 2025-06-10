# 🛠️ Orchestra AI Maintenance Scripts

## 📋 **Available Scripts**

### **🚀 Deployment Scripts**
- `one_click_deploy.sh` - Complete system deployment with verification
- `daily_health_check.sh` - Comprehensive system health monitoring

### **📚 Documentation Scripts**
- `consolidate_documentation.sh` - Archive outdated docs and organize current ones

## 🎯 **Usage Examples**

```bash
# Full deployment
./scripts/one_click_deploy.sh

# Deployment without frontend
./scripts/one_click_deploy.sh --skip-frontend

# Verification only
./scripts/one_click_deploy.sh --verify-only

# Daily health check
./scripts/daily_health_check.sh

# Quiet health check (for cron)
CRON_MODE=1 ./scripts/daily_health_check.sh
```

## 📊 **Maintenance Schedule**

### **Daily**
- Run health check script
- Monitor system performance

### **Weekly**
- Review health check logs
- Update documentation if needed

### **Monthly**
- Archive old logs
- Update performance benchmarks

---

**All scripts are production-tested and safe for automated use.**
