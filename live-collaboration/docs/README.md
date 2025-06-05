# Live Collaboration System - Cursor ↔ Manus AI

> **Real-time pair programming between Cursor IDE and Manus AI**

## 🎯 Project Overview

This system enables **true real-time collaboration** between Cursor IDE and Manus AI, eliminating the need for GitHub commits to share code changes. Manus can see your code changes **instantly** as you type, enabling seamless AI-assisted development.

### Key Features

- ✅ **Real-time file synchronization** - Changes appear instantly in shared database
- ✅ **WebSocket-based communication** - Low-latency, bidirectional updates  
- ✅ **Cursor IDE integration** - Automatic file watching with smart filtering
- ✅ **Manus AI visibility** - Complete access to live development session
- ✅ **Session persistence** - Collaborate across disconnections
- ✅ **Change history tracking** - Full audit trail of modifications
- ✅ **Multi-file support** - Tracks Python, JavaScript, TypeScript, and more
- ✅ **Conflict resolution** - Handles simultaneous edits gracefully

## 🏗️ System Architecture

```
┌─────────────────┐    WebSocket     ┌─────────────────┐    Database    ┌─────────────────┐
│   Cursor IDE    │ ◄─────────────► │ Collaboration   │ ◄────────────► │   PostgreSQL    │
│                 │                 │     Server      │                │     +Redis      │
│ - File Watcher  │                 │                 │                └─────────────────┘
│ - Change Stream │                 │ - Session Mgmt  │                         ▲
│ - Auto Sync     │                 │ - Real-time Hub │                         │
└─────────────────┘                 │ - Conflict Res  │                         │
                                    └─────────────────┘                         │
                                             ▲                                  │
                                             │ WebSocket                        │
                                             ▼                                  │
                                    ┌─────────────────┐                         │
                                    │    Manus AI     │ ◄───────────────────────┘
                                    │                 │      Direct Access
                                    │ - Live Files    │
                                    │ - Change Stream │
                                    │ - History View  │
                                    └─────────────────┘
```

## 🚀 Quick Start

### 1. Setup

```bash
cd live-collaboration
chmod +x setup_collaboration.sh
./setup_collaboration.sh
```

### 2. Start Collaboration Server

```bash
./start_collaboration_server.sh
```

### 3. Connect Cursor IDE

```bash
# In your project directory
./start_cursor_watcher.sh /path/to/your/project my-session-123
```

### 4. Connect Manus AI

```bash
./start_manus_client.sh
```

### 5. Verify Everything Works

```bash
./run_tests.sh
```

## 📁 Project Structure

```
live-collaboration/
├── cursor-plugin/          # Cursor IDE integration
│   └── file_watcher.py     # Real-time file monitoring
├── sync-server/            # WebSocket collaboration server
│   └── collaboration_server.py
├── database/               # Database schema and migrations
│   └── schema.sql          # PostgreSQL tables for collaboration
├── manus-interface/        # Manus AI client interface
│   └── manus_client.py     # API for Manus to access live files
├── tests/                  # Comprehensive test suite
│   └── test_collaboration.py
├── docs/                   # Documentation
│   └── README.md           # This file
├── requirements.txt        # Python dependencies
└── setup_collaboration.sh # One-click setup script
```

## 🔧 Component Details

### Cursor Plugin (`cursor-plugin/`)

**Purpose**: Watches Cursor workspace for file changes and streams them to the collaboration server.

**Key Features**:
- File system monitoring with `watchdog`
- Smart file filtering (ignores `.git`, `node_modules`, etc.)
- Debounced change detection (avoids spam)
- Content hashing for efficient sync
- WebSocket streaming to server

**Usage**:
```bash
python cursor-plugin/file_watcher.py /path/to/workspace --session-id my-session
```

### Collaboration Server (`sync-server/`)

**Purpose**: Central hub for real-time communication between Cursor and Manus.

**Key Features**:
- WebSocket server on port 8765
- Session management and persistence
- Real-time file change broadcasting
- Database persistence with PostgreSQL
- Redis caching for performance
- Conflict resolution and change ordering

**WebSocket Protocol**:
```json
// Cursor → Server (file change)
{
  "type": "file_change",
  "file_path": "/full/path/to/file.py",
  "relative_path": "src/main.py",
  "content": "print('hello world')",
  "change_type": "modify"
}

// Server → Manus (change notification)
{
  "type": "file_change",
  "relative_path": "src/main.py",
  "content": "print('hello world')",
  "change_type": "modify",
  "timestamp": "2025-06-05T08:30:00Z"
}
```

### Database Schema (`database/`)

**Purpose**: Persistent storage for collaboration sessions and file changes.

**Key Tables**:
- `collaboration_sessions` - Active collaboration sessions
- `live_files` - Current state of tracked files
- `live_changes` - Complete change history with rollback support
- `manus_activity` - Manus AI interaction tracking
- `live_cursors` - Real-time cursor positions (future feature)

