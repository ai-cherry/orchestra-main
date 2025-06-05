#!/usr/bin/env python3
"""
Cherry AI Backend Deployment Summary and Status Check
"""

import os
import sys
import json
import psycopg2
import redis
import requests
from datetime import datetime
from pathlib import Path
import subprocess

def check_service_status():
    """Check status of all backend services"""
    
    print("🎼 Cherry AI Backend Status Check")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "issues": [],
        "recommendations": []
    }
    
    # 1. Check PostgreSQL
    print("📊 PostgreSQL:")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="cherry_ai",
            user="postgres",
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        cursor = conn.cursor()
        
        # Check version
        # TODO: Run EXPLAIN ANALYZE on this query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0].split()[1]
        print(f"  ✅ Connected (PostgreSQL {version})")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  📋 Tables: {', '.join(tables) if tables else 'None'}")
        
        # Check user count
        # TODO: Run EXPLAIN ANALYZE on this query
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"  👥 Users: {user_count}")
        
        cursor.close()
        conn.close()
        
        status["services"]["postgresql"] = {
            "status": "running",
            "version": version,
            "tables": tables
        }
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        status["services"]["postgresql"] = {"status": "error", "error": str(e)}
        status["issues"].append("PostgreSQL connection failed")
    
    # 2. Check Redis
    print("\n📮 Redis:")
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        info = r.info()
        version = info.get('redis_version', 'unknown')
        print(f"  ✅ Connected (Redis {version})")
        print(f"  💾 Memory: {info.get('used_memory_human', 'unknown')}")
        print(f"  🔑 Keys: {r.dbsize()}")
        
        status["services"]["redis"] = {
            "status": "running",
            "version": version,
            "memory": info.get('used_memory_human', 'unknown')
        }
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        status["services"]["redis"] = {"status": "error", "error": str(e)}
        status["issues"].append("Redis connection failed")
    
    # 3. Check Weaviate
    print("\n🔍 Weaviate:")
    try:
        response = requests.get("http://localhost:8080/v1/meta", timeout=5)
        if response.status_code == 200:
            meta = response.json()
            version = meta.get('version', 'unknown')
            print(f"  ✅ Connected (Weaviate {version})")
            
            # Check schema
            schema_response = requests.get("http://localhost:8080/v1/schema", timeout=5)
            if schema_response.status_code == 200:
                schema = schema_response.json()
                classes = schema.get('classes', [])
                print(f"  📊 Classes: {len(classes)}")
                if classes:
                    print(f"  📋 Class names: {', '.join([c['class'] for c in classes])}")
            
            status["services"]["weaviate"] = {
                "status": "running",
                "version": version,
                "classes": len(classes)
            }
            
        else:
            raise Exception(f"HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        status["services"]["weaviate"] = {"status": "error", "error": str(e)}
        status["issues"].append("Weaviate connection failed")
    
    # 4. Check API
    print("\n🌐 API Server:")
    api_found = False
    for port in [8000, 8001]:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"  ✅ Running on port {port}")
                api_found = True
                
                # Check docs
                docs_response = requests.get(f"http://localhost:{port}/docs", timeout=2)
                if docs_response.status_code == 200:
                    print(f"  📚 API docs: http://localhost:{port}/docs")
                
                status["services"]["api"] = {
                    "status": "running",
                    "port": port,
                    "docs_url": f"http://localhost:{port}/docs"
                }
                break
                
        except:
            continue
    
    if not api_found:
        print("  ⚠️  Not running or not accessible")
        status["services"]["api"] = {"status": "not_running"}
        status["issues"].append("API server not accessible")
        status["recommendations"].append("Start API with: cd core/conductor/src && uvicorn main:app --host 0.0.0.0 --port 8000")
    
    # 5. Check Docker containers
    print("\n🐳 Docker Containers:")
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line and any(svc in line for svc in ['postgres', 'redis', 'weaviate', 'cherry_ai']):
                    name, status = line.split('\t')
                    containers.append(f"{name}: {status}")
                    print(f"  • {name}: {status}")
            
            status["services"]["docker"] = {
                "status": "running",
                "containers": containers
            }
        
    except Exception as e:
        print(f"  ❌ Error checking Docker: {str(e)}")
    
    # 6. Summary and Recommendations
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_services_running = all(
        svc.get("status") == "running"
        for svc in status["services"].values()
        if isinstance(svc, dict) and svc.get("status")
    )
    
    if all_services_running:
        print("✅ All services are running properly!")
    else:
        print("⚠️  Some services need attention:")
        for issue in status["issues"]:
            print(f"  - {issue}")
    
    if status["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in status["recommendations"]:
            print(f"  - {rec}")
    
    # 7. Save status report
    report_file = f"backend_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # 8. Quick start commands
    print("\n🚀 Quick Commands:")
    print("  • View API docs: http://localhost:8000/docs")
    print(
        "  • Test login: curl -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"scoobyjava\",
        \"password\":\"Huskers1983$\"}'"
    )
    print("  • View logs: tail -f /tmp/cherry_ai-api.log")
    print("  • Check containers: docker ps")
    
    return status

def main():
    """Main execution"""
    status = check_service_status()
    
    # Exit with appropriate code
    if status["issues"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()