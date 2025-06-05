import os
#!/usr/bin/env python3
"""Test all services are working"""

import sys
import psycopg2
import redis
import requests

def test_postgres():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
password = os.getenv('ORCHESTRA_APP_PASSWORD')
            database="postgres"
        )
        cur = conn.cursor()
        # TODO: Run EXPLAIN ANALYZE on this query
        cur.execute("SELECT 1")
        result = cur.fetchone()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"PostgreSQL Error: {e}")
        return False

def test_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.set('test', 'value')
        result = r.get('test')
        r.delete('test')
        return result == 'value'
    except Exception as e:
        print(f"Redis Error: {e}")
        return False

def test_weaviate():
    try:
        response = requests.get('http://localhost:8080/v1/.well-known/ready')
        return response.status_code == 200
    except Exception as e:
        print(f"Weaviate Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing services...")
    
    tests = {
        "PostgreSQL": test_postgres(),
        "Redis": test_redis(),
        "Weaviate": test_weaviate()
    }
    
    all_passed = True
    for service, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{service}: {status}")
        if not result:
            all_passed = False
    
    sys.exit(0 if all_passed else 1)
