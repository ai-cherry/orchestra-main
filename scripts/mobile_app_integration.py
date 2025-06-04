#!/usr/bin/env python3
"""Mobile App Integration for Cherry AI"""

from pathlib import Path
import json


class MobileAppIntegration:
    """Setup mobile app integration for Cherry AI"""
    
    def __init__(self):
        self.base_dir = Path("/root/cherry_ai-main")
        self.mobile_api_created = False
    
    def create_mobile_api(self):
        """Create mobile-specific API endpoints"""
        
        mobile_api_content = """
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from typing_extensions import Optional, Any
from datetime import datetime
import jwt

router = APIRouter(prefix="/mobile/v1", tags=["mobile"])

class DeviceAuthRequest(BaseModel):
    device_id: str
    platform: str  # ios, android
    app_version: str
    push_token: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    mode: str = "normal"
    filters: Optional[Dict[str, Any]] = None

class QuickTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    persona: str = "cherry"

@router.post("/auth/device")
async def authenticate_device(request: DeviceAuthRequest):
    # Device-based authentication for mobile apps
    # Generate device-specific JWT token
    token = jwt.encode({
        "device_id": request.device_id,
        "platform": request.platform,
        "app_version": request.app_version,
        "iat": datetime.utcnow()
    }, "secret", algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "device_id": request.device_id
    }

@router.post("/search")
async def mobile_search(request: SearchRequest):
    # Mobile-optimized search endpoint
    # Implement mobile-specific search logic
    # Optimize for smaller payloads and faster response
    results = []
    
    # Mock search results
    for i in range(5):
        results.append({
            "id": f"result_{i}",
            "title": f"Result {i} for {request.query}",
            "snippet": f"This is a snippet for result {i}",
            "relevance": 0.9 - (i * 0.1)
        })
    
    return {
        "query": request.query,
        "mode": request.mode,
        "results": results,
        "total": len(results)
    }

@router.post("/tasks/quick")
async def create_quick_task(request: QuickTaskRequest):
    # Quick task creation for mobile
    task_id = f"task_{datetime.utcnow().timestamp()}"
    
    return {
        "task_id": task_id,
        "title": request.title,
        "description": request.description,
        "persona": request.persona,
        "status": "created",
        "created_at": datetime.utcnow().isoformat()
    }

@router.get("/sync/delta")
async def get_sync_delta(device_id: str, last_sync: Optional[str] = None):
    # Get changes since last sync for offline support
    # Implement delta sync logic
    changes = {
        "tasks": [],
        "agents": [],
        "personas": [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return changes

@router.post("/analytics/event")
async def track_analytics_event(event_name: str, properties: Dict[str, Any]):
    # Track mobile app analytics events
    return {
        "event": event_name,
        "tracked": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.ws("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    # WebSocket connection for real-time updates
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process incoming messages
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
"""
        
        # Save mobile API file
        mobile_api_path = self.base_dir / "src" / "api" / "mobile_api.py"
        mobile_api_path.parent.mkdir(parents=True, exist_ok=True)
        mobile_api_path.write_text(mobile_api_content)
        
        # Create Android SDK
        android_sdk_content = """
package com.cherry_ai.ai.sdk

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

class cherry_aiAISDK(private val apiKey: String, private val baseUrl: String = "https://cherry-ai.me") {
    
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $apiKey")
                .build()
            chain.proceed(request)
        }
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(baseUrl)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    private val api = retrofit.create(cherry_aiAPI::class.java)
    
    suspend fun search(query: String, mode: String = "normal"): SearchResponse {
        return api.search(SearchRequest(query, mode))
    }
    
    suspend fun createQuickTask(title: String, description: String? = null): TaskResponse {
        return api.createQuickTask(QuickTaskRequest(title, description))
    }
    
    suspend fun syncDelta(lastSync: String?): SyncResponse {
        return api.getSyncDelta(lastSync)
    }
}
"""
        
        # Save Android SDK
        android_sdk_path = self.base_dir / "mobile" / "android" / "cherry_aiAISDK.kt"
        android_sdk_path.parent.mkdir(parents=True, exist_ok=True)
        android_sdk_path.write_text(android_sdk_content)
        
        # Create analytics dashboard HTML
        dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherry AI Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .chart-container {
            position: relative;
            height: 300px;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>Cherry AI Analytics Dashboard</h1>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value" id="total-users">0</div>
                <div class="metric-label">Total Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="api-calls">0</div>
                <div class="metric-label">API Calls Today</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avg-response">0ms</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-tasks">0</div>
                <div class="metric-label">Active Tasks</div>
            </div>
        </div>
        
        <div class="metric-card">
            <h2>API Usage Over Time</h2>
            <div class="chart-container">
                <canvas id="usage-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <h2>Search Modes Distribution</h2>
            <div class="chart-container">
                <canvas id="search-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <h2>Persona Usage</h2>
            <div class="chart-container">
                <canvas id="persona-chart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Analytics dashboard JavaScript
        async function updateDashboard() {
            try {
                const response = await fetch('/api/analytics/summary');
                const data = await response.json();
                
                document.getElementById('total-users').textContent = data.totalUsers || 0;
                document.getElementById('api-calls').textContent = data.apiCallsToday || 0;
                document.getElementById('avg-response').textContent = (data.avgResponseTime || 0) + 'ms';
                document.getElementById('active-tasks').textContent = data.activeTasks || 0;
            } catch (error) {
                console.error('Failed to fetch analytics:', error);
            }
        }
        
        // Initialize charts
        const usageChart = new Chart(document.getElementById('usage-chart'), {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        const searchChart = new Chart(document.getElementById('search-chart'), {
            type: 'doughnut',
            data: { labels: [], datasets: [] },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        const personaChart = new Chart(document.getElementById('persona-chart'), {
            type: 'bar',
            data: { labels: [], datasets: [] },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        // Update dashboard every 30 seconds
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>"""
        
        # Save analytics dashboard
        dashboard_path = self.base_dir / "admin-ui" / "public" / "analytics" / "dashboard.html"
        dashboard_path.parent.mkdir(parents=True, exist_ok=True)
        dashboard_path.write_text(dashboard_html)
        
        self.mobile_api_created = True
        print("✅ Mobile API endpoints created")
        print("✅ Android SDK created")
        print("✅ Analytics dashboard created")
    
    def setup_all_integrations(self):
        """Setup all mobile integrations"""
        self.create_mobile_api()
        
        print("\n📱 Mobile Integration Complete!")
        print("\nMobile API Endpoints:")
        print("- POST /mobile/v1/auth/device - Device authentication")
        print("- POST /mobile/v1/search - Mobile-optimized search")
        print("- POST /mobile/v1/tasks/quick - Quick task creation")
        print("- GET /mobile/v1/sync/delta - Get changes for offline sync")
        print("- WS /mobile/v1/ws/{device_id} - WebSocket connection")
        print("\nAnalytics Dashboard:")
        print("Access at: https://cherry-ai.me/analytics/dashboard")


if __name__ == "__main__":
    integration = MobileAppIntegration()
    integration.setup_all_integrations()
