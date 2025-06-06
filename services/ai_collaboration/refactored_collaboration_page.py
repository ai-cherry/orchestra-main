#!/usr/bin/env python3
"""
AI Collaboration Dashboard - Single Page Component
Refactored to be a sub-component within cherry-ai.me website
Located at: /settings/developer-tools/collaboration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse
import json
import asyncio

from ..auth.dependencies import require_admin_role, get_current_user
from ..models.entities import AITask, AIAgent
from ..models.enums import TaskStatus, AIAgentType
from .service import AICollaborationService


# Create router for collaboration page
collaboration_router = APIRouter(
    prefix="/api/settings/developer-tools/collaboration",
    tags=["developer-tools"],
    dependencies=[Depends(require_admin_role)]  # Admin-only access
)


class CollaborationPageService:
    """
    Service for the AI Collaboration Dashboard page
    This is a single page within the Cherry AI admin interface
    """
    
    def __init__(self, main_service: AICollaborationService):
        self.main_service = main_service
        self.active_sessions: Dict[str, WebSocket] = {}
        self.manus_connection: Optional[WebSocket] = None
        self.cursor_connection: Optional[WebSocket] = None
        
    async def get_page_data(self, user_id: str) -> Dict[str, Any]:
        """Get data for rendering the collaboration page"""
        return {
            "page_title": "AI Development Collaboration",
            "page_description": "Bridge between Manus and Cursor for AI ecosystem development",
            "breadcrumbs": [
                {"label": "Settings", "path": "/settings"},
                {"label": "Developer Tools", "path": "/settings/developer-tools"},
                {"label": "AI Collaboration", "path": "/settings/developer-tools/collaboration"}
            ],
            "features": {
                "real_time_communication": True,
                "task_coordination": True,
                "code_collaboration": True,
                "testing_integration": True,
                "performance_monitoring": True
            },
            "current_status": await self._get_collaboration_status(),
            "recent_tasks": await self._get_recent_development_tasks(),
            "active_connections": {
                "manus": self.manus_connection is not None,
                "cursor": self.cursor_connection is not None
            }
        }
        
    async def _get_collaboration_status(self) -> Dict[str, Any]:
        """Get current collaboration status"""
        # Get development-specific metrics
        metrics = await self.main_service.get_collaboration_metrics()
        
        return {
            "active_development_tasks": metrics.get("active_tasks", 0),
            "completed_today": metrics.get("completed_today", 0),
            "average_completion_time": metrics.get("avg_completion_time", "N/A"),
            "collaboration_health": metrics.get("health_score", 100)
        }
        
    async def _get_recent_development_tasks(self) -> List[Dict[str, Any]]:
        """Get recent development tasks"""
        # Filter for development-related tasks only
        tasks = await self.main_service.database.fetch("""
            SELECT t.*, a.agent_name 
            FROM ai_tasks t
            LEFT JOIN ai_personas a ON t.agent_id = a.id
            WHERE t.task_type IN ('development', 'testing', 'deployment', 'optimization')
            ORDER BY t.created_at DESC
            LIMIT 10
        """)
        
        return [
            {
                "id": task["task_id"],
                "type": task["task_type"],
                "status": task["status"],
                "agent": task["agent_name"] or "Unassigned",
                "created": task["created_at"].isoformat(),
                "description": task["payload"].get("description", "")
            }
            for task in tasks
        ]
        
    async def handle_manus_connection(self, websocket: WebSocket) -> None:
        """Handle Manus AI connection"""
        await websocket.accept()
        self.manus_connection = websocket
        
        try:
            await websocket.send_json({
                "type": "connection_established",
                "agent": "manus",
                "message": "Connected to Cherry AI Collaboration Dashboard"
            })
            
            while True:
                data = await websocket.receive_json()
                await self._process_manus_message(data)
                
        except WebSocketDisconnect:
            self.manus_connection = None
            await self._notify_cursor("manus_disconnected")
            
    async def handle_cursor_connection(self, websocket: WebSocket) -> None:
        """Handle Cursor AI connection"""
        await websocket.accept()
        self.cursor_connection = websocket
        
        try:
            await websocket.send_json({
                "type": "connection_established",
                "agent": "cursor",
                "message": "Connected to Cherry AI Collaboration Dashboard"
            })
            
            while True:
                data = await websocket.receive_json()
                await self._process_cursor_message(data)
                
        except WebSocketDisconnect:
            self.cursor_connection = None
            await self._notify_manus("cursor_disconnected")
            
    async def _process_manus_message(self, data: Dict[str, Any]) -> None:
        """Process message from Manus"""
        message_type = data.get("type")
        
        if message_type == "task_request":
            # Create development task
            task = await self._create_development_task(data)
            await self._notify_cursor("new_task", task)
            
        elif message_type == "code_review":
            # Forward to Cursor for review
            await self._notify_cursor("code_review_request", data)
            
        elif message_type == "deployment_ready":
            # Notify about deployment readiness
            await self._notify_all("deployment_notification", data)
            
    async def _process_cursor_message(self, data: Dict[str, Any]) -> None:
        """Process message from Cursor"""
        message_type = data.get("type")
        
        if message_type == "task_completed":
            # Update task status
            await self._update_task_status(data["task_id"], TaskStatus.COMPLETED)
            await self._notify_manus("task_completed", data)
            
        elif message_type == "code_changes":
            # Forward code changes to Manus
            await self._notify_manus("code_update", data)
            
        elif message_type == "test_results":
            # Share test results
            await self._notify_all("test_results", data)
            
    async def _create_development_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a development task"""
        task = AITask(
            id=0,  # Will be set by database
            task_type=data.get("task_type", "development"),
            payload={
                "description": data.get("description"),
                "requirements": data.get("requirements", []),
                "priority": data.get("priority", "medium"),
                "requested_by": "manus"
            },
            priority=self._map_priority(data.get("priority", "medium"))
        )
        
        # Save to database
        task_id = await self.main_service.database.insert(
            "ai_tasks",
            task_type=task.task_type,
            payload=task.payload,
            status=task.status.value,
            priority=task.priority
        )
        
        return {
            "task_id": task_id,
            "type": task.task_type,
            "status": task.status.value,
            "payload": task.payload
        }
        
    async def _update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status"""
        await self.main_service.database.update(
            "ai_tasks",
            {"task_id": task_id},
            status=status.value,
            updated_at=datetime.utcnow()
        )
        
    async def _notify_manus(self, event_type: str, data: Any = None) -> None:
        """Send notification to Manus"""
        if self.manus_connection:
            try:
                await self.manus_connection.send_json({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except:
                self.manus_connection = None
                
    async def _notify_cursor(self, event_type: str, data: Any = None) -> None:
        """Send notification to Cursor"""
        if self.cursor_connection:
            try:
                await self.cursor_connection.send_json({
                    "type": event_type,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except:
                self.cursor_connection = None
                
    async def _notify_all(self, event_type: str, data: Any = None) -> None:
        """Send notification to all connected agents"""
        await self._notify_manus(event_type, data)
        await self._notify_cursor(event_type, data)
        
    def _map_priority(self, priority_str: str) -> int:
        """Map priority string to numeric value"""
        mapping = {
            "low": 3,
            "medium": 5,
            "high": 7,
            "critical": 9
        }
        return mapping.get(priority_str.lower(), 5)


# Initialize service
collaboration_page_service = None


def get_collaboration_page_service() -> CollaborationPageService:
    """Get or create collaboration page service"""
    global collaboration_page_service
    if not collaboration_page_service:
        # This would be properly initialized with dependencies
        raise RuntimeError("Collaboration page service not initialized")
    return collaboration_page_service


# API Endpoints for the collaboration page

@collaboration_router.get("/")
async def get_collaboration_dashboard(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get collaboration dashboard data"""
    service = get_collaboration_page_service()
    return await service.get_page_data(current_user["id"])


