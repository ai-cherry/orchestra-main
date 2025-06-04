#!/usr/bin/env python3
"""
Comprehensive backend audit and fix script for Cherry AI
"""

import os
import sys
import json
import subprocess
import asyncio
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class BackendAuditor:
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.root_dir = Path("/root/cherry_ai-main")
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_issue(self, category: str, issue: str, severity: str = "MEDIUM"):
        """Add an issue to the list"""
        self.issues.append({
            "category": category,
            "issue": issue,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        
    def add_fix(self, category: str, fix: str):
        """Add a fix to the list"""
        self.fixes_applied.append({
            "category": category,
            "fix": fix,
            "timestamp": datetime.now().isoformat()
        })
        
    async def audit_backend_structure(self):
        """Audit the backend directory structure"""
        self.log("🔍 Auditing backend structure...")
        
        expected_dirs = [
            "backend/app",
            "backend/app/api",
            "backend/app/core",
            "backend/app/models",
            "backend/app/services",
            "backend/app/utils",
            "backend/tests",
            "backend/alembic"
        ]
        
        for dir_path in expected_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                self.add_issue("STRUCTURE", f"Missing directory: {dir_path}", "HIGH")
                
    async def audit_api_endpoints(self):
        """Audit API endpoints and routes"""
        self.log("🔍 Auditing API endpoints...")
        
        # Check main.py
        main_file = self.root_dir / "backend/app/main.py"
        if main_file.exists():
            content = main_file.read_text()
            
            # Check for CORS configuration
            if "CORSMiddleware" not in content:
                self.add_issue("API", "Missing CORS middleware configuration", "HIGH")
                
            # Check for proper error handlers
            if "@app.exception_handler" not in content:
                self.add_issue("API", "Missing global exception handlers", "MEDIUM")
                
            # Check for API documentation
            if "title=" not in content or "version=" not in content:
                self.add_issue("API", "Missing API documentation metadata", "LOW")
        else:
            self.add_issue("API", "Missing backend/app/main.py", "CRITICAL")
            
    async def audit_database_schema(self):
        """Audit database schema and models"""
        self.log("🔍 Auditing database schema...")
        
        # Check for models
        models_dir = self.root_dir / "backend/app/models"
        if models_dir.exists():
            model_files = list(models_dir.glob("*.py"))
            if len(model_files) < 3:
                self.add_issue("DATABASE", "Insufficient database models", "MEDIUM")
                
            # Check for proper indexes
            for model_file in model_files:
                content = model_file.read_text()
                if "Index" not in content and "index=True" not in content:
                    self.add_issue("DATABASE", f"No indexes defined in {model_file.name}", "MEDIUM")
                    
        # Check alembic migrations
        alembic_dir = self.root_dir / "backend/alembic"
        if not alembic_dir.exists():
            self.add_issue("DATABASE", "Missing alembic migrations directory", "HIGH")
            
    async def audit_authentication(self):
        """Audit authentication mechanisms"""
        self.log("🔍 Auditing authentication...")
        
        auth_file = self.root_dir / "backend/app/core/auth.py"
        if auth_file.exists():
            content = auth_file.read_text()
            
            # Check for JWT implementation
            if "jwt" not in content.lower():
                self.add_issue("AUTH", "JWT not implemented", "HIGH")
                
            # Check for password hashing
            if "bcrypt" not in content and "passlib" not in content:
                self.add_issue("AUTH", "No password hashing library used", "CRITICAL")
                
            # Check for token expiration
            if "expire" not in content:
                self.add_issue("AUTH", "No token expiration logic", "HIGH")
        else:
            self.add_issue("AUTH", "Missing authentication module", "CRITICAL")
            
    async def audit_error_handling(self):
        """Audit error handling patterns"""
        self.log("🔍 Auditing error handling...")
        
        # Check for custom exceptions
        exceptions_file = self.root_dir / "backend/app/core/exceptions.py"
        if not exceptions_file.exists():
            self.add_issue("ERROR_HANDLING", "Missing custom exceptions module", "MEDIUM")
            
        # Check API routes for try-except blocks
        api_dir = self.root_dir / "backend/app/api"
        if api_dir.exists():
            for route_file in api_dir.glob("*.py"):
                content = route_file.read_text()
                if "try:" not in content:
                    self.add_issue("ERROR_HANDLING", f"No error handling in {route_file.name}", "MEDIUM")
                    
    async def audit_security(self):
        """Audit security vulnerabilities"""
        self.log("🔍 Auditing security...")
        
        # Check for SQL injection vulnerabilities
        backend_dir = self.root_dir / "backend"
        if backend_dir.exists():
            for py_file in backend_dir.rglob("*.py"):
                content = py_file.read_text()
                if "f\"SELECT" in content or "f'SELECT" in content:
                    self.add_issue("SECURITY", f"Potential SQL injection in {py_file.name}", "CRITICAL")
                    
                # Check for hardcoded secrets
                if "password=" in content and "env" not in content:
                    self.add_issue("SECURITY", f"Potential hardcoded password in {py_file.name}", "CRITICAL")
                    
        # Check for rate limiting
        main_file = self.root_dir / "backend/app/main.py"
        if main_file.exists():
            content = main_file.read_text()
            if "RateLimiter" not in content and "slowapi" not in content:
                self.add_issue("SECURITY", "No rate limiting implemented", "HIGH")
                
    async def audit_performance(self):
        """Audit performance bottlenecks"""
        self.log("🔍 Auditing performance...")
        
        # Check for database connection pooling
        db_file = self.root_dir / "backend/app/core/database.py"
        if db_file.exists():
            content = db_file.read_text()
            if "pool_size" not in content:
                self.add_issue("PERFORMANCE", "No database connection pooling configured", "HIGH")
                
            # Check for async database operations
            if "async def" not in content:
                self.add_issue("PERFORMANCE", "Database operations not async", "MEDIUM")
                
        # Check for caching implementation
        cache_implemented = False
        for py_file in (self.root_dir / "backend").rglob("*.py"):
