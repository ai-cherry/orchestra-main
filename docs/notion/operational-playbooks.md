# Operational Playbooks - Notion Integration

## 📚 **Overview**

This guide provides comprehensive operational procedures for managing the Orchestra AI Notion workspace, interpreting metrics, troubleshooting issues, and maintaining optimal performance.

## 🎯 **Daily Operations**

### **Morning Startup Checklist**
```bash
# 1. Verify Notion API connectivity
python3 -c "from config.notion_config import get_config; print('✅ Config loaded')"

# 2. Check MCP server status
python3 mcp_unified_server.py --health-check

# 3. Validate database access
python3 -c "
from config.notion_config import validate_database_access, get_config
results = validate_database_access(get_config())
print(f'Accessible databases: {sum(results.values())}/{len(results)}')
"

# 4. Test dashboard creation
python3 enhanced_project_dashboard.py --dry-run
```

### **Evening Wrap-up Routine**
```bash
# 1. Generate daily activity summary
python3 notion_daily_summary.py

# 2. Backup configuration
cp config/notion_config.py config/backups/notion_config_$(date +%Y%m%d).py

# 3. Review AI tool performance
python3 -c "
from notion_integration_api import OrchestrationNotionBridge, create_notion_config
import asyncio

async def daily_metrics():
    bridge = OrchestrationNotionBridge(create_notion_config())
    metrics = await bridge.get_daily_metrics()
    print(f'Tasks completed today: {metrics.get('tasks_completed', 0)}')
    print(f'AI tool usage: {metrics.get('tool_usage', {})}')

asyncio.run(daily_metrics())
"
```

## 📊 **Metrics Interpretation**

### **1. AI Tool Performance Metrics**

#### **Response Time Analysis**
```python
# Good Performance Indicators
response_times = {
    "cursor": "< 500ms",    # ✅ Excellent for quick edits
    "continue": "< 1000ms", # ✅ Fast UI development
    "mcp_server": "< 100ms" # ✅ Low-latency coordination
}

# Warning Thresholds
warning_thresholds = {
    "cursor": 1000,      # 🟡 Getting slower
    "continue": 2000,    # 🟡 UI responsiveness issues
    "mcp_server": 300   # 🟡 Coordination latency
}

# Critical Thresholds
critical_thresholds = {
    "cursor": 2000,      # 🔴 Significantly impacted
    "continue": 4000,    # 🔴 UI development blocked
    "mcp_server": 1000  # 🔴 System coordination failing
}
```

#### **Success Rate Monitoring**
```python
# Health Status Interpretation
def interpret_success_rate(rate):
    if rate >= 95:
        return "🟢 Excellent - Operating optimally"
    elif rate >= 90:
        return "🟡 Good - Minor issues may exist"
    elif rate >= 80:
        return "🟠 Warning - Investigation needed"
    else:
        return "🔴 Critical - Immediate attention required"

# Common Success Rate Issues
success_rate_issues = {
    "90-95%": "Network connectivity intermittent",
    "80-90%": "API rate limiting or authentication issues",
    "70-80%": "Configuration problems or resource constraints",
    "< 70%": "Major system failure or misconfiguration"
}
```

### **2. Development Velocity Metrics**

#### **Task Completion Analysis**
```python
# Velocity Calculations
def calculate_velocity_metrics(tasks_data):
    """Calculate development velocity from task data"""
    
    # Tasks completed per day
    daily_completion = len([t for t in tasks_data if t.status == 'Done'])
    
    # Average task completion time
    completion_times = [t.actual_hours for t in tasks_data if t.actual_hours]
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
    
    # Estimation accuracy
    estimates = [(t.actual_hours, t.estimated_hours) for t in tasks_data 
                if t.actual_hours and t.estimated_hours]
    estimation_accuracy = calculate_estimation_accuracy(estimates)
    
    return {
        "daily_completion": daily_completion,
        "avg_completion_time": avg_completion_time,
        "estimation_accuracy": estimation_accuracy,
        "velocity_trend": calculate_trend(tasks_data)
    }

# Velocity Benchmarks
velocity_benchmarks = {
    "solo_developer": {
        "tasks_per_day": 3,      # ✅ Sustainable pace
        "story_points_per_week": 20,  # ✅ Good progress
        "estimation_accuracy": 80     # ✅ Good planning
    },
    "ai_assisted": {
        "tasks_per_day": 5,      # 🚀 AI acceleration
        "story_points_per_week": 35,  # 🚀 Enhanced productivity
        "estimation_accuracy": 85     # 🚀 Better predictability
    }
}
```