@collaboration_router.get("/status")
async def get_collaboration_status() -> Dict[str, Any]:
    """Get current collaboration status"""
    service = get_collaboration_page_service()
    return await service._get_collaboration_status()


@collaboration_router.get("/tasks")
async def get_development_tasks(
    limit: int = 20,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get development tasks"""
    service = get_collaboration_page_service()
    
    query = """
        SELECT t.*, a.agent_name 
        FROM ai_tasks t
        LEFT JOIN ai_personas a ON t.agent_id = a.id
        WHERE t.task_type IN ('development', 'testing', 'deployment', 'optimization')
    """
    
    if status:
        query += f" AND t.status = '{status}'"
        
    query += " ORDER BY t.created_at DESC LIMIT %s"
    
    tasks = await service.main_service.database.fetch(query, limit)
    
    return [
        {
            "id": task["task_id"],
            "type": task["task_type"],
            "status": task["status"],
            "agent": task["agent_name"] or "Unassigned",
            "created": task["created_at"].isoformat(),
            "payload": task["payload"]
        }
        for task in tasks
    ]


@collaboration_router.post("/tasks")
async def create_development_task(
    task_data: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new development task"""
    service = get_collaboration_page_service()
    
    task_data["requested_by"] = current_user["username"]
    task = await service._create_development_task(task_data)
    
    # Notify connected agents
    await service._notify_all("new_development_task", task)
    
    return task


@collaboration_router.websocket("/ws/manus")
async def manus_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Manus connection"""
    service = get_collaboration_page_service()
    await service.handle_manus_connection(websocket)


@collaboration_router.websocket("/ws/cursor")
async def cursor_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Cursor connection"""
    service = get_collaboration_page_service()
    await service.handle_cursor_connection(websocket)


# React component structure for the page
COLLABORATION_PAGE_COMPONENT = """
// AI Collaboration Dashboard Page Component
// Located at: /settings/developer-tools/collaboration

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Divider
} from '@mui/material';
import { 
  Code as CodeIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuth } from '../../hooks/useAuth';

export const AICollaborationDashboard: React.FC = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [connections, setConnections] = useState({
    manus: false,
    cursor: false
  });
  
  // WebSocket connections for real-time updates
  const manusWs = useWebSocket('/api/settings/developer-tools/collaboration/ws/manus');
  const cursorWs = useWebSocket('/api/settings/developer-tools/collaboration/ws/cursor');
  
  useEffect(() => {
    // Fetch initial dashboard data
    fetchDashboardData();
    fetchTasks();
    
    // Set up WebSocket listeners
    if (manusWs) {
      manusWs.on('connection_established', () => {
        setConnections(prev => ({ ...prev, manus: true }));
      });
      
      manusWs.on('disconnect', () => {
        setConnections(prev => ({ ...prev, manus: false }));
      });
    }
    
    if (cursorWs) {
      cursorWs.on('connection_established', () => {
        setConnections(prev => ({ ...prev, cursor: true }));
      });
      
      cursorWs.on('disconnect', () => {
        setConnections(prev => ({ ...prev, cursor: false }));
      });
    }
  }, [manusWs, cursorWs]);
  
  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/settings/developer-tools/collaboration/');
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };
  
  const fetchTasks = async () => {
    try {
      const response = await fetch('/api/settings/developer-tools/collaboration/tasks');
      const data = await response.json();
      setTasks(data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };
  
  if (!dashboardData) {
    return <LinearProgress />;
  }
  
  return (
    <Box sx={{ p: 3 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          {dashboardData.page_title}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {dashboardData.page_description}
        </Typography>
      </Box>
      
      {/* Connection Status */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Manus Connection
              </Typography>
              <Chip
                icon={connections.manus ? <CheckIcon /> : <ErrorIcon />}
                label={connections.manus ? 'Connected' : 'Disconnected'}
                color={connections.manus ? 'success' : 'error'}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cursor Connection
              </Typography>
              <Chip
                icon={connections.cursor ? <CheckIcon /> : <ErrorIcon />}
                label={connections.cursor ? 'Connected' : 'Disconnected'}
                color={connections.cursor ? 'success' : 'error'}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Development Tasks */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">
              Development Tasks
            </Typography>
            <IconButton onClick={fetchTasks}>
              <RefreshIcon />
            </IconButton>
          </Box>
          
          <List>
            {tasks.map((task, index) => (
              <React.Fragment key={task.id}>
                <ListItem>
                  <ListItemText
                    primary={task.description || `${task.type} Task`}
                    secondary={`Status: ${task.status} | Agent: ${task.agent} | Created: ${new Date(task.created).toLocaleString()}`}
                  />
                  <Chip
                    size="small"
                    label={task.status}
                    color={task.status === 'completed' ? 'success' : 'default'}
                  />
                </ListItem>
                {index < tasks.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

// This component is rendered within the main Cherry AI admin interface
// It's not a standalone application but a page within the larger system
"""


def initialize_collaboration_page(main_service: AICollaborationService) -> None:
    """Initialize the collaboration page service"""
    global collaboration_page_service
    collaboration_page_service = CollaborationPageService(main_service)
    
    print("✅ AI Collaboration Dashboard page initialized")
    print("📍 Location: /settings/developer-tools/collaboration")
    print("🔒 Access: Admin-only with additional authentication")