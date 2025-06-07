#!/usr/bin/env python3
"""
Cherry AI Usage Analytics and Monitoring System
Tracks AI interaction patterns and provides optimization insights
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cherry-ai-analytics")

@dataclass
class AIInteraction:
    """Represents a single AI interaction"""
    timestamp: float
    tool_name: str
    model_used: str
    response_time: float
    token_count: int
    success: bool
    context_size: int
    user_satisfaction: Optional[int] = None  # 1-5 rating
    error_message: Optional[str] = None

@dataclass
class UsageMetrics:
    """Aggregated usage metrics"""
    total_interactions: int
    avg_response_time: float
    success_rate: float
    most_used_tools: List[str]
    peak_usage_hours: List[int]
    model_performance: Dict[str, Dict[str, float]]

class CherryAIAnalytics:
    """Analytics and monitoring system for Cherry AI interactions"""
    
    def __init__(self, db_path: str = "cherry_ai_analytics.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for analytics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                tool_name TEXT NOT NULL,
                model_used TEXT NOT NULL,
                response_time REAL NOT NULL,
                token_count INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                context_size INTEGER NOT NULL,
                user_satisfaction INTEGER,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL,
                command_sequence TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                avg_completion_time REAL,
                success_rate REAL,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_type TEXT NOT NULL,
                description TEXT NOT NULL,
                impact_score INTEGER NOT NULL,
                implementation_effort INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                implemented BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")
    
    def log_interaction(self, interaction: AIInteraction):
        """Log a single AI interaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_interactions 
            (timestamp, tool_name, model_used, response_time, token_count, 
             success, context_size, user_satisfaction, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.timestamp,
            interaction.tool_name,
            interaction.model_used,
            interaction.response_time,
            interaction.token_count,
            interaction.success,
            interaction.context_size,
            interaction.user_satisfaction,
            interaction.error_message
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Logged interaction: {interaction.tool_name} - {interaction.response_time:.2f}s")
    
    def get_usage_metrics(self, days: int = 7) -> UsageMetrics:
        """Get aggregated usage metrics for the specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_timestamp = time.time() - (days * 24 * 3600)
        
        # Total interactions
        cursor.execute("""
            SELECT COUNT(*) FROM ai_interactions 
            WHERE timestamp > ?
        """, (since_timestamp,))
        total_interactions = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time) FROM ai_interactions 
            WHERE timestamp > ? AND success = 1
        """, (since_timestamp,))
        avg_response_time = cursor.fetchone()[0] or 0.0
        
        # Success rate
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) 
            FROM ai_interactions 
            WHERE timestamp > ?
        """, (since_timestamp,))
        success_rate = cursor.fetchone()[0] or 0.0
        
        # Most used tools
        cursor.execute("""
            SELECT tool_name, COUNT(*) as usage_count 
            FROM ai_interactions 
            WHERE timestamp > ?
            GROUP BY tool_name 
            ORDER BY usage_count DESC 
            LIMIT 5
        """, (since_timestamp,))
        most_used_tools = [row[0] for row in cursor.fetchall()]
        
        # Peak usage hours
        cursor.execute("""
            SELECT strftime('%H', datetime(timestamp, 'unixepoch')) as hour, COUNT(*) as count
            FROM ai_interactions 
            WHERE timestamp > ?
            GROUP BY hour 
            ORDER BY count DESC 
            LIMIT 3
        """, (since_timestamp,))
        peak_usage_hours = [int(row[0]) for row in cursor.fetchall()]
        
        # Model performance
        cursor.execute("""
            SELECT 
                model_used,
                AVG(response_time) as avg_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                AVG(CASE WHEN user_satisfaction IS NOT NULL THEN user_satisfaction ELSE 0 END) as satisfaction
            FROM ai_interactions 
            WHERE timestamp > ?
            GROUP BY model_used
        """, (since_timestamp,))
        
        model_performance = {}
        for row in cursor.fetchall():
            model_performance[row[0]] = {
                "avg_response_time": row[1],
                "success_rate": row[2],
                "avg_satisfaction": row[3]
            }
        
        conn.close()
        
        return UsageMetrics(
            total_interactions=total_interactions,
            avg_response_time=avg_response_time,
            success_rate=success_rate,
            most_used_tools=most_used_tools,
            peak_usage_hours=peak_usage_hours,
            model_performance=model_performance
        )
    
    def detect_workflow_patterns(self) -> List[Dict[str, Any]]:
        """Detect common workflow patterns from interaction history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent interactions grouped by time windows
        cursor.execute("""
            SELECT tool_name, timestamp 
            FROM ai_interactions 
            WHERE timestamp > ? 
            ORDER BY timestamp
        """, (time.time() - (7 * 24 * 3600),))
        
        interactions = cursor.fetchall()
        patterns = []
        
        # Simple pattern detection: sequences of 2-4 tools within 10 minutes
        for i in range(len(interactions) - 1):
            sequence = [interactions[i][0]]
            start_time = interactions[i][1]
            
            for j in range(i + 1, min(i + 4, len(interactions))):
                if interactions[j][1] - start_time <= 600:  # 10 minutes
                    sequence.append(interactions[j][0])
                else:
                    break
            
            if len(sequence) >= 2:
                pattern_name = " → ".join(sequence)
                patterns.append({
                    "pattern": pattern_name,
                    "sequence": sequence,
                    "frequency": 1,
                    "duration": interactions[i + len(sequence) - 1][1] - start_time
                })
        
        # Aggregate similar patterns
        pattern_counts = {}
        for pattern in patterns:
            key = pattern["pattern"]
            if key in pattern_counts:
                pattern_counts[key]["frequency"] += 1
                pattern_counts[key]["avg_duration"] = (
                    pattern_counts[key]["avg_duration"] + pattern["duration"]
                ) / 2
            else:
                pattern_counts[key] = {
                    "pattern": key,
                    "frequency": 1,
                    "avg_duration": pattern["duration"]
                }
        
        # Return top patterns
        sorted_patterns = sorted(
            pattern_counts.values(), 
            key=lambda x: x["frequency"], 
            reverse=True
        )
        
        conn.close()
        return sorted_patterns[:10]
    
    def generate_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on usage patterns"""
        metrics = self.get_usage_metrics(days=7)
        suggestions = []
        
        # Slow response time suggestion
        if metrics.avg_response_time > 5.0:
            suggestions.append({
                "type": "performance",
                "title": "Optimize Response Times",
                "description": f"Average response time is {metrics.avg_response_time:.1f}s. Consider caching frequently accessed data or optimizing MCP server performance.",
                "impact_score": 8,
                "implementation_effort": 6
            })
        
        # Low success rate suggestion
        if metrics.success_rate < 90.0:
            suggestions.append({
                "type": "reliability",
                "title": "Improve Success Rate",
                "description": f"Success rate is {metrics.success_rate:.1f}%. Review error patterns and improve error handling.",
                "impact_score": 9,
                "implementation_effort": 7
            })
        
        # Underutilized tools suggestion
        if len(metrics.most_used_tools) < 3:
            suggestions.append({
                "type": "utilization",
                "title": "Expand Tool Usage",
                "description": "Only a few tools are being used frequently. Consider creating workflows that leverage more MCP server capabilities.",
                "impact_score": 6,
                "implementation_effort": 4
            })
        
        # Model optimization suggestion
        best_model = None
        best_score = 0
        for model, perf in metrics.model_performance.items():
            score = (perf["success_rate"] * 0.4) + ((10 - perf["avg_response_time"]) * 0.3) + (perf["avg_satisfaction"] * 0.3)
            if score > best_score:
                best_score = score
                best_model = model
        
        if best_model and len(metrics.model_performance) > 1:
            suggestions.append({
                "type": "model_optimization",
                "title": f"Optimize Model Usage",
                "description": f"{best_model} shows the best performance. Consider using it for more tasks.",
                "impact_score": 7,
                "implementation_effort": 3
            })
        
        return suggestions
    
    def export_analytics_report(self, output_path: str = "cherry_ai_analytics_report.json"):
        """Export comprehensive analytics report"""
        metrics = self.get_usage_metrics(days=30)
        patterns = self.detect_workflow_patterns()
        suggestions = self.generate_optimization_suggestions()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_days": 30,
            "usage_metrics": asdict(metrics),
            "workflow_patterns": patterns,
            "optimization_suggestions": suggestions,
            "summary": {
                "total_interactions": metrics.total_interactions,
                "daily_average": metrics.total_interactions / 30,
                "performance_score": min(100, (metrics.success_rate + (10 - metrics.avg_response_time) * 10)),
                "top_workflow": patterns[0]["pattern"] if patterns else "No patterns detected"
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Analytics report exported to {output_path}")
        return report

def main():
    """Main function for testing analytics system"""
    analytics = CherryAIAnalytics()
    
    # Example usage: log some test interactions
    test_interactions = [
        AIInteraction(
            timestamp=time.time() - 3600,
            tool_name="get_smart_suggestions",
            model_used="claude-3-sonnet",
            response_time=2.5,
            token_count=1500,
            success=True,
            context_size=5000,
            user_satisfaction=4
        ),
        AIInteraction(
            timestamp=time.time() - 3500,
            tool_name="search_codebase",
            model_used="claude-3-sonnet",
            response_time=1.8,
            token_count=800,
            success=True,
            context_size=3000,
            user_satisfaction=5
        )
    ]
    
    for interaction in test_interactions:
        analytics.log_interaction(interaction)
    
    # Generate and display metrics
    metrics = analytics.get_usage_metrics(days=7)
    print(f"Usage Metrics (7 days):")
    print(f"  Total interactions: {metrics.total_interactions}")
    print(f"  Average response time: {metrics.avg_response_time:.2f}s")
    print(f"  Success rate: {metrics.success_rate:.1f}%")
    print(f"  Most used tools: {', '.join(metrics.most_used_tools)}")
    
    # Export full report
    report = analytics.export_analytics_report()
    print(f"\nFull analytics report exported with {len(report['optimization_suggestions'])} suggestions")

if __name__ == "__main__":
    main()

