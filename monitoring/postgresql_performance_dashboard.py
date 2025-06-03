#!/usr/bin/env python3
"""
"""
    """Collects and aggregates performance metrics."""
        """Collect current performance metrics."""
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "connection_pool": {
                "total": pool_stats["total_connections"],
                "used": pool_stats["used_connections"],
                "idle": pool_stats["idle_connections"],
                "utilization": (
                    (pool_stats["used_connections"] / pool_stats["total_connections"] * 100)
                    if pool_stats["total_connections"] > 0
                    else 0
                ),
            },
            "cache": {
                "hit_rate": perf_metrics["cache"]["hit_rate"],
                "total_hits": perf_metrics["cache"]["hits"],
                "total_misses": perf_metrics["cache"]["misses"],
                "size": db_health.get("cache_stats", {}).get("size", 0),
            },
            "operations": {
                "total": perf_metrics["operations"]["total"],
                "by_type": perf_metrics["operations"]["by_type"],
                "avg_duration_ms": perf_metrics["operations"]["avg_duration_ms"],
            },
            "health": {
                "postgresql": manager_health["status"],
                "unified_pg": pg_health["status"],
                "unified_db": db_health["status"],
                "overall": (
                    "healthy"
                    if all(s["status"] == "healthy" for s in [manager_health, pg_health, db_health])
                    else "degraded"
                ),
            },
            "database": {
                "size_mb": manager_health["database"].get("size_mb", 0),
                "connections": manager_health["database"].get("active_connections", 0),
                "version": manager_health["database"].get("version", "unknown"),
            },
        }

        # Store in history
        self.metrics_history.append(metrics)

        return metrics

    async def get_historical_metrics(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get historical metrics for the specified time range."""
        """Get query performance statistics."""
            """
        """
        return {"slow_queries": [dict(q) for q in slow_queries], "query_stats": dict(self.query_times)}

    async def get_table_stats(self) -> List[Dict[str, Any]]:
        """Get table size and performance statistics."""
            """
        """
app = FastAPI(title="PostgreSQL Performance Dashboard")
monitor = PerformanceMonitor()

# WebSocket connections
connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics."""
        print(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/")
async def dashboard():
    """Serve the dashboard HTML."""
        content="""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            height: 400px;
        }
        .status-healthy {
            color: #10b981;
        }
        .status-degraded {
            color: #f59e0b;
        }
        .status-unhealthy {
            color: #ef4444;
        }
        .table-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        th {
            font-weight: 600;
            color: #374151;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #3b82f6;
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>PostgreSQL Performance Dashboard</h1>
            <p>Real-time monitoring of the unified PostgreSQL architecture</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Connection Pool Utilization</div>
                <div class="metric-value" id="pool-utilization">0%</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="pool-progress" style="width: 0%"></div>
                </div>
                <div class="metric-label" id="pool-details">0/0 connections</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Cache Hit Rate</div>
                <div class="metric-value" id="cache-hit-rate">0%</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cache-progress" style="width: 0%"></div>
                </div>
                <div class="metric-label" id="cache-details">0 hits, 0 misses</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Operations/sec</div>
                <div class="metric-value" id="ops-per-sec">0</div>
                <div class="metric-label" id="ops-details">0 total operations</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">System Health</div>
                <div class="metric-value" id="system-health" class="status-healthy">Healthy</div>
                <div class="metric-label" id="health-details">All systems operational</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="performance-chart"></canvas>
        </div>
        
        <div class="chart-container">
            <canvas id="operations-chart"></canvas>
        </div>
        
        <div class="table-container">
            <h3>Table Statistics</h3>
            <table id="table-stats">
                <thead>
                    <tr>
                        <th>Schema</th>
                        <th>Table</th>
                        <th>Size</th>
                        <th>Live Rows</th>
                        <th>Dead Rows</th>
                        <th>Last Vacuum</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Initialize charts
        const performanceCtx = document.getElementById('performance-chart').getContext('2d');
        const performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Connection Pool %',
                        data: [],
                        borderColor: '#3b82f6',
                        tension: 0.1
                    },
                    {
                        label: 'Cache Hit Rate %',
                        data: [],
                        borderColor: '#10b981',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        const operationsCtx = document.getElementById('operations-chart').getContext('2d');
        const operationsChart = new Chart(operationsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Operations by Type',
                    data: [],
                    backgroundColor: [
                        '#3b82f6',
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#8b5cf6',
                        '#ec4899'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
        
        // WebSocket connection
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        let metricsHistory = [];
        let lastOpsCount = 0;
        let lastTimestamp = Date.now();
        
        ws.onmessage = function(event) {
            const metrics = JSON.parse(event.data);
            metricsHistory.push(metrics);
            
            // Keep only last 60 data points
            if (metricsHistory.length > 60) {
                metricsHistory.shift();
            }
            
            // Update metrics cards
            document.getElementById('pool-utilization').textContent = 
                metrics.connection_pool.utilization.toFixed(1) + '%';
            document.getElementById('pool-progress').style.width = 
                metrics.connection_pool.utilization + '%';
            document.getElementById('pool-details').textContent = 
                `${metrics.connection_pool.used}/${metrics.connection_pool.total} connections`;
            
            document.getElementById('cache-hit-rate').textContent = 
                (metrics.cache.hit_rate * 100).toFixed(1) + '%';
            document.getElementById('cache-progress').style.width = 
                (metrics.cache.hit_rate * 100) + '%';
            document.getElementById('cache-details').textContent = 
                `${metrics.cache.total_hits} hits, ${metrics.cache.total_misses} misses`;
            
            // Calculate ops/sec
            const currentOps = metrics.operations.total;
            const currentTime = Date.now();
            const timeDiff = (currentTime - lastTimestamp) / 1000;
            const opsPerSec = timeDiff > 0 ? (currentOps - lastOpsCount) / timeDiff : 0;
            
            document.getElementById('ops-per-sec').textContent = opsPerSec.toFixed(1);
            document.getElementById('ops-details').textContent = 
                `${metrics.operations.total} total operations`;
            
            lastOpsCount = currentOps;
            lastTimestamp = currentTime;
            
            // Update health status
            const healthElement = document.getElementById('system-health');
            healthElement.textContent = metrics.health.overall.charAt(0).toUpperCase() + 
                metrics.health.overall.slice(1);
            healthElement.className = 'metric-value status-' + metrics.health.overall;
            
            // Update performance chart
            const labels = metricsHistory.map(m => 
                new Date(m.timestamp).toLocaleTimeString()
            );
            performanceChart.data.labels = labels;
            performanceChart.data.datasets[0].data = metricsHistory.map(m => 
                m.connection_pool.utilization
            );
            performanceChart.data.datasets[1].data = metricsHistory.map(m => 
                m.cache.hit_rate * 100
            );
            performanceChart.update();
            
            // Update operations chart
            const opsData = metrics.operations.by_type;
            operationsChart.data.labels = Object.keys(opsData);
            operationsChart.data.datasets[0].data = Object.values(opsData);
            operationsChart.update();
        };
        
        // Fetch table stats periodically
        async function updateTableStats() {
            try {
                const response = await fetch('/api/table-stats');
                const stats = await response.json();
                
                const tbody = document.querySelector('#table-stats tbody');
                tbody.innerHTML = stats.map(stat => `
                    <tr>
                        <td>${stat.schemaname}</td>
                        <td>${stat.tablename}</td>
                        <td>${stat.total_size}</td>
                        <td>${stat.live_rows.toLocaleString()}</td>
                        <td>${stat.dead_rows.toLocaleString()}</td>
                        <td>${stat.last_vacuum ? new Date(stat.last_vacuum).toLocaleString() : 'Never'}</td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Failed to fetch table stats:', error);
            }
        }
        
        // Update table stats every 30 seconds
        setInterval(updateTableStats, 30000);
        updateTableStats();
    </script>
</body>
</html>
    """
@app.get("/api/metrics/current")
async def get_current_metrics():
    """Get current performance metrics."""
@app.get("/api/metrics/history")
async def get_metrics_history(minutes: int = 5):
    """Get historical metrics."""
@app.get("/api/query-performance")
async def get_query_performance():
    """Get query performance statistics."""
@app.get("/api/table-stats")
async def get_table_stats():
    """Get table statistics."""
    """Background task to collect metrics periodically."""
            print(f"Error collecting metrics: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
if __name__ == "__main__":
    # Run the dashboard
    uvicorn.run("postgresql_performance_dashboard:app", host="0.0.0.0", port=8000, reload=True)
