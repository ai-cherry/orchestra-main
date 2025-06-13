from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_subscriptions: Dict[str, Set[str]] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        logger.info(f"User {user_id} connected")
    
    def disconnect(self, user_id: str):
        """Handle disconnection"""
        if user_id in self.active_connections:
            # Remove from all channel subscriptions
            if user_id in self.user_subscriptions:
                for channel in self.user_subscriptions[user_id]:
                    if channel in self.channel_subscribers:
                        self.channel_subscribers[channel].discard(user_id)
                del self.user_subscriptions[user_id]
            
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_channel(self, message: dict, channel: str):
        """Broadcast a message to all subscribers of a channel"""
        if channel in self.channel_subscribers:
            disconnected_users = []
            for user_id in self.channel_subscribers[channel].copy():
                try:
                    await self.send_personal_message(message, user_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {user_id}: {e}")
                    disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(user_id)
    
    def subscribe_user_to_channel(self, user_id: str, channel: str):
        """Subscribe a user to a channel"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].add(channel)
            
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(user_id)
            
            logger.info(f"User {user_id} subscribed to channel {channel}")
    
    def unsubscribe_user_from_channel(self, user_id: str, channel: str):
        """Unsubscribe a user from a channel"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel)
            
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(user_id)
            
        logger.info(f"User {user_id} unsubscribed from channel {channel}")

# Global connection manager
manager = ConnectionManager()

class WebSocketService:
    def __init__(self):
        self.manager = manager
    
    async def handle_connection(self, websocket: WebSocket, user_id: str):
        """Handle a new WebSocket connection"""
        await self.manager.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_text()
                await self.handle_message(data, user_id)
        except WebSocketDisconnect:
            self.manager.disconnect(user_id)
    
    async def handle_message(self, data: str, user_id: str):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "subscribe":
                channel = message.get("channel")
                if channel:
                    self.manager.subscribe_user_to_channel(user_id, channel)
                    await self.manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "channel": channel,
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
            
            elif message_type == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    self.manager.unsubscribe_user_from_channel(user_id, channel)
                    await self.manager.send_personal_message({
                        "type": "unsubscription_confirmed",
                        "channel": channel,
                        "timestamp": datetime.now().isoformat()
                    }, user_id)
            
            elif message_type == "ping":
                await self.manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, user_id)
            
            elif message_type == "get_status":
                await self.send_connection_status(user_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from user {user_id}: {data}")
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
    
    async def send_connection_status(self, user_id: str):
        """Send connection status to user"""
        subscriptions = list(self.manager.user_subscriptions.get(user_id, set()))
        await self.manager.send_personal_message({
            "type": "status",
            "connected": True,
            "subscriptions": subscriptions,
            "timestamp": datetime.now().isoformat()
        }, user_id)
    
    async def broadcast_file_upload_progress(self, file_id: str, progress: float, status: str, 
                                           filename: str = None, speed: str = None, eta: str = None):
        """Broadcast file upload progress to subscribers"""
        message = {
            "type": "upload_progress",
            "file_id": file_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if filename:
            message["filename"] = filename
        if speed:
            message["speed"] = speed
        if eta:
            message["eta"] = eta
        
        await self.manager.broadcast_to_channel(message, "file_uploads")
    
    async def broadcast_file_processing_update(self, file_id: str, stage: str, progress: float, 
                                             details: str = None):
        """Broadcast file processing updates"""
        message = {
            "type": "processing_update",
            "file_id": file_id,
            "stage": stage,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            message["details"] = details
        
        await self.manager.broadcast_to_channel(message, "file_processing")
    
    async def broadcast_system_alert(self, alert_type: str, title: str, message: str, 
                                   severity: str = "info"):
        """Broadcast system alerts"""
        alert_message = {
            "type": "system_alert",
            "alert_type": alert_type,
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.broadcast_to_channel(alert_message, "system_alerts")
    
    async def send_persona_update(self, user_id: str, persona: str, action: str):
        """Send persona-specific updates"""
        message = {
            "type": "persona_update",
            "persona": persona,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.manager.send_personal_message(message, user_id)
    
    async def broadcast_agent_status(self, agent_id: str, status: str, details: dict = None):
        """Broadcast agent status updates"""
        message = {
            "type": "agent_status",
            "agent_id": agent_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            message.update(details)
        
        await self.manager.broadcast_to_channel(message, "agent_updates")
    
    def get_connection_stats(self) -> dict:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.manager.active_connections),
            "total_subscriptions": sum(len(subs) for subs in self.manager.user_subscriptions.values()),
            "channels": list(self.manager.channel_subscribers.keys()),
            "channel_subscriber_count": {
                channel: len(subscribers) 
                for channel, subscribers in self.manager.channel_subscribers.items()
            }
        }

# Global WebSocket service instance
websocket_service = WebSocketService()

# Background task to send periodic heartbeats
async def heartbeat_task():
    """Send periodic heartbeat to all connected clients"""
    while True:
        try:
            if manager.active_connections:
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": len(manager.active_connections)
                }
                
                # Send to all connected clients
                for user_id in list(manager.active_connections.keys()):
                    await manager.send_personal_message(heartbeat_message, user_id)
            
            # Wait 30 seconds before next heartbeat
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")
            await asyncio.sleep(30) 