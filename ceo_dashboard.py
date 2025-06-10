#!/usr/bin/env python3
"""
PayReady CEO Business Intelligence Dashboard
Live web dashboard with real-time metrics, Zapier integration, and Sophia AI insights
"""

from flask import Flask, render_template, jsonify, request
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
import sqlite3
import os
from threading import Thread
import requests
import time

# Dashboard Configuration
app = Flask(__name__)
app.secret_key = "payready_ceo_dashboard_2025"

# API Endpoints
ZAPIER_MCP_URL = "http://localhost:8001"
SOPHIA_AI_URL = "http://localhost:8014"
ZAPIER_API_KEY = "zap_dev_12345_abcdef_orchestra_ai_cursor"

# Dashboard Database
DB_PATH = "ceo_dashboard.db"

def init_dashboard_db():
    """Initialize SQLite database for dashboard metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for dashboard data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ceo_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metric_type TEXT NOT NULL,
            metric_value REAL,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deal_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT UNIQUE,
            deal_name TEXT,
            health_score INTEGER,
            risk_factors TEXT,
            client_name TEXT,
            amount REAL,
            stage TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitive_intel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor TEXT,
            mention_context TEXT,
            threat_level TEXT,
            call_id TEXT,
            mentioned_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_coaching (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rep_name TEXT,
            call_id TEXT,
            question_quality_score INTEGER,
            objection_handling_score INTEGER,
            improvement_areas TEXT,
            strengths TEXT,
            call_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Insert sample data for demonstration
    insert_sample_data()

def insert_sample_data():
    """Insert sample data for CEO dashboard demonstration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sample deal health data
    sample_deals = [
        ("deal_001", "Acme Corp Payment Integration", 85, "Long sales cycle, Multiple decision makers", "Acme Corporation", 150000, "Negotiation"),
        ("deal_002", "TechStart Billing Solution", 92, "None identified", "TechStart Inc", 75000, "Proposal"),
        ("deal_003", "Enterprise Corp Platform", 65, "Budget concerns, Competitive pressure", "Enterprise Corp", 300000, "Discovery"),
        ("deal_004", "StartupXYZ Integration", 78, "Technical complexity", "StartupXYZ", 45000, "Demo"),
    ]
    
    for deal in sample_deals:
        cursor.execute('''
            INSERT OR REPLACE INTO deal_health 
            (deal_id, deal_name, health_score, risk_factors, client_name, amount, stage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', deal)
    
    # Sample competitive intelligence
    competitive_data = [
        ("Stripe", "Client mentioned considering Stripe for processing", "Medium", "gong_call_001"),
        ("Square", "Positive comparison to Square's ease of use", "Low", "gong_call_002"),
        ("PayPal", "Client expressed concerns about PayPal fees", "Low", "gong_call_003"),
    ]
    
    for comp in competitive_data:
        cursor.execute('''
            INSERT OR REPLACE INTO competitive_intel 
            (competitor, mention_context, threat_level, call_id)
            VALUES (?, ?, ?, ?)
        ''', comp)
    
    # Sample sales coaching data
    coaching_data = [
        ("Sarah Johnson", "gong_call_001", 85, 78, "Discovery questions, Closing techniques", "Product knowledge, Rapport building"),
        ("Mike Chen", "gong_call_002", 92, 88, "Objection handling", "Technical expertise, Value proposition"),
        ("Lisa Rodriguez", "gong_call_003", 76, 82, "Talk time ratio, Follow-up", "Client engagement, Problem identification"),
    ]
    
    for coach in coaching_data:
        cursor.execute('''
            INSERT OR REPLACE INTO sales_coaching 
            (rep_name, call_id, question_quality_score, objection_handling_score, improvement_areas, strengths)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', coach)
    
    # Sample CEO metrics
    metrics_data = [
        ("total_revenue_pipeline", 570000),
        ("average_deal_health", 80),
        ("at_risk_deals", 1),
        ("competitive_threats", 2),
        ("team_performance", 85),
    ]
    
    for metric_type, value in metrics_data:
        cursor.execute('''
            INSERT INTO ceo_metrics (metric_type, metric_value, metadata)
            VALUES (?, ?, ?)
        ''', (metric_type, value, "Sample data for dashboard demo"))
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    """Main CEO dashboard page"""
    return render_template('ceo_dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Get current CEO metrics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get latest metrics
    metrics = {}
    
    # Total pipeline value
    cursor.execute('SELECT SUM(amount) FROM deal_health')
    total_pipeline = cursor.fetchone()[0] or 0
    
    # Average deal health
    cursor.execute('SELECT AVG(health_score) FROM deal_health')
    avg_health = cursor.fetchone()[0] or 0
    
    # At-risk deals (health < 70)
    cursor.execute('SELECT COUNT(*) FROM deal_health WHERE health_score < 70')
    at_risk = cursor.fetchone()[0] or 0
    
    # Competitive threats
    cursor.execute('SELECT COUNT(*) FROM competitive_intel WHERE threat_level IN ("Medium", "High")')
    threats = cursor.fetchone()[0] or 0
    
    # Team performance average
    cursor.execute('SELECT AVG((question_quality_score + objection_handling_score) / 2) FROM sales_coaching')
    team_performance = cursor.fetchone()[0] or 0
    
    # Total deals
    cursor.execute('SELECT COUNT(*) FROM deal_health')
    total_deals = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        "total_pipeline": total_pipeline,
        "average_deal_health": round(avg_health, 1),
        "at_risk_deals": at_risk,
        "competitive_threats": threats,
        "team_performance": round(team_performance, 1),
        "total_deals": total_deals,
        "last_updated": datetime.now().isoformat()
    })

