#!/usr/bin/env python3
"""Task queue for agent coordination"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from typing_extensions import Optional
from collections.abc import deque

logger = logging.getLogger(__name__)


class AgentTaskQueue:
    """Manage task queue for agents"""
    
    def __init__(self):
        self.queues = {}  # agent_id -> deque of tasks
        self.priorities = {}  # task_id -> priority
    
    async def enqueue_task(self, agent_id: str, task: Dict[str, Any], priority: int = 5) -> bool:
        """Add a task to an agent's queue"""
        try:
            if agent_id not in self.queues:
                self.queues[agent_id] = deque()
            
            task_id = task.get("id")
            self.priorities[task_id] = priority
            
            # Insert based on priority
            inserted = False
            for i, existing_task in enumerate(self.queues[agent_id]):
                existing_priority = self.priorities.get(existing_task.get("id"), 5)
                if priority > existing_priority:
                    self.queues[agent_id].insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.queues[agent_id].append(task)
            
            logger.info(f"Task {task_id} enqueued for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Enqueue error: {str(e)}")
            return False
    
    async def dequeue_task(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get next task for an agent"""
        try:
            if agent_id not in self.queues or not self.queues[agent_id]:
                return None
            
            task = self.queues[agent_id].popleft()
            task_id = task.get("id")
            
            if task_id in self.priorities:
                del self.priorities[task_id]
            
            return task
            
        except Exception as e:
            logger.error(f"Dequeue error: {str(e)}")
            return None
