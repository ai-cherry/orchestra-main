# 🎯 Orchestra AI Project Priorities & AI Assistant Guidelines

## 🚀 **Core Project Philosophy**

**Performance > Security** (Solo Development Mode)
- Fast iteration and development velocity prioritized
- Security measures optimized for single-developer workflow
- Production-grade security implemented at deployment boundaries

## 🤖 **AI Assistant Permissions & Boundaries**

### **✅ AUTHORIZED AI OPERATIONS**

#### **Infrastructure & Deployment**
- **GitHub Operations**: Full repository management, branch operations, PR creation
- **Cloud Infrastructure**: Lambda Labs deployment, Pulumi stack management
- **Database Operations**: Schema updates, data migration, performance optimization
- **MCP Server Management**: Configuration, deployment, monitoring
- **Container Management**: Docker operations, service orchestration

#### **Development Operations**
- **Code Generation**: Full codebase modification, refactoring, optimization
- **Configuration Management**: Environment setup, service configuration
- **Testing**: Automated test creation, integration testing
- **Documentation**: Real-time documentation updates, API documentation

#### **Secret & Credential Management**
- **Environment Variables**: Read/write operations via `core/env_config.py`
- **Pulumi Secrets**: Full access to Pulumi secret management
- **API Key Usage**: Authorized to use GitHub, GCP, Lambda Labs credentials
- **Database Credentials**: Access via centralized configuration only

### **🚫 PROHIBITED OPERATIONS**

#### **Security Boundaries**
- **No Production Secret Exposure**: Never log or display actual secret values
- **No Git History Modification**: Avoid rewriting history with sensitive data
- **No Credential Hardcoding**: All secrets must use centralized config
- **No Unauthorized Network Access**: Stick to approved endpoints and services

#### **Operational Boundaries**
- **No Manual Server Access**: Use automation tools and scripts only
- **No Data Deletion**: Never delete user data without explicit confirmation
- **No Service Interruption**: Avoid operations that would break running services

## 🔐 **Secret Management Policy**

### **Single Source of Truth: Pulumi + Environment**
```python
# ✅ CORRECT: Use centralized settings
from legacy.core.env_config import settings
api_key = settings.notion_api_token

# ❌ FORBIDDEN: Hardcoded secrets
api_key = "ntn_actual_secret_key_here"
```

### **Access Hierarchy**
1. **Pulumi Secrets** (Production): `pulumi config set --secret`
2. **Environment Variables** (Development): `.env` file via `settings`
3. **Fallback Values** (Development only): Empty strings or clear placeholders

### **Documentation Standards**
- **Use Placeholders**: `<api-key>`, `<secret-value>`, `<token>`
- **Reference Settings**: Always point to `settings.api_key`
- **No Real Values**: Never include actual secrets in docs

## ⚡ **Performance vs Security Trade-offs**

### **Solo Developer Optimizations**
- **Local Development**: Simplified auth, shared credentials, fast iteration
- **Rapid Prototyping**: Performance-first approach for feature development
- **Resource Efficiency**: 70% reduction in background services for speed

### **Production Security Gates**
- **Deployment Boundaries**: Full security validation at production deployment
- **Credential Rotation**: Automated rotation for production environments
- **Access Logging**: Comprehensive audit trails for production operations
- **Compliance Controls**: HIPAA/PCI compliance for respective domains

## 🔍 **Auditing & Monitoring Expectations**

### **AI Assistant Activity Tracking**
- **All operations logged** to Notion workspace via MCP integration
- **Performance metrics** tracked for optimization
- **Error patterns** monitored for improvement
- **Success rates** measured for reliability

### **Security Audit Requirements**
- **Monthly secret rotation** for production systems
- **Quarterly access review** for AI assistant permissions
- **Real-time monitoring** of credential usage patterns
- **Incident response** procedures for security events

## 🎭 **Persona-Specific Guidelines**

### **Cherry (Personal Overseer)**
- **Cross-domain coordination**: Full access to all system components
- **Project management**: Can modify task priorities and workflows
- **Team communication**: Authorized for external communications

### **Sophia (Financial Expert)**
- **PayReady systems**: Full access with PCI compliance requirements
- **Financial data**: Encrypted storage and transmission mandatory
- **Regulatory compliance**: Must follow financial industry standards

### **Karen (Medical Specialist)**
- **ParagonRX systems**: Full access with HIPAA compliance requirements
- **Medical data**: Encrypted storage with audit trails
- **Clinical standards**: Must follow medical coding regulations

## 🚀 **Development Velocity Guidelines**

### **Fast Track Operations** (No approval needed)
- Code generation and refactoring
- Documentation updates
- Test creation and execution
- Local environment setup
- MCP server configuration

### **Standard Track Operations** (Automated approval)
- Database schema changes
- Infrastructure updates via Pulumi
- Production environment variables
- Service deployment configurations

### **Review Track Operations** (Manual approval)
- Production secret rotation
- Security policy changes
- External service integrations
- Data migration operations

## 📊 **Success Metrics**

### **Development Velocity**
- **Code generation speed**: 3-5x faster than manual coding
- **Bug resolution time**: <30 minutes average
- **Feature delivery**: Same-day for simple features
- **Infrastructure updates**: <15 minutes deployment

### **System Reliability**
- **Uptime**: >99.9% for production services
- **Response time**: <200ms for API operations
- **Error rates**: <0.1% for critical paths
- **Recovery time**: <5 minutes for service restoration

## 🎯 **Priority Matrix**

| Priority | Focus Area | AI Assistant Role |
|----------|------------|-------------------|
| **P0** | System Security | Enforce all security policies |
| **P1** | Development Velocity | Maximize automation and speed |
| **P2** | User Experience | Optimize for developer workflow |
| **P3** | Resource Efficiency | Minimize system overhead |
| **P4** | Documentation | Maintain real-time documentation |

---

**Last Updated**: $(date)  
**Approval Authority**: Solo Developer (Performance-First Mode)  
**Review Cycle**: Monthly for effectiveness, Quarterly for security 