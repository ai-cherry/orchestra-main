# Orchestra AI - Real Agents System

## Overview

Orchestra AI now features **REAL working agents** that perform actual system monitoring, data analysis, and service checks. No more mock data!

## Real Agents

### 🖥️ System Monitor (`sys-001`)
- **Purpose**: Monitors system resources and executes system commands
- **Capabilities**:
  - CPU usage monitoring: Returns real-time CPU percentage
  - Memory monitoring: Shows actual RAM usage and total
  - Disk usage: Reports real disk space statistics
  - System commands: Can execute basic shell commands

### 📊 Data Analyzer (`analyze-001`)
- **Purpose**: Analyzes data and provides insights
- **Capabilities**:
  - Text analysis: Counts words and characters
  - File counting: Can count Python files in directories
  - Complexity scoring: Analyzes task complexity

### 🔍 Service Monitor (`monitor-001`)
- **Purpose**: Monitors services and system health
- **Capabilities**:
  - Service checks: Reports operational services
  - Alert monitoring: Tracks system alerts
  - Health monitoring: Overall system status

## Installation

### Prerequisites
- Python 3.10+
- Redis server
- Nginx (for web deployment)

### Local Development
```bash
# Clone the repository
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/production/requirements.txt

# Test the agents
python test_real_agents.py

# Start the API
python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
```

### Production Deployment
The real agents are deployed at `/root/orchestra-main` on the production server.

Service configuration: `/etc/systemd/system/orchestra-real.service`

## API Endpoints

### Get All Agents
```bash
GET /api/agents
X-API-Key: <your-api-key>
```

Response:
```json
[
  {
    "id": "sys-001",
    "name": "System Monitor",
    "type": "system",
    "status": "idle",
    "lastRun": "2025-05-31T17:31:52.279048",
    "description": "Monitors system resources and runs system commands",
    "memory_usage": 45.6,
    "tasks_completed": 0,
    "current_task": null
  },
  ...
]
```

### Query Agents
```bash
POST /api/query
X-API-Key: <your-api-key>
Content-Type: application/json

{
  "query": "check CPU usage"
}
```

Response:
```json
{
  "response": "Current CPU usage: 23.5%",
  "agent_id": "sys-001",
  "timestamp": "2025-05-31T17:32:25.290604",
  "tokens_used": 9
}
```

## Example Queries

- **System Monitoring**:
  - "Check CPU usage" → Real CPU percentage
  - "Check memory status" → Actual RAM usage
  - "Check disk usage" → Real disk statistics

- **Data Analysis**:
  - "Analyze this data" → Character/word count
  - "Count files" → Counts Python files
  - "Analyze complexity" → Task complexity score

- **Service Monitoring**:
  - "Check services" → Service status
  - "Monitor system" → System health
  - "Check alerts" → Active alerts

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Admin UI      │────▶│   API Server    │
│  (React/Vite)   │     │  (FastAPI)      │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
            ┌───────▼──────┐ ┌───▼────┐ ┌────▼─────┐
            │ System Agent │ │Analyzer│ │ Monitor  │
            │  (sys-001)   │ │(analyze│ │(monitor- │
            └──────────────┘ │ -001)  │ │  001)    │
                            └────────┘ └──────────┘
```

## Configuration

Environment variables in `.env`:
```bash
# API Configuration
ORCHESTRA_API_KEY=<your-secure-api-key>

# Redis Configuration
REDIS_URL=redis://localhost:6379

# OpenAI Configuration (optional)
OPENAI_API_KEY=<your-openai-key>
```

## Troubleshooting

### Check Service Status
```bash
systemctl status orchestra-real
```

### View Logs
```bash
journalctl -u orchestra-real -f
```

### Test Agents Locally
```bash
python test_real_agents.py
```

### Common Issues
1. **psutil not installed**: Run `pip install psutil`
2. **Port already in use**: Kill existing process with `pkill -f uvicorn`
3. **Redis not running**: Start with `systemctl start redis-server`

## Security

- API requires authentication via `X-API-Key` header
- Default key should be changed in production
- Service runs as root (consider creating dedicated user for production)

## Future Enhancements

- [ ] Add more agent types (database monitor, log analyzer, etc.)
- [ ] Implement agent communication/coordination
- [ ] Add persistent task queuing
- [ ] Integrate with external monitoring tools
- [ ] Add WebSocket support for real-time updates

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-agent`)
3. Commit your changes (`git commit -m 'Add amazing agent'`)
4. Push to the branch (`git push origin feature/amazing-agent`)
5. Open a Pull Request

## License

[Add your license here]