### **3. System Health Monitoring**

#### **Database Performance**
```python
# Database Health Indicators
database_health_checks = {
    "response_time": {
        "good": "< 200ms",
        "warning": "200-500ms", 
        "critical": "> 500ms"
    },
    "error_rate": {
        "good": "< 1%",
        "warning": "1-5%",
        "critical": "> 5%"
    },
    "cache_hit_rate": {
        "good": "> 80%",
        "warning": "60-80%",
        "critical": "< 60%"
    }
}

# Daily Health Check Script
def daily_health_check():
    """Perform comprehensive system health check"""
    
    checks = {
        "api_connectivity": check_notion_api(),
        "database_access": check_database_access(),
        "mcp_server_health": check_mcp_server(),
        "cache_performance": check_cache_performance(),
        "error_rates": check_error_rates()
    }
    
    # Generate health report
    report = generate_health_report(checks)
    log_to_notion(report)
    
    return report
```

## 🔧 **Troubleshooting Procedures**

### **1. API Connection Issues**

#### **Problem: Notion API Authentication Errors**
```bash
# Diagnostic Steps
echo "🔍 Diagnosing Notion API authentication..."

# Check environment variables
echo "NOTION_API_TOKEN: ${NOTION_API_TOKEN:0:10}..."
echo "NOTION_WORKSPACE_ID: $NOTION_WORKSPACE_ID"

# Validate token format
python3 -c "
import os
token = os.getenv('NOTION_API_TOKEN', '')
if token.startswith('secret_'):
    print('✅ Token format valid')
else:
    print('❌ Invalid token format - should start with secret_')
"

# Test API connectivity
curl -H "Authorization: Bearer $NOTION_API_TOKEN" \
     -H "Notion-Version: 2022-06-28" \
     https://api.notion.com/v1/users/me

# Resolution Steps
if [ $? -ne 0 ]; then
    echo "🔧 Resolving authentication issues..."
    echo "1. Verify token in .env file"
    echo "2. Check Notion integration permissions"
    echo "3. Regenerate token if necessary"
fi
```

#### **Problem: Rate Limiting**
```python
# Rate Limit Handler
import time
import random

def handle_rate_limit(response):
    """Handle Notion API rate limiting gracefully"""
    
    if response.status_code == 429:
        # Get retry delay from headers
        retry_after = int(response.headers.get('Retry-After', 1))
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0.1, 0.3)
        sleep_time = retry_after + jitter
        
        print(f"⏱️ Rate limited. Waiting {sleep_time:.1f} seconds...")
        time.sleep(sleep_time)
        
        return True
    return False

# Implement exponential backoff
def exponential_backoff_retry(func, max_retries=3):
    """Retry function with exponential backoff"""
    
    for attempt in range(max_retries):
        try:
            result = func()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"🔄 Retry {attempt + 1}/{max_retries} in {wait_time:.1f}s")
            time.sleep(wait_time)
```

### **2. Performance Issues**

