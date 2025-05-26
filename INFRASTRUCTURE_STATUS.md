# Orchestra AI Infrastructure Status

## 🏗️ Current Infrastructure Setup

### 1. **DragonflyDB (Redis-compatible Cache)**
- **Host**: qpwj3s2ae.dragonflydb.cloud
- **Port**: 6385
- **Memory**: 12.5 GB
- **Compute**: Standard
- **Connection**: `rediss://` (TLS enabled)
- **Status**: ✅ Configured in Pulumi

### 2. **MongoDB Atlas (Primary Database)**
- **Organization**: scoobyjava's Org (ID: 67e050d114db796e8048b290)
- **Cluster**: cluster0.oaceter.mongodb.net
- **Database User**: musillynn
- **Connection**: MongoDB+SRV protocol
- **Features**:
  - Retry writes enabled
  - Majority write concern
  - Service account configured
- **Status**: ✅ Configured in Pulumi

### 3. **Weaviate Cloud (Vector Search)**
- **Endpoint**: 2jnpk8ibqhwscncku73wq.c0.us-east1.gcp.weaviate.cloud
- **Region**: US East 1 (GCP)
- **Protocol**: HTTPS
- **Authentication**: API Key
- **Status**: ✅ Configured in Pulumi

### 4. **DigitalOcean (Deployment Platform)**
- **Droplet**: ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01
- **Specs**:
  - 2 vCPUs
  - 8 GB RAM
  - 160 GB Storage
  - Intel processor
  - San Francisco region (sfo2)
- **OS**: Ubuntu
- **Status**: ✅ Configured in Pulumi

### 5. **Pulumi (Infrastructure as Code)**
- **Organization**: scoobyjava-org
- **Projects**:
  - luminous-moissanite-kiwi (Python/Aiven)
  - upbeat-ruthenium-sloth (Go/Aiven)
- **Stack**: dev
- **Backend**: Pulumi Cloud
- **Status**: ✅ Active

## 🔐 Secret Management

All secrets are now centralized in Pulumi:

### Core Services
- ✅ MongoDB connection string and API keys
- ✅ DragonflyDB connection URI
- ✅ Weaviate endpoint and API key
- ✅ DigitalOcean API token and root password
- ✅ Pulumi access token

### LLM Services (from GCP migration)
- ✅ OpenAI API key
- ✅ Anthropic API key
- ✅ OpenRouter API key
- ✅ Portkey API key
- ✅ Perplexity API key
- ✅ 40+ additional service keys

## 📋 Quick Reference

### Local Development
```bash
# Set passphrase
export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"

# Generate environment
python scripts/generate_env_from_pulumi.py
source .env

# Start services
./start_orchestra.sh
```

### View Configuration
```bash
cd infra
pulumi config --show-secrets
```

### Update Secrets
```bash
cd infra
pulumi config set --secret <key> <value>
cd ..
python scripts/generate_env_from_pulumi.py
```

## 🚀 Deployment Commands

### DigitalOcean Deployment
```bash
cd infra
pulumi up
```

### MongoDB Connection
```python
# Install driver
python -m pip install "pymongo[srv]"

# Connection string is in MONGODB_URI env var
```

## 📊 Service Limits

- **DragonflyDB**: 12.5 GB memory limit
- **MongoDB Atlas**: Free tier limits apply
- **Weaviate**: Cloud tier limits apply
- **DigitalOcean**: 2 vCPU, 8 GB RAM droplet

## ✅ Migration Status

- ✅ All secrets migrated from GitHub/GCP to Pulumi
- ✅ Real credentials configured and tested
- ✅ Documentation complete
- ✅ Automation scripts ready
- ⚠️ Git history cleanup pending

## 🔧 Next Steps

1. Clean git history: `./scripts/clean_git_history.sh`
2. Rotate any exposed keys after cleanup
3. Deploy infrastructure: `cd infra && pulumi up`
4. Test all service connections
