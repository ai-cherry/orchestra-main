# Orchestra AI MVP Setup Guide

This guide will help you set up the enhanced Orchestra AI MVP with native natural language interaction, advanced vector memory, and comprehensive data source integrations.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Redis server
- Google Cloud Project with appropriate APIs enabled
- API keys for data sources (Gong, Salesforce, HubSpot, Slack, Looker)

### 2. Installation

```bash
# Install MVP requirements
pip install -r requirements-mvp.txt

# Start Redis (required for vector memory caching)
# Option A: Using Docker
docker run -d -p 6379:6379 redis:alpine

# Option B: Local Redis installation
redis-server

# Verify Redis is running
redis-cli ping
```

### 3. Environment Configuration

Create a `.env` file with your API keys:

```bash
# Google Cloud Platform
GOOGLE_CLOUD_PROJECT=cherry-ai-project
PORTKEY_API_KEY=your_portkey_api_key

# Data Source API Keys
GONG_API_KEY=your_gong_api_key
SALESFORCE_CLIENT_ID=your_salesforce_client_id
SALESFORCE_CLIENT_SECRET=your_salesforce_client_secret
HUBSPOT_API_KEY=your_hubspot_api_key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
LOOKER_CLIENT_ID=your_looker_client_id
LOOKER_CLIENT_SECRET=your_looker_client_secret
LOOKER_BASE_URL=https://your-company.looker.com
```

### 4. Initialize the System

```bash
# Initialize the MVP system
python mvp_orchestra_ai.py init

# This will:
# ✓ Initialize the Enhanced Vector Memory System
# ✓ Set up Data Aggregation Orchestrator
# ✓ Configure all available data source integrations
# ✓ Initialize the Enhanced Natural Language Interface
```

## 🎯 MVP Features Overview

### Enhanced Vector Memory System
- **Semantic Search**: High-performance vector similarity search across all data sources
- **Contextual Memory**: Rich metadata and relationship mapping between memories
- **Real-time Caching**: Redis-backed embedding cache for fast retrieval
- **Memory Relationships**: Graph-based memory connections for enhanced context

### Data Source Integrations
- **Gong.io**: Call recordings, transcripts, insights, and deal intelligence
- **Salesforce**: Accounts, opportunities, contacts, and activities
- **HubSpot**: Contacts, companies, deals, and marketing data
- **Slack**: Messages, channels, threads, and user interactions
- **Looker**: Dashboards, looks, explores, and business intelligence data

### Natural Language Interface
- **Context-Aware Conversations**: Maintains conversation history and context
- **Intent Classification**: Automatically understands user intent
- **Multi-Modal AI Routing**: Uses best AI model for each query type
- **Real-Time Data Integration**: Access to all synchronized data during conversations

## 💬 Using the MVP

### Interactive Chat Mode

```bash
# Start a casual conversation
python mvp_orchestra_ai.py chat --mode casual

# Start an analytical conversation
python mvp_orchestra_ai.py chat --mode analytical

# Available modes: casual, analytical, technical, strategic, creative
```

#### Chat Commands:
- **Regular conversation**: Just type naturally
- **`sync`**: Synchronize data from all configured sources
- **`search <query>`**: Search across all memory
- **`quit`/`exit`/`bye`**: End conversation

### Data Synchronization

```bash
# Sync last 24 hours of data from all sources
python mvp_orchestra_ai.py sync

# Sync last 7 days of data
python mvp_orchestra_ai.py sync --hours 168

# This will sync:
# - Gong call recordings and insights
# - Salesforce CRM data
# - HubSpot marketing and sales data
# - Slack conversations
# - Looker dashboards and analytics
```

### Memory Search

```bash
# Search across all data sources
python mvp_orchestra_ai.py search "client feedback on new product"

# Search specific sources
python mvp_orchestra_ai.py search "pipeline updates" --sources salesforce hubspot

# Get more results
python mvp_orchestra_ai.py search "team communication" --top-k 10
```

## 🔧 Advanced Configuration

### Memory System Tuning

```python
# In your code, customize memory settings
memory_system = EnhancedVectorMemorySystem(
    project_id="your-project",
    embedding_model="all-MiniLM-L6-v2",  # Fast and accurate
    # embedding_model="all-mpnet-base-v2",  # More accurate, slower
    max_context_memories=30,  # Increase for more context
    context_window_days=60    # Extend memory window
)
```

### Data Source Rate Limiting

```python
# Adjust rate limits per source in mvp_orchestra_ai.py
configs = {
    "gong": DataSourceConfig(rate_limit=0.5),      # 0.5 req/sec
    "salesforce": DataSourceConfig(rate_limit=2.0), # 2 req/sec
    "hubspot": DataSourceConfig(rate_limit=10.0),   # 10 req/sec
    "slack": DataSourceConfig(rate_limit=1.0),      # 1 req/sec
    "looker": DataSourceConfig(rate_limit=5.0)      # 5 req/sec
}
```

### Conversation Modes

Each mode optimizes the AI response style:

- **Casual**: Friendly, conversational responses
- **Analytical**: Data-driven, analytical responses with insights
- **Technical**: Detailed technical explanations and solutions
- **Strategic**: High-level strategic thinking and recommendations
- **Creative**: Creative problem-solving and ideation

## 📊 Example Use Cases

### 1. Sales Pipeline Analysis
```
You: "What are the latest updates on our Q4 pipeline from Salesforce and Gong calls?" 