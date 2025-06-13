# 🎼 Orchestra AI - Real Admin Control Center

A fully functional admin dashboard for managing Orchestra AI system with real-time monitoring, agent management, and system controls.

## 🚀 Features

### Real-Time System Monitoring
- **Live System Metrics**: CPU, memory, disk usage, network I/O
- **Agent Status Tracking**: Active agents, request counts, success rates
- **Performance Analytics**: Response times, throughput, error rates
- **Auto-refresh**: Updates every 10 seconds

### AI Agent Management
- **Agent Deployment**: Deploy new AI agents with custom configurations
- **Agent Control**: Start, stop, restart individual agents
- **Performance Monitoring**: Track requests, success rates, resource usage
- **Status Indicators**: Visual status (active, idle, error, stopped)

### System Administration
- **Emergency Controls**: Emergency stop all agents and workflows
- **System Restart**: Restart all components safely
- **Backup Management**: Create and manage system backups
- **Activity Logging**: Real-time activity feed with detailed logs

### Modern UI/UX
- **Dark Theme**: Professional dark interface optimized for monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Live data updates without page refresh
- **Interactive Controls**: Click-to-action buttons with feedback
- **Notifications**: Toast notifications for all actions

## 🏗️ Architecture

### Backend (FastAPI)
```
api/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
└── models/             # Data models (Pydantic)
```

### Frontend (Vanilla JS)
```
web/public/
├── admin.html          # Main admin dashboard
├── dashboard.html      # Alternative dashboard view
└── index.html         # Landing page
```

### Key Components
- **FastAPI Backend**: RESTful API with real system metrics
- **Real-time Updates**: WebSocket-like polling for live data
- **System Integration**: Uses `psutil` for actual system metrics
- **In-memory Storage**: Fast data access (can be replaced with database)

## 🛠️ Installation & Setup

### Quick Start
```bash
# Make startup script executable
chmod +x start_admin_server.sh

# Start the admin server
./start_admin_server.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt

# Start the server
cd api && python main.py
```

### Access Points
- **Admin Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

## 📊 API Endpoints

### System Management
- `GET /api/system/status` - Get system metrics
- `POST /api/system/emergency-stop` - Emergency stop all components
- `POST /api/system/restart` - Restart all components
- `POST /api/system/backup` - Create system backup
- `GET /api/health` - Health check

### Agent Management
- `GET /api/agents` - List all agents
- `GET /api/agents/{id}` - Get agent details
- `POST /api/agents/deploy` - Deploy new agent
- `POST /api/agents/{id}/start` - Start agent
- `POST /api/agents/{id}/stop` - Stop agent

### Workflow Management
- `GET /api/workflows` - List all workflows
- `POST /api/workflows/{id}/start` - Start workflow
- `POST /api/workflows/{id}/pause` - Pause workflow

### Activity & Logging
- `GET /api/activity` - Get activity logs

## 🎯 Usage Guide

### Dashboard Navigation
1. **System Dashboard**: Overview of all system metrics
2. **AI Agents**: Manage individual AI agents
3. **Workflows**: Control automated workflows
4. **Activity Logs**: View system activity and events

### Agent Management
1. **Deploy Agent**: Click "Deploy New Agent" button
2. **Control Agents**: Use Start/Stop buttons on agent cards
3. **Monitor Performance**: View real-time metrics for each agent
4. **View Details**: Click "Details" for comprehensive agent info

### System Controls
1. **Emergency Stop**: Immediately halt all operations
2. **System Restart**: Safely restart all components
3. **Create Backup**: Generate system backup
4. **Refresh Data**: Manually refresh all data

### Monitoring Features
- **Real-time Metrics**: System stats update every 10 seconds
- **Status Indicators**: Color-coded status for quick assessment
- **Activity Feed**: Live stream of system events
- **Performance Tracking**: Historical data and trends

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# System Settings
AUTO_REFRESH_INTERVAL=10000  # milliseconds
MAX_ACTIVITY_LOGS=50
BACKUP_RETENTION_DAYS=30
```

### Customization
- **Themes**: Modify CSS variables in `admin.html`
- **Refresh Rate**: Change `refreshInterval` in JavaScript
- **API Endpoints**: Update `API_BASE` constant
- **Agent Types**: Extend agent deployment options

## 🚀 Deployment

### Local Development
```bash
./start_admin_server.sh
```

### Production Deployment
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app

# Using Docker
docker build -t orchestra-admin .
docker run -p 8000:8000 orchestra-admin
```

### Vercel Deployment
```bash
# Deploy frontend
cd web
vercel deploy

# Deploy API (separate service)
cd api
vercel deploy
```

## 📈 Performance

### Metrics Tracked
- **System Resources**: CPU, Memory, Disk, Network
- **Agent Performance**: Requests/min, Success rate, Response time
- **System Health**: Uptime, Error rates, Component status
- **User Activity**: Admin actions, Deployments, System changes

### Optimization Features
- **Efficient Polling**: Smart refresh intervals
- **Lazy Loading**: Load data on demand
- **Caching**: In-memory caching for frequently accessed data
- **Background Tasks**: Non-blocking operations

## 🔒 Security

### Built-in Security
- **CORS Protection**: Configurable cross-origin policies
- **Input Validation**: Pydantic model validation
- **Error Handling**: Secure error messages
- **Rate Limiting**: API request throttling

### Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

## 🐛 Troubleshooting

### Common Issues
1. **Port Already in Use**: Change port in `main.py`
2. **Permission Denied**: Run `chmod +x start_admin_server.sh`
3. **Module Not Found**: Ensure virtual environment is activated
4. **API Connection Failed**: Check if backend server is running

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
python api/main.py
```

### Health Check
```bash
# Test API health
curl http://localhost:8000/api/health
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install dependencies
4. Make changes
5. Test thoroughly
6. Submit pull request

### Code Style
- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ features
- **HTML/CSS**: Semantic markup, BEM methodology

## 📄 License

MIT License - see LICENSE file for details.

---

**🎼 Orchestra AI Admin System - Conduct your AI symphony with precision and control!** 