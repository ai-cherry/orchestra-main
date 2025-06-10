# Sequential Thinking: AWS Removal & Cloud Service Optimization Strategy

## 🎯 **Objective**
Complete removal of AWS dependencies and alignment with modern cloud stack:
- **Compute**: Lambda Labs (GPU instances)
- **Frontend**: Vercel
- **Databases**: PostgreSQL, Redis (self-hosted on Lambda Labs)
- **Vector Stores**: Pinecone Cloud, Weaviate Cloud
- **Data Integration**: Airbyte
- **IaC**: Pulumi

## 📊 **Current State Analysis**

### **AWS Dependencies to Remove**
1. **Deployment Scripts**:
   - `deploy_production.sh` - AWS ECS/ECR deployment
   - GitHub secrets for AWS credentials
   - AWS CLI dependencies

2. **Infrastructure Code**:
   - `infrastructure/index.ts` - AWS resources (ECR, ECS, ALB, Route53)
   - `infrastructure/feedback_system.py` - AWS RDS, ElastiCache, EC2

3. **Storage & Services**:
   - S3 references in ML scripts
   - AWS-specific Prefect configuration
   - ECR for container registry

4. **Documentation**:
   - AWS references in architecture docs
   - AWS-specific deployment guides

### **GCP Dependencies to Evaluate**
1. **Pinecone Configuration**:
   - Currently using `us-west1-gcp` region
   - Explore Pinecone's cloud-native options

2. **Firestore References**:
   - Memory adapter using Firestore
   - Should be replaced with Redis on Lambda Labs

## 🚀 **Implementation Strategy**

### **Phase 1: Remove AWS Infrastructure Code**
1. Delete AWS-specific deployment scripts
2. Remove AWS Pulumi configurations
3. Clean up AWS dependencies from requirements

### **Phase 2: GitHub Secrets Cleanup**
1. Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
2. Add Lambda Labs and Vercel tokens
3. Update CI/CD workflows

### **Phase 3: Replace AWS Services**
1. **Container Registry**: ECR → GitHub Container Registry or Docker Hub
2. **Object Storage**: S3 → MinIO on Lambda Labs or Backblaze B2
3. **Managed Database**: RDS → PostgreSQL on Lambda Labs
4. **Cache**: ElastiCache → Redis on Lambda Labs

### **Phase 4: Optimize Cloud Services**
1. **Pinecone**: Investigate cloud regions and pricing
2. **Weaviate**: Verify cloud configuration is optimal
3. **Redis**: Deploy on Lambda Labs for low latency

### **Phase 5: Update Documentation**
1. Remove all AWS references
2. Document new deployment strategy
3. Update architecture diagrams

## 📋 **Implementation Checklist**

### **Immediate Actions**
- [ ] Remove `deploy_production.sh`
- [ ] Delete `infrastructure/index.ts` (AWS-specific)
- [ ] Remove AWS credentials from GitHub secrets
- [ ] Update `infrastructure/feedback_system.py` for Lambda Labs

### **Service Replacements**
- [ ] ECR → GitHub Container Registry
- [ ] S3 → MinIO or Backblaze B2
- [ ] RDS → PostgreSQL on Lambda Labs
- [ ] ElastiCache → Redis on Lambda Labs
- [ ] Route53 → Vercel DNS or Cloudflare

### **Code Updates**
- [ ] Remove `prefect-aws` dependency
- [ ] Update all S3 URIs to configurable endpoints
- [ ] Replace FirestoreMemoryAdapter with RedisMemoryAdapter
- [ ] Update Pinecone configuration for optimal region

### **Documentation Updates**
- [ ] Update HIGH_LEVEL_ARCHITECTURE.md
- [ ] Update SECRETS_CONFIGURATION.md
- [ ] Remove AWS-specific guides
- [ ] Create Lambda Labs deployment guide

## 🔧 **Technical Implementation Details**

### **1. Container Registry Migration**
```yaml
# Before (AWS ECR)
image: 123456789.dkr.ecr.us-east-1.amazonaws.com/orchestra:latest

# After (GitHub Container Registry)
image: ghcr.io/ai-cherry/orchestra:latest
```

### **2. Object Storage Migration**
```python
# Before
artifact_store_uri = "s3://bucket/mlflow-artifacts"

# After (MinIO on Lambda Labs)
artifact_store_uri = os.getenv("OBJECT_STORAGE_URI", "http://minio:9000/mlflow-artifacts")
```

### **3. Database Configuration**
```python
# Before (AWS RDS)
database_url = "postgresql://user:pass@rds.amazonaws.com/db"

# After (Lambda Labs PostgreSQL)
database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/orchestra")
```

## 🌐 **Cloud Service Analysis**

### **Pinecone Cloud Options**
1. **Regions Available**:
   - us-west1-gcp (current)
   - us-east1-gcp
   - eu-west1-gcp
   - us-central1-gcp
   
2. **Recommendation**: Stay with us-west1-gcp if Lambda Labs instances are in US West

### **Weaviate Cloud**
- Already using cloud version ✅
- Ensure API keys are properly configured
- Consider data residency requirements

### **MinIO vs Backblaze B2**
- **MinIO**: Self-hosted on Lambda Labs, S3-compatible, no egress fees
- **Backblaze B2**: Managed service, S3-compatible, low storage costs
- **Recommendation**: MinIO for development, Backblaze B2 for production backups

## 🎯 **Success Metrics**
1. Zero AWS dependencies in codebase
2. All services running on Lambda Labs + Vercel + managed cloud services
3. Simplified deployment with single `deploy_lambda_labs.sh` script
4. Reduced cloud costs by eliminating unnecessary AWS services
5. Improved performance with services co-located on Lambda Labs

## 🚨 **Risk Mitigation**
1. **Data Migration**: Backup all data before migrating from AWS services
2. **Gradual Rollout**: Test each service replacement in staging first
3. **Rollback Plan**: Keep AWS resources for 30 days after migration
4. **Monitoring**: Set up comprehensive monitoring on new infrastructure

---

**Ready to execute this comprehensive AWS removal strategy!** 