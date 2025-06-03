#!/usr/bin/env python3
"""
Coding Activity Monitor - Detects coding patterns and triggers orchestration
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable
from datetime import datetime, timedelta
import watchdog.observers
import watchdog.events
import fnmatch
import json
import aiohttp

logger = logging.getLogger(__name__)

class CodingPattern:
    """Defines patterns that trigger orchestration"""
    
    def __init__(self, name: str, patterns: List[str], 
                 threshold: int = 1, window_seconds: int = 60):
        self.name = name
        self.patterns = patterns  # File patterns to match
        self.threshold = threshold  # Number of events to trigger
        self.window_seconds = window_seconds
        self.events: List[datetime] = []
    
    def add_event(self) -> bool:
        """Add event and check if threshold reached"""
        now = datetime.now()
        # Remove old events outside window
        self.events = [e for e in self.events 
                      if now - e < timedelta(seconds=self.window_seconds)]
        self.events.append(now)
        return len(self.events) >= self.threshold

class CodingActivityMonitor(watchdog.events.FileSystemEventHandler):
    """Monitors file system for coding activities"""
    
    def __init__(self, orchestrator_callback: Callable, 
                 watch_paths: List[str] = None):
        super().__init__()
        self.orchestrator_callback = orchestrator_callback
        self.watch_paths = watch_paths or ['/root/orchestra-main']
        self.observer = watchdog.observers.Observer()
        self.patterns = self._initialize_patterns()
        self.active_sessions: Dict[str, datetime] = {}
        
    def _initialize_patterns(self) -> List[CodingPattern]:
        """Initialize coding patterns that trigger orchestration"""
        return [
            # Rapid file edits (3+ in 30 seconds)
            CodingPattern("rapid_editing", ["*.py", "*.js", "*.ts"], 3, 30),
            
            # New file creation
            CodingPattern("new_file_creation", ["*.py", "*.js", "*.ts"], 1, 10),
            
            # Test file changes
            CodingPattern("test_updates", ["test_*.py", "*_test.py", "*.test.js"], 1, 10),
            
            # Configuration changes
            CodingPattern("config_changes", ["*.yaml", "*.yml", "*.json", ".env"], 1, 30),
            
            # Large refactoring (10+ files in 2 minutes)
            CodingPattern("refactoring", ["*.py", "*.js", "*.ts"], 10, 120),
        ]
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        self._process_event(event.src_path, "modified")
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        self._process_event(event.src_path, "created")
    
    def _process_event(self, file_path: str, event_type: str):
        """Process file system events and check patterns"""
        file_name = os.path.basename(file_path)
        
        triggers = []
        for pattern in self.patterns:
            # Check if file matches any pattern
            if any(fnmatch.fnmatch(file_name, p) for p in pattern.patterns):
                if pattern.add_event():
                    triggers.append({
                        "pattern": pattern.name,
                        "file": file_path,
                        "event": event_type,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Trigger orchestration if patterns detected
        if triggers:
            asyncio.create_task(self._trigger_orchestration(triggers))
    
    async def _trigger_orchestration(self, triggers: List[Dict]):
        """Trigger orchestration based on detected patterns"""
        context = {
            "triggers": triggers,
            "session_id": self._get_or_create_session(),
            "workspace": self.watch_paths[0],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Triggering orchestration: {triggers[0]['pattern']}")
        await self.orchestrator_callback(context)
    
    def _get_or_create_session(self) -> str:
        """Get current coding session or create new one"""
        now = datetime.now()
        session_timeout = timedelta(minutes=30)
        
        # Clean old sessions
        self.active_sessions = {
            sid: start for sid, start in self.active_sessions.items()
            if now - start < session_timeout
        }
        
        # Return existing or create new session
        if self.active_sessions:
            return list(self.active_sessions.keys())[0]
        else:
            session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}"
            self.active_sessions[session_id] = now
            return session_id
    
    def start(self):
        """Start monitoring file system"""
        for path in self.watch_paths:
            if os.path.exists(path):
                self.observer.schedule(self, path, recursive=True)
                logger.info(f"Monitoring path: {path}")
        
        self.observer.start()
        logger.info("Coding activity monitor started")
    
    def stop(self):
        """Stop monitoring"""
        self.observer.stop()
        self.observer.join()
        logger.info("Coding activity monitor stopped")

class ScheduledAutomation:
    """Handles scheduled automation rules"""
    
    def __init__(self, orchestrator_callback: Callable):
        self.orchestrator_callback = orchestrator_callback
        self.rules = self._load_automation_rules()
        self.tasks = []
    
    def _load_automation_rules(self) -> List[Dict]:
        """Load automation rules from configuration"""
        return [
            {
                "name": "daily_code_review",
                "schedule": "0 9 * * *",  # 9 AM daily
                "action": "code_review",
                "params": {"depth": "comprehensive"}
            },
            {
                "name": "hourly_optimization_check",
                "schedule": "0 * * * *",  # Every hour
                "action": "performance_check",
                "params": {"threshold": 0.8}
            },
            {
                "name": "weekly_refactoring_suggestions",
                "schedule": "0 10 * * 1",  # Monday 10 AM
                "action": "refactoring_analysis",
                "params": {"scope": "full"}
            }
        ]
    
    async def start(self):
        """Start scheduled automations"""
        for rule in self.rules:
            task = asyncio.create_task(self._run_scheduled_task(rule))
            self.tasks.append(task)
        logger.info(f"Started {len(self.rules)} scheduled automations")
    
    async def _run_scheduled_task(self, rule: Dict):
        """Run a scheduled task based on cron expression"""
        # Simplified - in production use proper cron parser
        while True:
            try:
                # Wait for next scheduled time
                await asyncio.sleep(3600)  # Check hourly
                
                # Trigger orchestration
                context = {
                    "automation": rule["name"],
                    "action": rule["action"],
                    "params": rule["params"],
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Triggering scheduled automation: {rule['name']}")
                await self.orchestrator_callback(context)
                
            except Exception as e:
                logger.error(f"Scheduled task error: {e}")
    
    def stop(self):
        """Stop all scheduled tasks"""
        for task in self.tasks:
            task.cancel()