#### **Problem: Slow Dashboard Loading**
```python
# Performance Diagnostic Script
def diagnose_performance_issues():
    """Diagnose and resolve dashboard performance issues"""
    
    import time
    from notion_integration_api import create_notion_config, NotionAPIClient
    
    config = create_notion_config()
    client = NotionAPIClient(config)
    
    # Test database query performance
    databases_to_test = [
        "task_management",
        "development_log", 
        "ai_tool_metrics"
    ]
    
    performance_results = {}
    
    for db_name in databases_to_test:
        start_time = time.time()
        
        try:
            # Test query with limit
            data = client.get_database_items(db_name, cache_strategy="REALTIME")
            end_time = time.time()
            
            performance_results[db_name] = {
                "response_time": end_time - start_time,
                "record_count": len(data),
                "status": "success"
            }
            
        except Exception as e:
            performance_results[db_name] = {
                "response_time": 0,
                "record_count": 0,
                "status": f"error: {str(e)}"
            }
    
    # Generate performance report
    for db_name, result in performance_results.items():
        status = "✅" if result["status"] == "success" else "❌"
        print(f"{status} {db_name}: {result['response_time']:.2f}s ({result['record_count']} records)")
    
    return performance_results

# Performance Optimization Steps
performance_optimization_steps = """
🚀 Performance Optimization Checklist:

1. Cache Strategy Review
   - Check cache hit rates
   - Adjust TTL values based on data volatility
   - Implement intelligent cache invalidation

2. Query Optimization
   - Use appropriate filters to reduce data transfer
   - Implement pagination for large datasets
   - Consider database indexing patterns

3. Network Optimization
   - Monitor API response times
   - Implement request compression
   - Use connection pooling

4. Frontend Optimization
   - Implement virtual scrolling for large lists
   - Use React.memo for expensive components
   - Optimize bundle size and loading
"""
```

### **3. Data Consistency Issues**

#### **Problem: Missing or Inconsistent Data**
```python
# Data Validation Script
def validate_data_consistency():
    """Validate data consistency across Notion databases"""
    
    from config.notion_config import get_config, validate_database_access
    
    config = get_config()
    
    # Check database accessibility
    access_results = validate_database_access(config)
    inaccessible_dbs = [db for db, accessible in access_results.items() if not accessible]
    
    if inaccessible_dbs:
        print(f"❌ Inaccessible databases: {inaccessible_dbs}")
        return False
    
    # Validate required properties
    validation_results = {}
    
    for db_name in ["task_management", "development_log", "ai_tool_metrics"]:
        try:
            # Get database schema
            db_id = getattr(config.databases, db_name)
            schema = get_database_schema(db_id)
            
            # Validate required properties exist
            required_props = get_required_properties(db_name)
            missing_props = [prop for prop in required_props if prop not in schema]
            
            validation_results[db_name] = {
                "status": "valid" if not missing_props else "invalid",
                "missing_properties": missing_props
            }
            
        except Exception as e:
            validation_results[db_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return validation_results

# Data Repair Procedures
def repair_data_inconsistencies(validation_results):
    """Repair identified data inconsistencies"""
    
    for db_name, result in validation_results.items():
        if result["status"] == "invalid":
            print(f"🔧 Repairing {db_name}...")
            
            # Add missing properties
            for prop in result["missing_properties"]:
                add_database_property(db_name, prop)
            
            print(f"✅ Repaired {db_name}")
```

## 📈 **Performance Monitoring**

### **1. Real-time Monitoring Dashboard**
```python
# Real-time Monitoring Script
def create_monitoring_dashboard():
    """Create real-time monitoring dashboard"""
    
    import time
    import json
    from datetime import datetime
    
    def collect_metrics():
        """Collect real-time system metrics"""
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_health": check_api_health(),
            "response_times": measure_response_times(),
            "error_rates": calculate_error_rates(),
            "cache_performance": get_cache_stats(),
            "active_connections": count_active_connections()
        }
    
    # Continuous monitoring loop
    while True:
        metrics = collect_metrics()
        
        # Log to console
        print(f"📊 {metrics['timestamp']}")
        print(f"   API Health: {metrics['api_health']}")
        print(f"   Avg Response: {metrics['response_times']['average']:.0f}ms")
        print(f"   Error Rate: {metrics['error_rates']:.1f}%")
        print(f"   Cache Hit Rate: {metrics['cache_performance']['hit_rate']:.1f}%")
        print("   " + "=" * 50)
        
        # Save metrics
        save_metrics_to_notion(metrics)
        
        time.sleep(60)  # Update every minute

# Alert Thresholds
alert_thresholds = {
    "response_time": 2000,      # 2 seconds
    "error_rate": 5.0,          # 5%
    "cache_hit_rate": 70.0,     # 70%
    "api_availability": 95.0    # 95%
}

def check_alerts(metrics):
    """Check metrics against alert thresholds"""
    
    alerts = []
    
    if metrics["response_times"]["average"] > alert_thresholds["response_time"]:
        alerts.append(f"🔴 High response time: {metrics['response_times']['average']:.0f}ms")
    
    if metrics["error_rates"] > alert_thresholds["error_rate"]:
        alerts.append(f"🔴 High error rate: {metrics['error_rates']:.1f}%")
    
    if metrics["cache_performance"]["hit_rate"] < alert_thresholds["cache_hit_rate"]:
        alerts.append(f"🔴 Low cache hit rate: {metrics['cache_performance']['hit_rate']:.1f}%")
    
    return alerts
```

