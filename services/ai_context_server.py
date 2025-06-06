#!/usr/bin/env python3
"""
Enhanced AI Context Server - Next Generation AI Collaboration
Provides rich, contextual codebase access to any AI assistant
"""

import asyncio
import json
import os
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from pathlib import Path
import traceback

# File monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Code analysis
import ast
import git

# Our existing imports
import websockets
import aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Vector store for semantic search
from weaviate import Client as WeaviateClient

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai-context-server")

@dataclass
class CodeContext:
    """Rich context about a code file"""
    path: str
    content: str
    language: str
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    last_modified: datetime = field(default_factory=datetime.now)
    git_history: List[Dict] = field(default_factory=list)
    related_tests: List[str] = field(default_factory=list)
    semantic_neighbors: List[str] = field(default_factory=list)

@dataclass
class ConnectedAI:
    """Enhanced AI connection with context tracking"""
    name: str
    websocket: WebSocket
    connected_at: datetime
    capabilities: List[str] = field(default_factory=list)
    last_ping: float = field(default_factory=time.time)
    message_count: int = 0
    subscribed_paths: Set[str] = field(default_factory=set)
    access_level: str = "contributor"  # observer, contributor, admin
    active_context: Optional[CodeContext] = None

class FileChangeHandler(FileSystemEventHandler):
    """Monitor file system changes"""
    def __init__(self, context_server):
        self.context_server = context_server
        
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.context_server.handle_file_change(event.src_path)
            )