@app.route('/api/deals')
def get_deals():
    """Get deal health data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT deal_id, deal_name, health_score, risk_factors, client_name, amount, stage, last_updated
        FROM deal_health
        ORDER BY amount DESC
    ''')
    
    deals = []
    for row in cursor.fetchall():
        deals.append({
            "deal_id": row[0],
            "deal_name": row[1],
            "health_score": row[2],
            "risk_factors": row[3].split(", ") if row[3] else [],
            "client_name": row[4],
            "amount": row[5],
            "stage": row[6],
            "last_updated": row[7]
        })
    
    conn.close()
    return jsonify(deals)

@app.route('/api/competitive')
def get_competitive_intel():
    """Get competitive intelligence data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT competitor, mention_context, threat_level, call_id, mentioned_date
        FROM competitive_intel
        ORDER BY mentioned_date DESC
    ''')
    
    competitive = []
    for row in cursor.fetchall():
        competitive.append({
            "competitor": row[0],
            "context": row[1],
            "threat_level": row[2],
            "call_id": row[3],
            "date": row[4]
        })
    
    conn.close()
    return jsonify(competitive)

@app.route('/api/coaching')
def get_coaching_insights():
    """Get sales coaching insights"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT rep_name, call_id, question_quality_score, objection_handling_score, 
               improvement_areas, strengths, call_date
        FROM sales_coaching
        ORDER BY call_date DESC
    ''')
    
    coaching = []
    for row in cursor.fetchall():
        coaching.append({
            "rep_name": row[0],
            "call_id": row[1],
            "question_quality": row[2],
            "objection_handling": row[3],
            "improvement_areas": row[4].split(", ") if row[4] else [],
            "strengths": row[5].split(", ") if row[5] else [],
            "call_date": row[6]
        })
    
    conn.close()
    return jsonify(coaching)

@app.route('/api/zapier/trigger', methods=['POST'])
def zapier_trigger():
    """Handle incoming Zapier webhook triggers"""
    data = request.get_json()
    
    # Process different types of triggers
    trigger_type = data.get('trigger_type', 'unknown')
    
    if trigger_type == 'gong_call_completed':
        process_gong_call(data)
    elif trigger_type == 'salesforce_opportunity_updated':
        process_salesforce_update(data)
    elif trigger_type == 'deal_health_alert':
        process_deal_alert(data)
    
    return jsonify({"status": "processed", "trigger_type": trigger_type})

def process_gong_call(data):
    """Process Gong call completion trigger"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract data from Gong webhook
    call_id = data.get('call_id', f"call_{int(time.time())}")
    rep_name = data.get('rep_name', 'Unknown Rep')
    
    # Simulate AI analysis results
    question_quality = data.get('question_quality_score', 80)
    objection_handling = data.get('objection_handling_score', 75)
    
    # Insert coaching insight
    cursor.execute('''
        INSERT OR REPLACE INTO sales_coaching 
        (rep_name, call_id, question_quality_score, objection_handling_score, improvement_areas, strengths)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (rep_name, call_id, question_quality, objection_handling, 
          "Follow-up timing", "Product knowledge"))
    
    conn.commit()
    conn.close()

def process_salesforce_update(data):
    """Process Salesforce opportunity update"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    deal_id = data.get('opportunity_id', f"deal_{int(time.time())}")
    deal_name = data.get('name', 'Unknown Deal')
    health_score = data.get('health_score', 75)
    
    cursor.execute('''
        INSERT OR REPLACE INTO deal_health 
        (deal_id, deal_name, health_score, risk_factors, client_name, amount, stage)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (deal_id, deal_name, health_score, "Auto-updated", 
          data.get('client_name', 'Unknown'), data.get('amount', 0), 
          data.get('stage', 'Unknown')))
    
    conn.commit()
    conn.close()

@app.route('/api/sophia/analyze', methods=['POST'])
def sophia_analysis():
    """Trigger Sophia AI analysis"""
    data = request.get_json()
    analysis_type = data.get('type', 'general')
    
    # Simulate Sophia AI response
    if analysis_type == 'deal_health':
        return jsonify({
            "analysis": "Based on recent call patterns and client engagement, the deal shows strong potential with minor risk factors around decision timeline.",
            "recommendations": [
                "Schedule executive demo within 2 weeks",
                "Prepare ROI analysis with specific metrics",
                "Address technical questions proactively"
            ],
            "confidence": 85,
            "generated_by": "Sophia AI",
            "timestamp": datetime.now().isoformat()
        })
    
    return jsonify({
        "analysis": f"Sophia AI analysis for {analysis_type} completed successfully",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/test/zapier')
def test_zapier_integration():
    """Test Zapier MCP integration"""
    try:
        # Test health endpoint
        response = requests.get(f"{ZAPIER_MCP_URL}/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            return jsonify({
                "status": "connected",
                "zapier_mcp": health_data,
                "uptime": health_data.get('uptime', 0),
                "capabilities": health_data.get('capabilities', [])
            })
        else:
            return jsonify({"status": "error", "message": "Zapier MCP not responding"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Initialize database
    init_dashboard_db()
    
    print("🚀 Starting PayReady CEO Dashboard...")
    print("=" * 50)
    print("📊 Dashboard URL: http://localhost:5000")
    print("🔗 API Endpoints:")
    print("   • Metrics: http://localhost:5000/api/metrics")
    print("   • Deals: http://localhost:5000/api/deals")
    print("   • Competitive: http://localhost:5000/api/competitive")
    print("   • Coaching: http://localhost:5000/api/coaching")
    print("   • Zapier Test: http://localhost:5000/api/test/zapier")
    print("🎯 Zapier Webhook: http://localhost:5000/api/zapier/trigger")
    print("=" * 50)
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 