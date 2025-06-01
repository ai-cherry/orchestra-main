"""
Template for Your First Real Agent
This will be customized based on your questionnaire responses
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum

from core.services.agents.base import Agent, AgentConfig as BaseAgentConfig, AgentCapability as BaseAgentCapability, AgentMessage, AgentStatus
from core.services.memory.unified_memory import get_memory_service
from agent.app.services.natural_language_processor import ResponseGenerator

logger = logging.getLogger(__name__)

class CustomAgentCapability(Enum):
    """Additional agent capabilities for your custom agent"""
    DATA_COLLECTION = "data_collection"
    TASK_AUTOMATION = "task_automation"  
    INTEGRATION = "integration"

class AutonomyLevel(Enum):
    """How autonomous the agent should be"""
    FULLY_AUTONOMOUS = "fully_autonomous"
    SEMI_AUTONOMOUS = "semi_autonomous"
    GUIDED = "guided"
    ASSISTANT = "assistant"

@dataclass
class CustomAgentConfig:
    """Extended configuration for your first agent"""
    base_config: BaseAgentConfig
    autonomy_level: AutonomyLevel
    data_types: List[str]
    communication_methods: List[str]
    trigger_mechanism: str
    complexity_level: str
    response_time_target: str
    memory_type: str
    voice_personality: str
    custom_capability: Optional[CustomAgentCapability] = None
    
class YourFirstAgent(Agent):
    """
    Your first real agent - customized based on your needs
    """
    
    def __init__(self, custom_config: CustomAgentConfig):
        # Map custom capabilities to base capabilities
        capability_map = {
            CustomAgentCapability.DATA_COLLECTION: BaseAgentCapability.MONITORING,
            CustomAgentCapability.TASK_AUTOMATION: BaseAgentCapability.TASK_EXECUTION,
            CustomAgentCapability.INTEGRATION: BaseAgentCapability.COLLABORATION
        }
        
        # Add mapped capability to base config if custom capability exists
        if custom_config.custom_capability:
            base_cap = capability_map.get(custom_config.custom_capability)
            if base_cap:
                custom_config.base_config.capabilities.add(base_cap)
        
        super().__init__(custom_config.base_config)
        self.custom_config = custom_config
        self.response_generator = ResponseGenerator()
        self.task_queue: List[Dict[str, Any]] = []
        self.approval_queue: List[Dict[str, Any]] = []
        
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process an incoming message and optionally return a response"""
        logger.info(f"{self.config.name} processing message from {message.sender_id}")
        
        # Extract task from message
        task = {
            "type": message.metadata.get("type", "general"),
            "content": message.content,
            "sender": message.sender_id,
            "metadata": message.metadata
        }
        
        # Process based on autonomy level
        if self.custom_config.autonomy_level == AutonomyLevel.GUIDED:
            if await self._requires_approval(task):
                self.approval_queue.append(task)
                return AgentMessage(
                    sender_id=self.config.id,
                    content="This task requires approval. I've added it to the approval queue.",
                    metadata={"status": "pending_approval", "task_id": len(self.approval_queue)}
                )
        
        # Execute task
        result = await self._execute_task(task)
        
        # Generate response
        response_text = await self._generate_response(result)
        
        # Add voice if configured
        voice_url = None
        if "voice" in self.custom_config.communication_methods:
            voice_url = await self.response_generator.text_to_speech(response_text)
        
        return AgentMessage(
            sender_id=self.config.id,
            content=response_text,
            metadata={
                "result": result,
                "voice_url": voice_url
            }
        )
    
    async def think(self) -> None:
        """Agent's thinking/reasoning process"""
        # Check for pending tasks
        if self.task_queue:
            logger.info(f"{self.config.name} is thinking about {len(self.task_queue)} pending tasks")
            
            # Prioritize tasks based on configuration
            if self.custom_config.response_time_target == "real_time":
                # Process immediately
                self.state.status = AgentStatus.EXECUTING
            elif self.custom_config.response_time_target == "batch":
                # Wait to batch process
                if len(self.task_queue) < 5:
                    await asyncio.sleep(1)
                    
    async def act(self) -> None:
        """Agent's action execution process"""
        if not self.task_queue:
            return
            
        # Process tasks based on complexity
        if self.custom_config.complexity_level == "simple":
            # Process one at a time
            task = self.task_queue.pop(0)
            await self._process_single_task(task)
        else:
            # Process multiple tasks
            tasks_to_process = self.task_queue[:5]
            self.task_queue = self.task_queue[5:]
            
            await asyncio.gather(*[
                self._process_single_task(task) 
                for task in tasks_to_process
            ])
    
    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task based on agent configuration"""
        task_type = task.get("type", "")
        
        if self.custom_config.custom_capability == CustomAgentCapability.DATA_COLLECTION:
            return await self._handle_data_collection(task)
        elif self.custom_config.custom_capability == CustomAgentCapability.TASK_AUTOMATION:
            return await self._handle_automation(task)
        elif self.custom_config.custom_capability == CustomAgentCapability.INTEGRATION:
            return await self._handle_integration(task)
        else:
            return await self._handle_general_task(task)
    
    async def _handle_data_collection(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data collection tasks"""
        source = task.get("metadata", {}).get("source", "unknown")
        
        # Simulate data collection
        collected_data = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "data_points": [
                {"metric": "cpu_usage", "value": 45.2},
                {"metric": "memory_usage", "value": 62.8},
                {"metric": "request_count", "value": 1523}
            ]
        }
        
        # Store in memory if configured
        if self.custom_config.memory_type in ["short_term", "long_term"]:
            await self.remember(
                key=f"data_collection_{source}",
                value=collected_data,
                metadata={"ttl": 3600 if self.custom_config.memory_type == "short_term" else None}
            )
        
        return {
            "status": "success",
            "data": collected_data,
            "summary": f"Collected {len(collected_data['data_points'])} data points from {source}"
        }
    
    async def _handle_automation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task automation"""
        workflow_name = task.get("metadata", {}).get("workflow", "default_workflow")
        
        # Execute workflow if available
        if workflow_name in self.config.workflow_names:
            context = await self.execute_workflow(
                workflow_name, 
                {"task": task, "agent_id": self.config.id}
            )
            return {
                "status": "workflow_executed",
                "workflow_id": str(context.workflow_id),
                "result": context.state
            }
        
        # Fallback to simple automation
        return {
            "status": "automated",
            "actions_taken": ["validated_input", "processed_data", "generated_output"],
            "summary": "Task automated successfully"
        }
    
    async def _handle_integration(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle integration tasks"""
        target_system = task.get("metadata", {}).get("target", "external_api")
        
        # Simulate integration
        return {
            "status": "integrated",
            "target": target_system,
            "data_synced": True,
            "records_processed": 42
        }
    
    async def _handle_general_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general tasks"""
        return {
            "status": "completed",
            "task_type": task.get("type", "unknown"),
            "summary": "General task processed"
        }
    
    async def _process_single_task(self, task: Dict[str, Any]) -> None:
        """Process a single task"""
        try:
            result = await self._execute_task(task)
            
            # Send result back if there's a sender
            if task.get("sender"):
                response = await self._generate_response(result)
                await self.send_message(
                    recipient_id=task["sender"],
                    content=response,
                    metadata=result
                )
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            if task.get("sender"):
                await self.send_message(
                    recipient_id=task["sender"],
                    content=f"Error processing task: {str(e)}",
                    metadata={"error": True}
                )
    
    async def _requires_approval(self, task: Dict[str, Any]) -> bool:
        """Check if task requires approval"""
        # Define approval rules based on your needs
        high_risk_keywords = ["delete", "modify", "update", "production"]
        task_content = task.get("content", "").lower()
        
        return any(keyword in task_content for keyword in high_risk_keywords)
    
    async def _generate_response(self, result: Dict[str, Any]) -> str:
        """Generate natural language response"""
        if self.custom_config.voice_personality == "professional":
            return f"Task completed. Status: {result.get('status', 'unknown')}. {result.get('summary', '')}"
        else:
            return f"Hey! I've finished that task for you. {result.get('summary', 'Everything went smoothly!')}"
    
    def add_task(self, task: Dict[str, Any]) -> None:
        """Add a task to the queue"""
        self.task_queue.append(task)
        
    def approve_task(self, task_id: int) -> bool:
        """Approve a pending task"""
        if 0 <= task_id < len(self.approval_queue):
            task = self.approval_queue.pop(task_id)
            self.task_queue.append(task)
            return True
        return False

# Factory function to create agents based on questionnaire answers
def create_agent_from_answers(answers: Dict[str, str]) -> YourFirstAgent:
    """Create a customized agent based on questionnaire answers"""
    
    # Map answers to configuration
    capability_map = {
        "A": CustomAgentCapability.DATA_COLLECTION,
        "B": CustomAgentCapability.TASK_AUTOMATION,
        "E": CustomAgentCapability.INTEGRATION
    }
    
    autonomy_map = {
        "A": AutonomyLevel.FULLY_AUTONOMOUS,
        "B": AutonomyLevel.SEMI_AUTONOMOUS,
        "C": AutonomyLevel.GUIDED,
        "D": AutonomyLevel.ASSISTANT
    }
    
    # Parse answers (this is a simplified version)
    primary_capability = capability_map.get(answers.get("q1", "B"))
    autonomy = autonomy_map.get(answers.get("q2", "B"))
    
    # Create base config
    base_config = BaseAgentConfig(
        id=f"custom_agent_{datetime.now().timestamp()}",
        name=answers.get("agent_name", "My First Agent"),
        description="Custom agent created from questionnaire",
        capabilities=set(),
        max_concurrent_tasks=5,
        memory_enabled=True,
        collaboration_enabled=True
    )
    
    # Create custom config
    custom_config = CustomAgentConfig(
        base_config=base_config,
        autonomy_level=autonomy,
        data_types=["mixed"],
        communication_methods=["natural_language", "voice"],
        trigger_mechanism=answers.get("q5", "event_driven"),
        complexity_level=answers.get("q6", "medium"),
        response_time_target=answers.get("q8", "near_real_time"),
        memory_type=answers.get("q10", "short_term"),
        voice_personality=answers.get("q11", "friendly"),
        custom_capability=primary_capability
    )
    
    return YourFirstAgent(custom_config) 