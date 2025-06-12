#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

def check_service(url, name):
    try:
        response = requests.get(url, timeout=5)
        status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"{datetime.now().strftime('%H:%M:%S')} {name}: {status}")
        return response.status_code == 200
    except Exception as e:
        print(f"{datetime.now().strftime('%H:%M:%S')} {name}: ❌ {str(e)[:50]}")
        return False

def main():
    services = [
        ("http://192.9.142.8:8000/health", "Personas API"),
        ("http://192.9.142.8:8010/health", "Main API"),
        ("http://192.9.142.8:8020/health", "OpenRouter API"),
        ("https://orchestra-admin-interface.vercel.app", "Admin Interface"),
        ("https://orchestra-ai-frontend.vercel.app", "AI Frontend"),
    ]
    
    print("🔍 Orchestra AI Service Monitor")
    print("=" * 50)
    
    while True:
        all_healthy = True
        for url, name in services:
            healthy = check_service(url, name)
            if not healthy:
                all_healthy = False
        
        if all_healthy:
            print(f"{datetime.now().strftime('%H:%M:%S')} 🎉 All services healthy!")
        else:
            print(f"{datetime.now().strftime('%H:%M:%S')} ⚠️ Some services have issues")
        
        print("-" * 30)
        time.sleep(30)

if __name__ == "__main__":
    main()