class AIContextServer:
    """
    Enhanced AI Bridge providing rich contextual codebase access
    """
    
    def __init__(self):
        self.host = os.getenv("CONTEXT_SERVER_HOST", "0.0.0.0")
        self.port = int(os.getenv("CONTEXT_SERVER_PORT", "8765"))
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/1")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        
        # Connected AI assistants
        self.connected_ais: Dict[str, ConnectedAI] = {}
        
        # Enhanced API keys with access levels
        self.api_keys = {
            "manus-key-2024": {"name": "manus-ai", "level": "admin"},
            "cursor-key-2024": {"name": "cursor-ai", "level": "admin"},
            "claude-key-2024": {"name": "claude-ai", "level": "contributor"},
            "gpt4-key-2024": {"name": "gpt4-ai", "level": "contributor"},
            "observer-key-2024": {"name": "observer", "level": "observer"}
        }
        
        # Services
        self.redis = None
        self.weaviate = None
        self.git_repo = None
        self.file_observer = None
        
        # Caches
        self.file_cache: Dict[str, CodeContext] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # FastAPI app
        self.app = FastAPI(title="AI Context Server", version="2.0.0")
        self.setup_fastapi()
        
    async def setup_services(self):
        """Initialize all services"""
        # Redis for real-time updates
        try:
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info("✅ Redis connected for real-time sync")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable: {e}")
        
        # Weaviate for semantic search
        try:
            self.weaviate = WeaviateClient(self.weaviate_url)
            logger.info("✅ Weaviate connected for semantic search")
        except Exception as e:
            logger.warning(f"⚠️ Weaviate unavailable: {e}")
        
        # Git repository
        try:
            self.git_repo = git.Repo(".")
            logger.info("✅ Git repository loaded")
        except Exception as e:
            logger.warning(f"⚠️ Git not available: {e}")
        
        # File system monitoring
        self.setup_file_monitoring()
        
        # Build initial caches
        await self.build_codebase_index()
    
    def setup_file_monitoring(self):
        """Setup file system monitoring"""
        event_handler = FileChangeHandler(self)
        self.file_observer = Observer()
        self.file_observer.schedule(event_handler, ".", recursive=True)
        self.file_observer.start()
        logger.info("✅ File system monitoring active")
    
    def setup_fastapi(self):
        """Setup FastAPI routes"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.get("/")
        async def root():
            return {
                "service": "AI Context Server",
                "version": "2.0.0",
                "features": [
                    "real-time file monitoring",
                    "semantic code search",
                    "dependency analysis",
                    "git integration",
                    "multi-AI collaboration"
                ]
            }
        
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "connected_ais": len(self.connected_ais),
                "cached_files": len(self.file_cache),
                "services": {
                    "redis": self.redis is not None,
                    "weaviate": self.weaviate is not None,
                    "git": self.git_repo is not None
                }
            }
        
        @self.app.websocket("/context/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_ai_connection(websocket)
    
    async def build_codebase_index(self):
        """Build initial codebase index"""
        logger.info("🔍 Building codebase index...")
        
        # Index Python files for now
        for py_file in Path(".").rglob("*.py"):
            if any(skip in str(py_file) for skip in ["venv/", "__pycache__", ".git/"]):
                continue
                
            try:
                context = await self.analyze_file(str(py_file))
                self.file_cache[str(py_file)] = context
                
                # Update dependency graph
                for dep in context.dependencies:
                    if dep not in self.dependency_graph:
                        self.dependency_graph[dep] = set()
                    self.dependency_graph[dep].add(str(py_file))
                    
            except Exception as e:
                logger.error(f"Failed to index {py_file}: {e}")
        
        logger.info(f"✅ Indexed {len(self.file_cache)} files")
    
    async def analyze_file(self, file_path: str) -> CodeContext:
        """Analyze a file and extract context"""
        context = CodeContext(path=file_path, content="", language="")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                context.content = f.read()
            
            # Detect language
            if file_path.endswith('.py'):
                context.language = "python"
                await self.analyze_python_file(context)
            elif file_path.endswith('.js') or file_path.endswith('.ts'):
                context.language = "javascript"
                # TODO: Add JS/TS analysis
            
            # Get git history if available
            if self.git_repo:
                try:
                    commits = list(self.git_repo.iter_commits(paths=file_path, max_count=5))
                    context.git_history = [
                        {
                            "sha": c.hexsha[:8],
                            "author": str(c.author),
                            "date": c.committed_datetime.isoformat(),
                            "message": c.message.strip()
                        }
                        for c in commits
                    ]
                except:
                    pass
            
            # Find related tests
            context.related_tests = self.find_related_tests(file_path)
            
            # Get semantic neighbors if Weaviate is available
            if self.weaviate:
                # TODO: Implement semantic search
                pass
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            
        return context
    
    async def analyze_python_file(self, context: CodeContext):
        """Extract Python-specific context"""
        try:
            tree = ast.parse(context.content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        context.imports.append(alias.name)
                        context.dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        context.imports.append(node.module)
                        context.dependencies.append(node.module)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    context.exports.append(node.name)
                    
        except Exception as e:
            logger.debug(f"AST parsing failed for {context.path}: {e}")
    
    def find_related_tests(self, file_path: str) -> List[str]:
        """Find test files related to a source file"""
        tests = []
        base_name = Path(file_path).stem
        
        # Common test patterns
        test_patterns = [
            f"test_{base_name}.py",
            f"{base_name}_test.py",
            f"tests/test_{base_name}.py",
            f"tests/{base_name}_test.py"
        ]
        
        for pattern in test_patterns:
            if Path(pattern).exists():
                tests.append(pattern)
                
        return tests
    
    async def handle_file_change(self, file_path: str):
        """Handle file system changes"""
        logger.info(f"📝 File changed: {file_path}")
        
        # Update cache
        context = await self.analyze_file(file_path)
        self.file_cache[file_path] = context
        
        # Notify subscribed AIs
        change_event = {
            "type": "file_changed",
            "path": file_path,
            "context": {
                "language": context.language,
                "imports": context.imports,
                "exports": context.exports,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send to AIs watching this file
        for ai_name, ai in self.connected_ais.items():
            if file_path in ai.subscribed_paths or "*" in ai.subscribed_paths:
                try:
                    await ai.websocket.send_text(json.dumps(change_event))
                except:
                    pass
        
        # Publish to Redis for distributed updates
        if self.redis:
            try:
                await self.redis.publish(
                    f"file_change:{file_path}",
                    json.dumps(change_event)
                )
            except:
                pass
    
    async def handle_ai_connection(self, websocket: WebSocket):
        """Handle enhanced AI connections"""
        await websocket.accept()
        
        ai_name = None
        try:
            # Enhanced authentication
            auth_msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            auth_data = json.loads(auth_msg)
            
            api_key = auth_data.get("api_key", "")
            if api_key not in self.api_keys:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid API key"
                }))
                await websocket.close()
                return
            
            # Get AI info
            key_info = self.api_keys[api_key]
            ai_name = auth_data.get("ai_name", key_info["name"])
            
            # Create enhanced connection
            connected_ai = ConnectedAI(
                name=ai_name,
                websocket=websocket,
                connected_at=datetime.now(),
                capabilities=auth_data.get("capabilities", []),
                access_level=key_info["level"]
            )
            
            self.connected_ais[ai_name] = connected_ai
            
            # Send rich welcome message
            welcome = {
                "type": "context_ready",
                "ai_name": ai_name,
                "access_level": connected_ai.access_level,
                "codebase": {
                    "files": len(self.file_cache),
                    "languages": list(set(c.language for c in self.file_cache.values() if c.language)),
                    "last_commit": self.git_repo.head.commit.hexsha[:8] if self.git_repo else None
                },
                "capabilities": {
                    "file_access": True,
                    "semantic_search": self.weaviate is not None,
                    "real_time_updates": True,
                    "git_integration": self.git_repo is not None,
                    "code_execution": connected_ai.access_level in ["contributor", "admin"]
                },
                "available_tools": self.get_available_tools(connected_ai.access_level)
            }
            
            await websocket.send_text(json.dumps(welcome))
            logger.info(f"✅ {ai_name} connected with {connected_ai.access_level} access")
            
            # Handle messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                    await self.handle_ai_message(ai_name, message)
                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except WebSocketDisconnect:
                    break
                    
        except Exception as e:
            logger.error(f"Connection error: {e}")
            logger.debug(traceback.format_exc())
        finally:
            if ai_name and ai_name in self.connected_ais:
                del self.connected_ais[ai_name]
                logger.info(f"🔌 {ai_name} disconnected")
    
    async def handle_ai_message(self, ai_name: str, message: str):
        """Handle messages from connected AIs"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            ai = self.connected_ais.get(ai_name)
            if not ai:
                return
            
            # Route message types
            if msg_type == "get_file":
                await self.handle_get_file(ai, data)
            elif msg_type == "search":
                await self.handle_search(ai, data)
            elif msg_type == "subscribe":
                await self.handle_subscribe(ai, data)
            elif msg_type == "get_context":
                await self.handle_get_context(ai, data)
            elif msg_type == "execute":
                await self.handle_execute(ai, data)
            else:
                # Broadcast to other AIs
                await self.broadcast_to_others(ai_name, data)
                
        except Exception as e:
            logger.error(f"Error handling message from {ai_name}: {e}")
            
    async def handle_get_file(self, ai: ConnectedAI, data: Dict):
        """Provide file with rich context"""
        file_path = data.get("path")
        
        # Check cache first
        if file_path in self.file_cache:
            context = self.file_cache[file_path]
        else:
            context = await self.analyze_file(file_path)
            self.file_cache[file_path] = context
        
        # Build response with related context
        response = {
            "type": "file_context",
            "path": file_path,
            "content": context.content,
            "language": context.language,
            "context": {
                "imports": context.imports,
                "exports": context.exports,
                "dependencies": list(self.dependency_graph.get(file_path, [])),
                "dependents": [f for f, deps in self.dependency_graph.items() if file_path in deps],
                "tests": context.related_tests,
                "git_history": context.git_history,
                "last_modified": context.last_modified.isoformat()
            }
        }
        
        await ai.websocket.send_text(json.dumps(response))
        
    async def handle_search(self, ai: ConnectedAI, data: Dict):
        """Handle semantic or keyword search"""
        query = data.get("query", "")
        search_type = data.get("search_type", "keyword")  # keyword or semantic
        
        results = []
        
        if search_type == "keyword":
            # Simple keyword search in cache
            for path, context in self.file_cache.items():
                if query.lower() in context.content.lower():
                    results.append({
                        "path": path,
                        "language": context.language,
                        "preview": self.get_preview(context.content, query),
                        "score": 1.0  # Simple scoring
                    })
        elif search_type == "semantic" and self.weaviate:
            # TODO: Implement semantic search with Weaviate
            pass
        
        await ai.websocket.send_text(json.dumps({
            "type": "search_results",
            "query": query,
            "results": results[:20]  # Limit results
        }))
    
    async def handle_subscribe(self, ai: ConnectedAI, data: Dict):
        """Subscribe AI to file changes"""
        paths = data.get("paths", [])
        
        for path in paths:
            ai.subscribed_paths.add(path)
        
        await ai.websocket.send_text(json.dumps({
            "type": "subscribed",
            "paths": list(ai.subscribed_paths)
        }))
    
    async def handle_get_context(self, ai: ConnectedAI, data: Dict):
        """Get intelligent context for current work"""
        file_path = data.get("current_file")
        context_type = data.get("context_type", "related")  # related, dependencies, etc.
        
        # This is where we'd implement smart context selection
        # For now, return related files
        context_files = []
        
        if file_path in self.file_cache:
            current = self.file_cache[file_path]
            
            # Get imports/dependencies
            for dep in current.dependencies:
                for cached_path, cached_context in self.file_cache.items():
                    if dep in cached_context.exports:
                        context_files.append({
                            "path": cached_path,
                            "reason": f"exports {dep}",
                            "preview": cached_context.content[:200]
                        })
        
        await ai.websocket.send_text(json.dumps({
            "type": "intelligent_context",
            "current_file": file_path,
            "context": context_files
        }))
        
    async def handle_execute(self, ai: ConnectedAI, data: Dict):
        """Handle code execution requests (if permitted)"""
        if ai.access_level not in ["contributor", "admin"]:
            await ai.websocket.send_text(json.dumps({
                "type": "error",
                "message": "Insufficient permissions for code execution"
            }))
            return
        
        # TODO: Implement sandboxed code execution
        await ai.websocket.send_text(json.dumps({
            "type": "execution_result",
            "status": "not_implemented"
        }))
    
    def get_preview(self, content: str, query: str, context_lines: int = 2) -> str:
        """Get preview of content around query match"""
        lines = content.split('\n')
        query_lower = query.lower()
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                return '\n'.join(lines[start:end])
        
        return content[:200]
    
    def get_available_tools(self, access_level: str) -> List[Dict]:
        """Get tools available for access level"""
        tools = [
            {"name": "get_file", "description": "Get file with full context"},
            {"name": "search", "description": "Search codebase"},
            {"name": "subscribe", "description": "Subscribe to file changes"},
            {"name": "get_context", "description": "Get intelligent context"}
        ]
        
        if access_level in ["contributor", "admin"]:
            tools.extend([
                {"name": "execute", "description": "Execute code in sandbox"},
                {"name": "modify_file", "description": "Modify files"}
            ])
            
        if access_level == "admin":
            tools.extend([
                {"name": "system_command", "description": "Run system commands"},
                {"name": "manage_ais", "description": "Manage other AI connections"}
            ])
            
        return tools
    
    async def broadcast_to_others(self, sender: str, message: Dict):
        """Broadcast message to other AIs"""
        for ai_name, ai in self.connected_ais.items():
            if ai_name != sender:
                try:
                    await ai.websocket.send_text(json.dumps({
                        **message,
                        "sender": sender
                    }))
                except:
                    pass
    
    async def start_server(self):
        """Start the enhanced context server"""
        await self.setup_services()
        
        logger.info(f"🚀 AI Context Server starting on {self.host}:{self.port}")
        logger.info(f"🧠 Features: Real-time sync, Semantic search, Git integration")
        logger.info(f"🔗 WebSocket: ws://{self.host}:{self.port}/context/ws")
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Start the AI Context Server"""
    server = AIContextServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main()) 