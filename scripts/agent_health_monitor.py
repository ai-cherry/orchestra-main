#!/usr/bin/env python3
"""
"""
    """Health metric data point"""
        """Check if metric is within healthy range"""
    """Monitors health of AI agents"""
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "response_time": 5.0,
            "error_rate": 0.1,
            "queue_depth": 100
        }
        self.monitoring_interval = 10  # seconds
    
    async def collect_agent_metrics(self, agent_id: str) -> Dict[str, float]:
        """Collect metrics for a specific agent"""
            "cpu_usage": random.uniform(20, 90),
            "memory_usage": random.uniform(30, 95),
            "response_time": random.uniform(0.1, 8.0),
            "error_rate": random.uniform(0, 0.2),
            "queue_depth": random.randint(0, 150)
        }
        
        return metrics
    
    async def monitor_agent(self, agent_id: str):
        """Monitor a single agent"""
        """Create an alert for unhealthy metric"""
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "metric": metric.metric_name,
            "value": metric.value,
            "threshold": metric.threshold,
            "severity": self._calculate_severity(metric)
        }
        
        self.alerts.append(alert)
        logger.warning(f"Health alert: {alert}")
        
        # TODO: Send notifications (email, Slack, etc.)
    
    def _calculate_severity(self, metric: HealthMetric) -> str:
        """Calculate alert severity"""
            return "info"
        
        ratio = metric.value / metric.threshold
        if ratio > 1.5:
            return "critical"
        elif ratio > 1.2:
            return "high"
        elif ratio > 1.0:
            return "medium"
        else:
            return "low"
    
    async def analyze_trends(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze health trends for an agent"""
            return {"error": "No metrics found for agent"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history[agent_id]
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No recent metrics found"}
        
        # Group by metric name
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append(metric.value)
        
        # Calculate statistics
        trends = {}
        for metric_name, values in metrics_by_name.items():
            trends[metric_name] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "trend": self._calculate_trend(values),
                "health_score": self._calculate_health_score(values, metric_name)
            }
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
            return "stable"
        
        # Simple linear trend
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        change = (second_half - first_half) / first_half
        
        if change > 0.1:
            return "increasing"
        elif change < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_health_score(self, values: List[float], metric_name: str) -> float:
        """Calculate health score (0-100)"""
        """Get data for health dashboard"""
                    "value": metric.value,
                    "healthy": metric.is_healthy
                }
            
            agent_health[agent_id] = {
                "latest_metrics": latest_metrics,
                "overall_health": self._calculate_overall_health(agent_id)
            }
        
        return {
            "agents": agent_health,
            "alerts": self.alerts[-10:],  # Last 10 alerts
            "summary": {
                "total_agents": len(self.metrics_history),
                "healthy_agents": sum(
                    1 for agent_id in self.metrics_history
                    if self._calculate_overall_health(agent_id) > 80
                ),
                "total_alerts": len(self.alerts)
            }
        }
    
    def _calculate_overall_health(self, agent_id: str) -> float:
        """Calculate overall health score for an agent"""
if __name__ == "__main__":
    async def main():
        monitor = AgentHealthMonitor()
        
        # Simulate monitoring multiple agents
        agent_ids = ["agent-1", "agent-2", "agent-3"]
        
        for _ in range(5):
            for agent_id in agent_ids:
                await monitor.monitor_agent(agent_id)
            await asyncio.sleep(2)
        
        # Analyze trends
        trends = await monitor.analyze_trends("agent-1")
        print(f"Trends: {json.dumps(trends, indent=2)}")
        
        # Get dashboard data
        dashboard = monitor.get_dashboard_data()
        print(f"Dashboard: {json.dumps(dashboard, indent=2)}")
    
    asyncio.run(main())
