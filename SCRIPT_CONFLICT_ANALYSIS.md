# Orchestra AI - Script Conflict Analysis

## 🔍 **Critical Conflicts Identified**

### **1. SSH Key Path Conflicts**
- **`deploy_orchestra_complete.sh`**: Uses `~/.ssh/id_rsa` (default)
- **`deploy_complete_system.sh`**: Uses `~/.ssh/orchestra_lambda` (specific)
- **`simple_deploy.sh`**: No SSH key specified (assumes default)

**CONFLICT**: Different SSH key paths will cause authentication failures

### **2. Directory Structure Conflicts**
- **`deploy_orchestra_complete.sh`**: Expects `/home/ubuntu/orchestra-dev`
- **`deploy_complete_system.sh`**: Expects `/home/ubuntu/orchestra-dev`
- **`simple_deploy.sh`**: Uses `/home/ubuntu/orchestra-main`

**CONFLICT**: Different target directories will cause deployment failures

### **3. Service Management Conflicts**
- **`deploy_orchestra_complete.sh`**: Uses supervisor + systemd
- **`deploy_complete_system.sh`**: Uses enhanced supervisor + systemd
- **`simple_deploy.sh`**: Uses simple nohup processes

**CONFLICT**: Multiple service management approaches will compete

### **4. Port Assignment Conflicts**
All scripts use similar port assignments but with different service structures:
- **API Server**: Port 8000 (consistent)
- **MCP Memory**: Port 8003 (consistent)
- **MCP Portkey**: Port 8004 (consistent)
- **AI Context**: Port 8005 (consistent)

**NO CONFLICT**: Port assignments are consistent

### **5. Nginx Configuration Conflicts**
- **`deploy_orchestra_complete.sh`**: Basic nginx proxy config
- **`deploy_complete_system.sh`**: Enhanced nginx with admin interface
- **`simple_deploy.sh`**: No nginx configuration

**CONFLICT**: Different nginx configurations will overwrite each other

## 📊 **Script Comparison Matrix**

| Feature | deploy_orchestra_complete.sh | deploy_complete_system.sh | simple_deploy.sh |
|---------|------------------------------|----------------------------|------------------|
| **Complexity** | High | High | Low |
| **SSH Key** | `~/.ssh/id_rsa` | `~/.ssh/orchestra_lambda` | Default |
| **Target Dir** | `/home/ubuntu/orchestra-dev` | `/home/ubuntu/orchestra-dev` | `/home/ubuntu/orchestra-main` |
| **Service Mgmt** | Supervisor + Systemd | Enhanced Supervisor + Systemd | Nohup |
| **Nginx** | Basic proxy | Enhanced proxy | None |
| **Vercel Deploy** | ✅ Yes | ✅ Yes | ❌ No |
| **Health Checks** | ✅ Comprehensive | ✅ Comprehensive | ✅ Basic |
| **Error Handling** | ✅ Good | ✅ Good | ⚠️ Minimal |

## 🎯 **Recommended Resolution**

### **Primary Script Choice**
**`deploy_orchestra_complete.sh`** is the most comprehensive and recent (Jun 15 06:30)

### **Required Fixes Before Execution**
1. **SSH Key Path**: Update to use provided SSH key
2. **Directory Consistency**: Ensure target directory exists
3. **Service Cleanup**: Stop conflicting services before deployment
4. **Nginx Cleanup**: Remove conflicting nginx configurations

### **Execution Order**
1. **Cleanup existing deployments**
2. **Fix SSH key configuration**
3. **Execute `deploy_orchestra_complete.sh`**
4. **Verify deployment**

## ⚠️ **Critical Issues to Address**

### **SSH Key Mismatch**
The provided SSH key format suggests it should be saved and referenced:
```bash
# Save provided SSH key
echo "ssh-rsa AAAAB3NzaC1yc2E..." > ~/.ssh/orchestra_lambda
chmod 600 ~/.ssh/orchestra_lambda
```

### **Directory Structure**
Need to ensure `/home/ubuntu/orchestra-dev` exists or update scripts to use correct path

### **Service Conflicts**
Multiple supervisor/systemd services may conflict - need cleanup before deployment

## 🚀 **Next Steps**

1. **Update SSH key configuration** in chosen script
2. **Clean up conflicting services** on Lambda Labs
3. **Execute the fixed deployment script**
4. **Validate all services are running correctly**