### **2. Performance Optimization Workflows**
```python
# Automated Performance Optimization
def auto_optimize_performance():
    """Automatically optimize system performance"""
    
    # Collect performance baseline
    baseline = collect_performance_baseline()
    
    # Identify optimization opportunities
    optimizations = [
        optimize_cache_strategy(),
        optimize_query_patterns(),
        optimize_network_requests(),
        optimize_data_structures()
    ]
    
    # Apply optimizations
    for optimization in optimizations:
        if optimization["impact_score"] > 0.1:  # 10% improvement threshold
            print(f"🚀 Applying optimization: {optimization['name']}")
            apply_optimization(optimization)
    
    # Measure improvement
    post_optimization = collect_performance_baseline()
    improvement = calculate_improvement(baseline, post_optimization)
    
    print(f"📈 Performance improvement: {improvement:.1f}%")
    
    return improvement

# Cache Strategy Optimization
def optimize_cache_strategy():
    """Optimize caching strategy based on usage patterns"""
    
    # Analyze cache usage patterns
    cache_stats = analyze_cache_usage()
    
    recommendations = []
    
    # Adjust TTL based on data volatility
    for db_name, stats in cache_stats.items():
        if stats["hit_rate"] < 70:
            new_ttl = min(stats["current_ttl"] * 2, 3600)  # Max 1 hour
            recommendations.append({
                "action": "increase_ttl",
                "database": db_name,
                "current_ttl": stats["current_ttl"],
                "recommended_ttl": new_ttl,
                "expected_improvement": 15
            })
    
    return recommendations
```

## 🔒 **Security Monitoring**

### **1. Access Control Monitoring**
```python
# Security Monitoring Script
def monitor_security():
    """Monitor security aspects of Notion integration"""
    
    security_checks = {
        "api_key_exposure": check_api_key_exposure(),
        "unauthorized_access": check_unauthorized_access(),
        "data_leakage": check_data_leakage(),
        "permission_escalation": check_permission_escalation()
    }
    
    # Generate security report
    security_report = {
        "timestamp": datetime.now().isoformat(),
        "status": "secure" if all(security_checks.values()) else "warning",
        "checks": security_checks
    }
    
    # Log security events
    if not security_report["status"] == "secure":
        log_security_incident(security_report)
    
    return security_report

# API Key Security Check
def check_api_key_exposure():
    """Check for exposed API keys in logs or configuration"""
    
    import re
    import os
    
    # Pattern to match Notion API keys
    api_key_pattern = r'secret_[a-zA-Z0-9]{43}'
    
    # Files to check
    files_to_check = [
        'logs/*.log',
        '*.py',
        '*.js',
        '*.ts',
        '.env*'
    ]
    
    exposed_keys = []
    
    for file_pattern in files_to_check:
        for file_path in glob.glob(file_pattern):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    matches = re.findall(api_key_pattern, content)
                    if matches:
                        exposed_keys.append({
                            "file": file_path,
                            "matches": len(matches)
                        })
            except Exception as e:
                continue
    
    return len(exposed_keys) == 0
```

## 📋 **Maintenance Procedures**

### **1. Weekly Maintenance Tasks**
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "🔧 Starting weekly Notion maintenance..."