### Manus Interface (`manus-interface/`)

**Purpose**: Clean API for Manus AI to access live development files and changes.

**Key Methods**:
```python
# Connect to a collaboration session
await client.connect_to_session("session-123")

# Get all current files
files = await client.get_current_files()

# Get specific file content
content = await client.get_file_content("src/main.py")

# Watch for changes
async def on_change(file_path, change_type, data):
    print(f"File {file_path} was {change_type}")

await client.watch_changes(on_change)

# Query by file type
python_files = await client.get_python_files()
js_files = await client.get_javascript_files()

# Get session history
recent_changes = await client.get_recent_changes(limit=10)
```

## 🔧 Configuration

The system uses environment variables for configuration:

```bash
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orchestra_main
DB_USER=postgres
DB_PASSWORD=postgres

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Collaboration server
COLLABORATION_PORT=8765
COLLABORATION_HOST=0.0.0.0

# File tracking
TRACK_EXTENSIONS=.py,.js,.ts,.jsx,.tsx,.html,.css,.json,.md
IGNORE_PATTERNS=.git,.vscode,__pycache__,node_modules,.env
```

## 🧪 Testing

The test suite validates end-to-end functionality:

```bash
# Run all tests
./run_tests.sh

# Or run directly
python tests/test_collaboration.py
```

**Test Coverage**:
- ✅ WebSocket connections (Cursor ↔ Server ↔ Manus)
- ✅ File synchronization (create, modify, delete)
- ✅ Real-time change detection
- ✅ Session persistence and recovery
- ✅ Multi-file type support
- ✅ Performance with large files
- ✅ Database integrity
- ✅ Error handling and reconnection

## 🚀 Production Deployment

### Lambda Labs Server Setup

1. **Install dependencies on Lambda Labs server**:
```bash
ssh ubuntu@150.136.94.139
cd /path/to/orchestra-main-2/live-collaboration
./setup_collaboration.sh
```

2. **Configure systemd service**:
```bash
sudo cp systemd/collaboration-server.service /etc/systemd/system/
sudo systemctl enable collaboration-server
sudo systemctl start collaboration-server
```

3. **Configure firewall**:
```bash
sudo ufw allow 8765/tcp  # WebSocket port
```

### Cursor IDE Setup

1. **On your local machine**:
```bash
# Clone or sync the live-collaboration directory
git clone <repo> live-collaboration
cd live-collaboration
pip install -r requirements.txt

# Start watching your project
./start_cursor_watcher.sh /path/to/your/project --server ws://150.136.94.139:8765
```

### Manus AI Integration

1. **In Manus AI system**:
```python
from live_collaboration.manus_interface.manus_client import ManusCollaborationClient

# Connect to remote collaboration server
client = ManusCollaborationClient("ws://150.136.94.139:8765")

# Get available sessions
sessions = client.get_available_sessions()
latest_session = sessions[0]['cursor_session_id']

# Start monitoring
await client.monitor_session(latest_session)

# Access live files
python_files = await client.get_python_files()
for file_data in python_files:
    content = await client.get_file_content(file_data['relative_path'])
    # Manus can now see live code as it's being written!
```

## 🔍 Monitoring & Debugging

### Log Locations

- **Collaboration Server**: `journalctl -u collaboration-server -f`
- **Cursor Watcher**: Terminal output with `--verbose` flag
- **Manus Client**: Python logging output

### Health Checks

```bash
# Check if collaboration server is running
curl -I http://localhost:8765

# Check database connectivity
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', database='orchestra_main', user='postgres', password='postgres')
print('DB OK')
"

# Check Redis connectivity
redis-cli ping
```

### Common Issues

| Issue | Solution |
|-------|----------|
| WebSocket connection fails | Check firewall, verify server is running on correct port |
| Files not syncing | Verify file extensions are in `TRACK_EXTENSIONS` |
| Database errors | Check PostgreSQL is running, schema is installed |
| Performance issues | Monitor Redis cache, check file sizes |
| Session not found | Verify Cursor watcher created session first |

## 🔮 Future Enhancements

- **Real-time cursor positions** - See where collaborators are editing
- **Live voice/video integration** - Talk while coding
- **Multi-user sessions** - Multiple developers + Manus
- **IDE plugins** - Native VS Code, PyCharm integration
- **Smart conflict resolution** - AI-assisted merge conflict resolution
- **Performance optimization** - Binary diff algorithms for large files
- **Security** - End-to-end encryption for sensitive projects

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `./run_tests.sh`
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs with `--verbose` flag
3. Run the test suite to isolate problems
4. Create an issue with detailed logs and reproduction steps

---

**🎉 Enjoy real-time collaboration with Manus AI!**

*No more Git commits just to share code changes - now Manus sees your code as you write it!* 