# 1. Database cleanup
echo "📊 Cleaning up database entries..."
python3 -c "
from notion_maintenance import cleanup_old_entries
cleanup_old_entries(days=30)  # Remove entries older than 30 days
"

# 2. Performance analysis
echo "📈 Analyzing performance trends..."
python3 -c "
from notion_analytics import generate_weekly_report
report = generate_weekly_report()
print(f'Weekly summary generated: {report}')
"

# 3. Configuration validation
echo "⚙️ Validating configuration..."
python3 -c "
from config.notion_config import get_config, validate_database_access
config = get_config()
results = validate_database_access(config)
print(f'Configuration valid: {all(results.values())}')
"

# 4. Security audit
echo "🔒 Running security audit..."
python3 -c "
from notion_security import run_security_audit
audit_results = run_security_audit()
print(f'Security status: {audit_results['status']}')
"

echo "✅ Weekly maintenance completed!"
```

### **2. Monthly Optimization Review**
```python
# Monthly Optimization Review
def monthly_optimization_review():
    """Conduct comprehensive monthly optimization review"""
    
    # Performance analysis
    performance_trends = analyze_monthly_performance()
    
    # Usage pattern analysis
    usage_patterns = analyze_usage_patterns()
    
    # Cost optimization
    cost_analysis = analyze_notion_api_costs()
    
    # Generate recommendations
    recommendations = generate_optimization_recommendations(
        performance_trends,
        usage_patterns,
        cost_analysis
    )
    
    # Create optimization plan
    optimization_plan = create_optimization_plan(recommendations)
    
    # Log to Notion for tracking
    log_monthly_review({
        "performance_trends": performance_trends,
        "usage_patterns": usage_patterns,
        "cost_analysis": cost_analysis,
        "recommendations": recommendations,
        "optimization_plan": optimization_plan
    })
    
    return optimization_plan
```

## 📞 **Emergency Procedures**

### **1. System Outage Response**
```python
# Emergency Response Playbook
def emergency_response_procedure():
    """Handle system outages and critical issues"""
    
    print("🚨 EMERGENCY RESPONSE ACTIVATED")
    
    # 1. Assess situation
    system_status = assess_system_status()
    print(f"System Status: {system_status['overall_health']}")
    
    # 2. Implement immediate fixes
    if system_status['api_accessible']:
        print("✅ API accessible - proceeding with standard recovery")
        standard_recovery_procedure()
    else:
        print("❌ API inaccessible - implementing emergency protocols")
        emergency_recovery_procedure()
    
    # 3. Notify stakeholders
    send_emergency_notification(system_status)
    
    # 4. Document incident
    document_incident(system_status)

def emergency_recovery_procedure():
    """Emergency recovery when API is inaccessible"""
    
    # Switch to cached data
    enable_offline_mode()
    
    # Check alternative endpoints
    test_alternative_endpoints()
    
    # Implement circuit breaker
    enable_circuit_breaker()
    
    # Start health monitoring
    start_health_monitoring()
```

### **2. Data Recovery Procedures**
```python
# Data Recovery Playbook
def data_recovery_procedure():
    """Recover lost or corrupted data"""
    
    # 1. Assess data loss scope
    data_assessment = assess_data_loss()
    
    # 2. Check available backups
    available_backups = list_available_backups()
    
    # 3. Implement recovery strategy
    if available_backups:
        recovery_strategy = "backup_restore"
        restore_from_backup(available_backups[-1])  # Latest backup
    else:
        recovery_strategy = "manual_reconstruction"
        reconstruct_data_manually()
    
    # 4. Validate recovery
    validation_results = validate_recovered_data()
    
    # 5. Document recovery process
    document_recovery_process({
        "data_assessment": data_assessment,
        "recovery_strategy": recovery_strategy,
        "validation_results": validation_results
    })
    
    return validation_results
```

---

**Last Updated**: 2025-01-24  
**Version**: 2.0  
**Maintenance Schedule**: Weekly reviews, Monthly optimizations  
**Emergency Contact**: Orchestra AI Development Team 