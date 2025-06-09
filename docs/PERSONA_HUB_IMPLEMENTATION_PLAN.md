# Orchestra AI Persona Hub Implementation Plan

## Overview

This implementation plan outlines a phased approach to integrate the Notion-powered persona hub into Orchestra AI, transforming Cherry, Sophia, and Karen into dynamic, lifelike orchestrators with distinct personalities and behaviors.

## Phase 1: Foundation Setup (Week 1)

### 1.1 Notion Database Configuration

**Objective:** Create the persona configuration database in Notion.

**Tasks:**
- [ ] Create "Personas" database in Notion with all required properties
- [ ] Configure OCEAN traits, communication styles, and prompt templates
- [ ] Add detailed entries for Cherry, Sophia, and Karen
- [ ] Set up appropriate access permissions

**Implementation:**
```python
from notion_client import Client
import os

# Initialize Notion client
notion = Client(auth=os.environ.get("NOTION_API_KEY"))

# Create Personas database
database = notion.databases.create(
    parent={"type": "page_id", "page_id": os.environ.get("NOTION_PARENT_PAGE_ID")},
    title=[{"type": "text", "text": {"content": "Personas"}}],
    properties={
        "Name": {"title": {}},
        "Role": {"rich_text": {}},
        "Backstory": {"rich_text": {}},
        "Openness": {"number": {"format": "number"}},
        "Conscientiousness": {"number": {"format": "number"}},
        "Extraversion": {"number": {"format": "number"}},
        "Agreeableness": {"number": {"format": "number"}},
        "Neuroticism": {"number": {"format": "number"}},
        "Humor": {"number": {"format": "number"}},
        "Formality": {"number": {"format": "number"}},
        "Prompt Template": {"rich_text": {}}
    }
)

# Store database ID in environment or configuration
print(f"Created Personas database with ID: {database['id']}")
```

**Deliverable:** Fully configured Notion database with persona entries.

### 1.2 Environment Setup

**Objective:** Prepare the development environment for persona integration.

**Tasks:**
- [ ] Add required environment variables for Notion API
- [ ] Install necessary dependencies (`notion-client`, etc.)
- [ ] Create configuration files for persona integration
- [ ] Set up logging for persona operations

**Implementation:**
```bash
# Add to .env file
NOTION_API_KEY=your_notion_api_key
NOTION_PERSONAS_DB_ID=your_database_id
NOTION_PARENT_PAGE_ID=your_parent_page_id

# Install dependencies
pip install notion-client pydantic httpx
```

**Deliverable:** Configured development environment ready for implementation.

## Phase 2: Core Integration (Weeks 2-3)

### 2.1 Persona Service API

**Objective:** Create API endpoints to access persona configurations.

**Tasks:**
- [ ] Implement FastAPI endpoints for persona retrieval
- [ ] Add caching for performance optimization
- [ ] Create data models for persona configuration
- [ ] Implement error handling and logging

**Implementation:**
```python
# src/personas/models.py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class OCEANTraits(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

class CommunicationStyle(BaseModel):
    humor: float
    formality: float

class PersonaConfig(BaseModel):
    name: str
    role: str
    backstory: str
    ocean_traits: OCEANTraits
    communication_style: CommunicationStyle
    prompt_template: str
```

```python
# src/personas/service.py
from notion_client import Client
from fastapi import HTTPException
from .models import PersonaConfig, OCEANTraits, CommunicationStyle
import time
import logging

logger = logging.getLogger(__name__)

class PersonaService:
    def __init__(self, notion_client: Client, database_id: str):
        self.notion_client = notion_client
        self.database_id = database_id
        self.persona_cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # 5 minutes
    
    async def get_persona(self, name: str) -> PersonaConfig:
        """Get persona configuration from Notion"""
        # Check cache first
        current_time = time.time()
        if name in self.persona_cache and self.cache_expiry.get(name, 0) > current_time:
            logger.debug(f"Returning cached persona: {name}")
            return self.persona_cache[name]
        
        # Query Notion
        logger.info(f"Fetching persona from Notion: {name}")
        try:
            results = self.notion_client.databases.query(
                database_id=self.database_id,
                filter={"property": "Name", "title": {"equals": name}}
            )
            
            if not results["results"]:
                logger.warning(f"Persona not found: {name}")
                raise HTTPException(status_code=404, detail=f"Persona {name} not found")
            
            page = results["results"][0]
            properties = page["properties"]
            
            # Extract properties
            persona_config = PersonaConfig(
                name=properties["Name"]["title"][0]["text"]["content"],
                role=properties["Role"]["rich_text"][0]["text"]["content"],
                backstory=properties["Backstory"]["rich_text"][0]["text"]["content"],
                ocean_traits=OCEANTraits(
                    openness=properties["Openness"]["number"],
                    conscientiousness=properties["Conscientiousness"]["number"],
                    extraversion=properties["Extraversion"]["number"],
                    agreeableness=properties["Agreeableness"]["number"],
                    neuroticism=properties["Neuroticism"]["number"]
                ),
                communication_style=CommunicationStyle(
                    humor=properties["Humor"]["number"],
                    formality=properties["Formality"]["number"]
                ),
                prompt_template=properties["Prompt Template"]["rich_text"][0]["text"]["content"]
            )
            
            # Update cache
            self.persona_cache[name] = persona_config
            self.cache_expiry[name] = current_time + self.cache_duration
            
            return persona_config
            
        except Exception as e:
            logger.error(f"Error fetching persona {name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching persona: {str(e)}")
```

**Deliverable:** Functional API endpoints for persona configuration retrieval.

### 2.2 Dynamic Persona Manager

**Objective:** Create a component to manage persona configurations and generate prompts.

**Tasks:**
- [ ] Implement the DynamicPersonaManager class
- [ ] Add methods for prompt generation based on persona traits
- [ ] Create context generation based on OCEAN traits
- [ ] Implement communication style adaptation

**Implementation:**
```python
# src/personas/manager.py
from typing import Dict, Any, Optional, List
import logging
from .models import PersonaConfig, OCEANTraits, CommunicationStyle
from .service import PersonaService

logger = logging.getLogger(__name__)

class DynamicPersonaManager:
    def __init__(self, persona_service: PersonaService):
        self.persona_service = persona_service
    
    async def get_persona(self, name: str) -> Optional[PersonaConfig]:
        """Get a specific persona configuration"""
        try:
            return await self.persona_service.get_persona(name)
        except Exception as e:
            logger.error(f"Error getting persona {name}: {str(e)}")
            return None
    
    async def get_prompt(self, name: str, context: Dict[str, Any]) -> str:
        """Generate a prompt for a specific persona with context"""
        persona = await self.get_persona(name)
        if not persona:
            logger.error(f"Persona {name} not found for prompt generation")
            raise ValueError(f"Persona {name} not found")
        
        logger.debug(f"Generating prompt for {name} with context keys: {list(context.keys())}")
        
        # Start with the template
        prompt = persona.prompt_template
        
        # Replace placeholders with context values
        for key, value in context.items():
            placeholder = f"[{key}]"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        
        # Add personality context based on OCEAN traits
        ocean_context = self._generate_ocean_context(persona.ocean_traits)
        communication_context = self._generate_communication_context(persona.communication_style)
        
        # Combine everything into a final prompt
        final_prompt = f"""
{persona.backstory}

Your personality traits:
{ocean_context}

Your communication style:
{communication_context}

Task:
{prompt}
"""
        return final_prompt
    
    def _generate_ocean_context(self, traits: OCEANTraits) -> str:
        """Generate context description based on OCEAN traits"""
        contexts = []
        
        if traits.openness > 0.7:
            contexts.append("You're highly creative and curious, open to new ideas and experiences.")
        elif traits.openness < 0.3:
            contexts.append("You're practical and conventional, preferring familiar routines and concrete ideas.")
        
        if traits.conscientiousness > 0.7:
            contexts.append("You're highly organized, detail-oriented, and focused on goals and duties.")
        elif traits.conscientiousness < 0.3:
            contexts.append("You're flexible, spontaneous, and prefer to keep options open rather than plan everything.")
        
        if traits.extraversion > 0.7:
            contexts.append("You're outgoing, energetic, and draw energy from social interaction.")
        elif traits.extraversion < 0.3:
            contexts.append("You're reserved, thoughtful, and prefer deeper one-on-one conversations.")
        
        if traits.agreeableness > 0.7:
            contexts.append("You're compassionate, cooperative, and prioritize harmony in relationships.")
        elif traits.agreeableness < 0.3:
            contexts.append("You're direct, challenging, and prioritize truth over tact.")
        
        if traits.neuroticism > 0.7:
            contexts.append("You're sensitive, emotionally reactive, and experience emotions intensely.")
        elif traits.neuroticism < 0.3:
            contexts.append("You're emotionally stable, calm under pressure, and rarely flustered.")
        
        return "\n".join(contexts)
    
    def _generate_communication_context(self, style: CommunicationStyle) -> str:
        """Generate context description based on communication style"""
        contexts = []
        
        if style.humor > 0.7:
            contexts.append("You frequently use humor and wit in your communication.")
        elif style.humor < 0.3:
            contexts.append("You're generally serious and straightforward in your communication.")
        
        if style.formality > 0.7:
            contexts.append("You communicate in a formal, professional manner.")
        elif style.formality < 0.3:
            contexts.append("You communicate in a casual, conversational tone.")
        
        return "\n".join(contexts)
```

**Deliverable:** Functional DynamicPersonaManager component.

## Phase 3: Orchestrator Enhancement (Weeks 4-5)

### 3.1 Enhanced Orchestrator Implementation

**Objective:** Update orchestrator implementations to leverage persona configurations.

**Tasks:**
- [ ] Refactor existing orchestrator code to use DynamicPersonaManager
- [ ] Implement persona-specific decision making
- [ ] Add memory systems for persona continuity
- [ ] Create consistent communication styles

**Implementation:**
```python
# src/personas/orchestrator.py
from typing import Dict, Any, List, Optional
import logging
from .manager import DynamicPersonaManager
from .models import PersonaConfig

logger = logging.getLogger(__name__)

class EnhancedOrchestrator:
    def __init__(self, name: str, persona_manager: DynamicPersonaManager, llm_service):
        self.name = name
        self.persona_manager = persona_manager
        self.llm_service = llm_service
        self.memory = []  # Simplified memory for this example
        logger.info(f"Initialized enhanced orchestrator: {name}")
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task according to this orchestrator's persona"""
        logger.info(f"Orchestrator {self.name} processing task: {task.get('id', 'unknown')}")
        
        # Get persona configuration
        persona = await self.persona_manager.get_persona(self.name)
        if not persona:
            logger.error(f"Persona configuration for {self.name} not found")
            raise ValueError(f"Persona configuration for {self.name} not found")
        
        # Prepare context for prompt
        context = {
            "task": task.get("description", ""),
            "domain": task.get("domain", ""),
            "priority": task.get("priority", "medium"),
            "historical_decisions": await self._get_relevant_memories(task),
            "client_history": task.get("client_history", "")
        }
        
        # Generate persona-specific prompt
        prompt = await self.persona_manager.get_prompt(self.name, context)
        
        # Send to LLM service
        logger.debug(f"Sending prompt to LLM for {self.name}")
        response = await self.llm_service.generate_response(prompt)
        
        # Store in memory
        await self._store_in_memory(task, response)
        
        return {
            "task_id": task.get("id"),
            "response": response,
            "orchestrator": self.name,
            "status": "completed"
        }
    
    async def _get_relevant_memories(self, task: Dict[str, Any]) -> str:
        """Get relevant memories for this task"""
        # In a real implementation, this would query a vector database
        # For simplicity, we'll just return the last 2 memories as a string
        relevant_memories = self.memory[-2:] if len(self.memory) > 1 else self.memory
        return "\n".join([f"- {memory['task']}: {memory['decision']}" for memory in relevant_memories])
    
    async def _store_in_memory(self, task: Dict[str, Any], response: str):
        """Store task and response in memory"""
        import datetime
        
        memory_entry = {
            "task": task.get("description", ""),
            "decision": response[:100] + "..." if len(response) > 100 else response,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.memory.append(memory_entry)
        logger.debug(f"Added memory for {self.name}: {memory_entry['task'][:30]}...")
        
        # Limit memory size
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
```

**Deliverable:** Enhanced orchestrators with persona-driven behavior.

### 3.2 LLM Integration

**Objective:** Create a service to handle LLM interactions for orchestrators.

**Tasks:**
- [ ] Implement LLM service with appropriate provider
- [ ] Add response generation based on prompts
- [ ] Implement error handling and retries
- [ ] Add logging and monitoring

**Implementation:**
```python
# src/llm/service.py
import os
import logging
import httpx
import asyncio
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM based on the prompt"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"LLM API error: {response.status_code} - {response.text}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                        else:
                            return f"Error generating response: {response.status_code}"
            
            except Exception as e:
                logger.error(f"LLM request error: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    return f"Error generating response: {str(e)}"
        
        return "Unable to generate response after multiple attempts."
```

**Deliverable:** Functional LLM service for orchestrator responses.

## Phase 4: CrewAI Integration (Weeks 6-7)

### 4.1 Orchestrated Crew Manager

**Objective:** Enhance CrewAI integration with persona-driven orchestration.

**Tasks:**
- [ ] Implement OrchestratedCrewManager
- [ ] Add persona-influenced agent creation
- [ ] Create domain-specific team assembly
- [ ] Implement orchestrator review of crew results

**Implementation:**
```python
# src/crews/manager.py
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any
import logging
from ..personas.manager import DynamicPersonaManager
from ..personas.orchestrator import EnhancedOrchestrator

logger = logging.getLogger(__name__)

class OrchestratedCrewManager:
    def __init__(self, persona_manager: DynamicPersonaManager, orchestrators: Dict[str, EnhancedOrchestrator]):
        self.persona_manager = persona_manager
        self.orchestrators = orchestrators
        logger.info("Initialized OrchestratedCrewManager")
    
    async def create_agent(self, role: str, domain: str, seniority: str = "mid") -> Agent:
        """Create a CrewAI agent with appropriate tools and capabilities"""
        logger.info(f"Creating agent: {role} in {domain} domain with {seniority} seniority")
        
        # Define base tools available to all agents
        base_tools = ["notion_reader", "notion_writer"]
        
        # Add domain-specific tools
        domain_tools = {
            "sales": ["crm_tool", "email_generator", "pitch_creator"],
            "research": ["web_search", "document_analyzer", "data_extractor"],
            "content": ["content_generator", "grammar_checker", "plagiarism_detector"],
            "project": ["task_tracker", "timeline_generator", "resource_allocator"],
            "data": ["data_processor", "chart_generator", "insight_extractor"]
        }
        
        tools = base_tools + domain_tools.get(domain, [])
        
        # Get personality traits from orchestrator
        orchestrator_name = self._get_orchestrator_for_domain(domain)
        persona = await self.persona_manager.get_persona(orchestrator_name)
        
        # Define agent backstory based on domain, seniority, and orchestrator influence
        backstory = f"You are a {seniority} level specialist in {domain}, working under the guidance of {orchestrator_name}."
        if orchestrator_name == "Cherry":
            backstory += " You value strategic thinking and efficiency."
        elif orchestrator_name == "Sophia":
            backstory += " You appreciate thorough research and data-driven decisions."
        elif orchestrator_name == "Karen":
            backstory += " You excel at building relationships and persuasive communication."
        
        # Create the agent
        agent = Agent(
            role=f"{seniority.capitalize()} {domain.capitalize()} Specialist",
            goal=f"Provide expert {domain} services and collaborate effectively",
            backstory=backstory,
            tools=tools,
            verbose=True,
            allow_delegation=(seniority in ["mid", "senior"])
        )
        
        return agent
    
    def _get_orchestrator_for_domain(self, domain: str) -> str:
        """Determine which orchestrator should handle this domain"""
        domain_mapping = {
            "sales": "Karen",
            "marketing": "Karen",
            "project": "Karen",
            "research": "Sophia",
            "data": "Sophia",
            "content": "Sophia"
        }
        
        # Default to Cherry for unknown domains
        return domain_mapping.get(domain, "Cherry")
    
    async def assemble_crew(self, task_description: str, domain: str, complexity: str = "medium") -> Dict[str, Any]:
        """Assemble and execute a crew based on task requirements"""
        logger.info(f"Assembling crew for task in {domain} domain with {complexity} complexity")
        
        # Determine team composition based on complexity
        agents = []
        tasks = []
        
        if complexity == "low":
            # Simple task, single agent
            agent = await self.create_agent(role="Specialist", domain=domain, seniority="mid")
            agents.append(agent)
            
            task = Task(
                description=task_description,
                agent=agent
            )
            tasks.append(task)
            
        elif complexity == "medium":
            # Medium complexity, 2-3 agents
            lead_agent = await self.create_agent(role="Lead", domain=domain, seniority="senior")
            support_agent = await self.create_agent(role="Support", domain=domain, seniority="mid")
            
            agents = [lead_agent, support_agent]
            
            # Create tasks with appropriate delegation
            lead_task = Task(
                description=f"Lead and coordinate completion of: {task_description}",
                agent=lead_agent
            )
            
            support_task = Task(
                description=f"Support the lead in completing: {task_description}",
                agent=support_agent
            )
            
            tasks = [lead_task, support_task]
            
        else:  # high complexity
            # Complex task, cross-functional team
            lead_agent = await self.create_agent(role="Lead", domain=domain, seniority="senior")
            domain_agent = await self.create_agent(role="Domain Expert", domain=domain, seniority="mid")
            
            # Determine complementary domain
            complementary_domains = {
                "sales": "marketing",
                "research": "data",
                "content": "research",
                "project": "content",
                "data": "research"
            }
            
            support_domain = complementary_domains.get(domain, "research")
            support_agent = await self.create_agent(role="Support", domain=support_domain, seniority="mid")
            
            agents = [lead_agent, domain_agent, support_agent]
            
            # Create tasks with appropriate delegation
            lead_task = Task(
                description=f"Lead and coordinate completion of: {task_description}",
                agent=lead_agent
            )
            
            domain_task = Task(
                description=f"Provide domain expertise for: {task_description}",
                agent=domain_agent
            )
            
            support_task = Task(
                description=f"Provide {support_domain} support for: {task_description}",
                agent=support_agent
            )
            
            tasks = [lead_task, domain_task, support_task]
        
        # Get the orchestrator for this domain
        orchestrator_name = self._get_orchestrator_for_domain(domain)
        orchestrator = self.orchestrators[orchestrator_name]
        
        # Have the orchestrator review the crew's plan
        logger.info(f"Getting {orchestrator_name} to review crew plan")
        orchestrator_review = await orchestrator.process_task({
            "description": f"Review and approve crew plan for: {task_description}",
            "domain": domain,
            "complexity": complexity
        })
        
        # Create and run the crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential
        )
        
        # Execute the crew
        logger.info(f"Executing crew for task in {domain} domain")
        result = crew.kickoff()
        
        # Have the orchestrator review the results
        logger.info(f"Getting {orchestrator_name} to review crew results")
        orchestrator_final_review = await orchestrator.process_task({
            "description": f"Review crew results for: {task_description}",
            "domain": domain,
            "complexity": complexity,
            "crew_result": result
        })
        
        return {
            "task": task_description,
            "domain": domain,
            "complexity": complexity,
            "orchestrator": orchestrator_name,
            "crew_result": result,
            "orchestrator_review": orchestrator_review,
            "orchestrator_final_review": orchestrator_final_review
        }
```

**Deliverable:** Functional OrchestratedCrewManager for persona-driven team assembly.

### 4.2 API Integration

**Objective:** Create API endpoints for orchestrated crew operations.

**Tasks:**
- [ ] Implement FastAPI endpoints for crew operations
- [ ] Add task submission and status checking
- [ ] Implement result retrieval and storage
- [ ] Add error handling and logging

**Implementation:**
```python
# src/api/crew_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
from ..crews.manager import OrchestratedCrewManager
from ..personas.manager import DynamicPersonaManager
from ..personas.orchestrator import EnhancedOrchestrator
from ..llm.service import LLMService
from ..personas.service import PersonaService
from notion_client import Client
import os
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencies
def get_notion_client():
    return Client(auth=os.environ.get("NOTION_API_KEY"))

def get_persona_service(notion_client: Client = Depends(get_notion_client)):
    return PersonaService(notion_client, os.environ.get("NOTION_PERSONAS_DB_ID"))

def get_persona_manager(persona_service: PersonaService = Depends(get_persona_service)):
    return DynamicPersonaManager(persona_service)

def get_llm_service():
    return LLMService()

def get_orchestrators(
    persona_manager: DynamicPersonaManager = Depends(get_persona_manager),
    llm_service: LLMService = Depends(get_llm_service)
):
    return {
        "Cherry": EnhancedOrchestrator("Cherry", persona_manager, llm_service),
        "Sophia": EnhancedOrchestrator("Sophia", persona_manager, llm_service),
        "Karen": EnhancedOrchestrator("Karen", persona_manager, llm_service)
    }

def get_crew_manager(
    persona_manager: DynamicPersonaManager = Depends(get_persona_manager),
    orchestrators: Dict[str, EnhancedOrchestrator] = Depends(get_orchestrators)
):
    return OrchestratedCrewManager(persona_manager, orchestrators)

# Task storage (in-memory for this example)
task_store = {}

# Endpoints
@router.post("/tasks", status_code=202)
async def create_task(
    task: Dict[str, Any],
    background_tasks: BackgroundTasks,
    crew_manager: OrchestratedCrewManager = Depends(get_crew_manager)
):
    """Submit a new task for processing by a crew"""
    task_id = str(uuid.uuid4())
    task["id"] = task_id
    task_store[task_id] = {"status": "pending", "task": task}
    
    # Process task in background
    background_tasks.add_task(process_task, task_id, task, crew_manager)
    
    return {"task_id": task_id, "status": "pending"}

async def process_task(task_id: str, task: Dict[str, Any], crew_manager: OrchestratedCrewManager):
    """Process a task using the crew manager"""
    try:
        logger.info(f"Processing task {task_id}")
        task_store[task_id]["status"] = "processing"
        
        # Assemble and run crew
        result = await crew_manager.assemble_crew(
            task_description=task.get("description", ""),
            domain=task.get("domain", "general"),
            complexity=task.get("complexity", "medium")
        )
        
        # Store result
        task_store[task_id]["status"] = "completed"
        task_store[task_id]["result"] = result
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        task_store[task_id]["status"] = "failed"
        task_store[task_id]["error"] = str(e)

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task"""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task_store[task_id]["status"],
        "result": task_store[task_id].get("result") if task_store[task_id]["status"] == "completed" else None,
        "error": task_store[task_id].get("error") if task_store[task_id]["status"] == "failed" else None
    }

@router.get("/tasks")
async def list_tasks():
    """List all tasks"""
    return [
        {
            "task_id": task_id,
            "status": info["status"],
            "description": info["task"].get("description", ""),
            "domain": info["task"].get("domain", ""),
            "complexity": info["task"].get("complexity", "")
        }
        for task_id, info in task_store.items()
    ]
```

**Deliverable:** Functional API endpoints for orchestrated crew operations.

## Phase 5: Testing and Refinement (Week 8)

### 5.1 Integration Testing

**Objective:** Test the complete integration of persona-driven orchestration.

**Tasks:**
- [ ] Create test scenarios for each orchestrator
- [ ] Test persona-specific responses
- [ ] Verify crew assembly and execution
- [ ] Test API endpoints

**Implementation:**
```python
# tests/test_persona_integration.py
import pytest
import asyncio
from unittest.mock import MagicMock, patch
import os
import json

# Mock Notion client and responses
@pytest.fixture
def mock_notion_client():
    with patch("notion_client.Client") as mock_client:
        # Set up mock responses for database queries
        mock_client.return_value.databases.query.return_value = {
            "results": [
                {
                    "id": "page_id",
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Cherry"}}]},
                        "Role": {"rich_text": [{"text": {"content": "Queen Bee Orchestrator"}}]},
                        "Backstory": {"rich_text": [{"text": {"content": "You're Cherry, the strategic mastermind running the show."}}]},
                        "Openness": {"number": 0.8},
                        "Conscientiousness": {"number": 0.9},
                        "Extraversion": {"number": 0.5},
                        "Agreeableness": {"number": 0.5},
                        "Neuroticism": {"number": 0.2},
                        "Humor": {"number": 0.4},
                        "Formality": {"number": 0.7},
                        "Prompt Template": {"rich_text": [{"text": {"content": "As Cherry, synthesize [context]."}}]}
                    }
                }
            ]
        }
        yield mock_client.return_value

# Mock LLM service
@pytest.fixture
def mock_llm_service():
    mock_service = MagicMock()
    mock_service.generate_response.return_value = asyncio.Future()
    mock_service.generate_response.return_value.set_result("This is a mock LLM response")
    return mock_service

# Test persona service
@pytest.mark.asyncio
async def test_persona_service(mock_notion_client):
    from src.personas.service import PersonaService
    
    service = PersonaService(mock_notion_client, "database_id")
    persona = await service.get_persona("Cherry")
    
    assert persona.name == "Cherry"
    assert persona.role == "Queen Bee Orchestrator"
    assert persona.ocean_traits.openness == 0.8
    assert persona.communication_style.humor == 0.4

# Test persona manager
@pytest.mark.asyncio
async def test_persona_manager():
    from src.personas.manager import DynamicPersonaManager
    from src.personas.models import PersonaConfig, OCEANTraits, CommunicationStyle
    
    # Mock persona service
    mock_service = MagicMock()
    mock_service.get_persona.return_value = asyncio.Future()
    mock_service.get_persona.return_value.set_result(
        PersonaConfig(
            name="Cherry",
            role="Queen Bee Orchestrator",
            backstory="You're Cherry, the strategic mastermind running the show.",
            ocean_traits=OCEANTraits(
                openness=0.8,
                conscientiousness=0.9,
                extraversion=0.5,
                agreeableness=0.5,
                neuroticism=0.2
            ),
            communication_style=CommunicationStyle(
                humor=0.4,
                formality=0.7
            ),
            prompt_template="As Cherry, synthesize [context]."
        )
    )
    
    manager = DynamicPersonaManager(mock_service)
    prompt = await manager.get_prompt("Cherry", {"context": "test context"})
    
    assert "You're Cherry, the strategic mastermind" in prompt
    assert "test context" in prompt
    assert "You're highly creative and curious" in prompt

# Test enhanced orchestrator
@pytest.mark.asyncio
async def test_enhanced_orchestrator(mock_llm_service):
    from src.personas.orchestrator import EnhancedOrchestrator
    from src.personas.manager import DynamicPersonaManager
    
    # Mock persona manager
    mock_manager = MagicMock()
    mock_manager.get_persona.return_value = asyncio.Future()
    mock_manager.get_persona.return_value.set_result(MagicMock())
    
    mock_manager.get_prompt.return_value = asyncio.Future()
    mock_manager.get_prompt.return_value.set_result("Test prompt")
    
    orchestrator = EnhancedOrchestrator("Cherry", mock_manager, mock_llm_service)
    result = await orchestrator.process_task({"description": "Test task"})
    
    assert result["orchestrator"] == "Cherry"
    assert result["status"] == "completed"
    assert result["response"] == "This is a mock LLM response"
```

**Deliverable:** Comprehensive test suite for persona integration.

### 5.2 Performance Optimization

**Objective:** Optimize the performance of persona-driven orchestration.

**Tasks:**
- [ ] Implement more efficient caching
- [ ] Optimize Notion API calls
- [ ] Add batch processing for crew operations
- [ ] Implement performance monitoring

**Implementation:**
```python
# src/utils/cache.py
import time
import logging
import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar('T')

class AsyncCache(Generic[T]):
    """Efficient async cache with TTL"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.lock = asyncio.Lock()
        logger.info(f"Initialized AsyncCache with TTL of {ttl_seconds} seconds")
    
    async def get(self, key: str, fetch_func: Callable[[], Awaitable[T]]) -> T:
        """Get item from cache or fetch it if missing/expired"""
        current_time = time.time()
        
        # Check if in cache and not expired
        if key in self.cache and self.cache[key]["expiry"] > current_time:
            logger.debug(f"Cache hit for key: {key}")
            return self.cache[key]["value"]
        
        # Need to fetch - use lock to prevent multiple fetches
        async with self.lock:
            # Check again in case another task fetched while waiting for lock
            if key in self.cache and self.cache[key]["expiry"] > current_time:
                logger.debug(f"Cache hit after lock for key: {key}")
                return self.cache[key]["value"]
            
            # Fetch and store
            logger.debug(f"Cache miss for key: {key}, fetching...")
            value = await fetch_func()
            
            self.cache[key] = {
                "value": value,
                "expiry": current_time + self.ttl_seconds
            }
            
            return value
    
    async def invalidate(self, key: str) -> None:
        """Invalidate a specific cache entry"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Invalidated cache for key: {key}")
    
    async def clear(self) -> None:
        """Clear the entire cache"""
        async with self.lock:
            self.cache.clear()
            logger.debug("Cleared entire cache")
    
    async def cleanup(self) -> int:
        """Remove expired entries, return count of removed items"""
        current_time = time.time()
        count = 0
        
        async with self.lock:
            expired_keys = [k for k, v in self.cache.items() if v["expiry"] <= current_time]
            for key in expired_keys:
                del self.cache[key]
                count += 1
            
            if count > 0:
                logger.debug(f"Cleaned up {count} expired cache entries")
            
            return count
```

**Deliverable:** Optimized performance for persona-driven orchestration.

## Phase 6: Admin Interface Preparation (Weeks 9-10)

### 6.1 API Endpoints for Admin

**Objective:** Create API endpoints for admin interface integration.

**Tasks:**
- [ ] Implement CRUD operations for personas
- [ ] Add endpoints for persona configuration
- [ ] Create endpoints for orchestrator monitoring
- [ ] Implement endpoints for crew management

**Implementation:**
```python
# src/api/admin_endpoints.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
from ..personas.service import PersonaService
from notion_client import Client
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependencies
def get_notion_client():
    return Client(auth=os.environ.get("NOTION_API_KEY"))

def get_persona_service(notion_client: Client = Depends(get_notion_client)):
    return PersonaService(notion_client, os.environ.get("NOTION_PERSONAS_DB_ID"))

# Endpoints for persona management
@router.get("/admin/personas")
async def list_personas(service: PersonaService = Depends(get_persona_service)):
    """List all personas"""
    results = service.notion_client.databases.query(database_id=service.database_id)
    return [
        {
            "id": page["id"],
            "name": page["properties"]["Name"]["title"][0]["text"]["content"],
            "role": page["properties"]["Role"]["rich_text"][0]["text"]["content"]
        }
        for page in results["results"]
    ]

@router.get("/admin/personas/{name}")
async def get_persona(name: str, service: PersonaService = Depends(get_persona_service)):
    """Get persona details"""
    return await service.get_persona(name)

@router.put("/admin/personas/{name}")
async def update_persona(
    name: str,
    persona_data: Dict[str, Any],
    service: PersonaService = Depends(get_persona_service)
):
    """Update persona configuration"""
    # Find the persona page
    results = service.notion_client.databases.query(
        database_id=service.database_id,
        filter={"property": "Name", "title": {"equals": name}}
    )
    
    if not results["results"]:
        raise HTTPException(status_code=404, detail=f"Persona {name} not found")
    
    page_id = results["results"][0]["id"]
    
    # Prepare properties for update
    properties = {}
    
    if "role" in persona_data:
        properties["Role"] = {"rich_text": [{"text": {"content": persona_data["role"]}}]}
    
    if "backstory" in persona_data:
        properties["Backstory"] = {"rich_text": [{"text": {"content": persona_data["backstory"]}}]}
    
    if "ocean_traits" in persona_data:
        traits = persona_data["ocean_traits"]
        if "openness" in traits:
            properties["Openness"] = {"number": traits["openness"]}
        if "conscientiousness" in traits:
            properties["Conscientiousness"] = {"number": traits["conscientiousness"]}
        if "extraversion" in traits:
            properties["Extraversion"] = {"number": traits["extraversion"]}
        if "agreeableness" in traits:
            properties["Agreeableness"] = {"number": traits["agreeableness"]}
        if "neuroticism" in traits:
            properties["Neuroticism"] = {"number": traits["neuroticism"]}
    
    if "communication_style" in persona_data:
        style = persona_data["communication_style"]
        if "humor" in style:
            properties["Humor"] = {"number": style["humor"]}
        if "formality" in style:
            properties["Formality"] = {"number": style["formality"]}
    
    if "prompt_template" in persona_data:
        properties["Prompt Template"] = {"rich_text": [{"text": {"content": persona_data["prompt_template"]}}]}
    
    # Update the page
    service.notion_client.pages.update(
        page_id=page_id,
        properties=properties
    )
    
    # Invalidate cache
    if hasattr(service, "persona_cache") and name in service.persona_cache:
        del service.persona_cache[name]
    
    return {"status": "updated", "name": name}

@router.post("/admin/personas")
async def create_persona(
    persona_data: Dict[str, Any],
    service: PersonaService = Depends(get_persona_service)
):
    """Create a new persona"""
    # Check if persona already exists
    name = persona_data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Persona name is required")
    
    results = service.notion_client.databases.query(
        database_id=service.database_id,
        filter={"property": "Name", "title": {"equals": name}}
    )
    
    if results["results"]:
        raise HTTPException(status_code=409, detail=f"Persona {name} already exists")
    
    # Prepare properties
    properties = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Role": {"rich_text": [{"text": {"content": persona_data.get("role", "")}}]},
        "Backstory": {"rich_text": [{"text": {"content": persona_data.get("backstory", "")}}]},
        "Prompt Template": {"rich_text": [{"text": {"content": persona_data.get("prompt_template", "")}}]}
    }
    
    # Add OCEAN traits
    traits = persona_data.get("ocean_traits", {})
    properties["Openness"] = {"number": traits.get("openness", 0.5)}
    properties["Conscientiousness"] = {"number": traits.get("conscientiousness", 0.5)}
    properties["Extraversion"] = {"number": traits.get("extraversion", 0.5)}
    properties["Agreeableness"] = {"number": traits.get("agreeableness", 0.5)}
    properties["Neuroticism"] = {"number": traits.get("neuroticism", 0.5)}
    
    # Add communication style
    style = persona_data.get("communication_style", {})
    properties["Humor"] = {"number": style.get("humor", 0.5)}
    properties["Formality"] = {"number": style.get("formality", 0.5)}
    
    # Create the page
    response = service.notion_client.pages.create(
        parent={"database_id": service.database_id},
        properties=properties
    )
    
    return {"status": "created", "id": response["id"], "name": name}

@router.delete("/admin/personas/{name}")
async def delete_persona(
    name: str,
    service: PersonaService = Depends(get_persona_service)
):
    """Delete a persona"""
    # Find the persona page
    results = service.notion_client.databases.query(
        database_id=service.database_id,
        filter={"property": "Name", "title": {"equals": name}}
    )
    
    if not results["results"]:
        raise HTTPException(status_code=404, detail=f"Persona {name} not found")
    
    page_id = results["results"][0]["id"]
    
    # Archive the page (Notion's way of deleting)
    service.notion_client.pages.update(
        page_id=page_id,
        archived=True
    )
    
    # Invalidate cache
    if hasattr(service, "persona_cache") and name in service.persona_cache:
        del service.persona_cache[name]
    
    return {"status": "deleted", "name": name}
```

**Deliverable:** API endpoints for admin interface integration.

### 6.2 Data Export for Migration

**Objective:** Create utilities for exporting persona data for future migration.

**Tasks:**
- [ ] Implement data export to JSON
- [ ] Create database schema for future migration
- [ ] Add documentation for migration process
- [ ] Create sample migration script

**Implementation:**
```python
# src/utils/export.py
import json
import os
import logging
from typing import Dict, Any, List
from notion_client import Client

logger = logging.getLogger(__name__)

class PersonaExporter:
    def __init__(self, notion_client: Client, database_id: str):
        self.notion_client = notion_client
        self.database_id = database_id
    
    async def export_all_personas(self, output_file: str) -> Dict[str, Any]:
        """Export all personas to a JSON file"""
        logger.info(f"Exporting all personas to {output_file}")
        
        # Query all personas
        results = self.notion_client.databases.query(database_id=self.database_id)
        
        # Process each persona
        personas = []
        for page in results["results"]:
            properties = page["properties"]
            
            # Extract persona data
            persona = {
                "id": page["id"],
                "name": properties["Name"]["title"][0]["text"]["content"],
                "role": properties["Role"]["rich_text"][0]["text"]["content"],
                "backstory": properties["Backstory"]["rich_text"][0]["text"]["content"],
                "ocean_traits": {
                    "openness": properties["Openness"]["number"],
                    "conscientiousness": properties["Conscientiousness"]["number"],
                    "extraversion": properties["Extraversion"]["number"],
                    "agreeableness": properties["Agreeableness"]["number"],
                    "neuroticism": properties["Neuroticism"]["number"]
                },
                "communication_style": {
                    "humor": properties["Humor"]["number"],
                    "formality": properties["Formality"]["number"]
                },
                "prompt_template": properties["Prompt Template"]["rich_text"][0]["text"]["content"]
            }
            
            personas.append(persona)
        
        # Create export data
        export_data = {
            "version": "1.0",
            "export_date": datetime.datetime.now().isoformat(),
            "personas": personas
        }
        
        # Write to file
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(personas)} personas to {output_file}")
        
        return {
            "status": "success",
            "file": output_file,
            "count": len(personas)
        }
    
    def generate_sql_schema(self) -> str:
        """Generate SQL schema for personas database"""
        schema = """
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(200) NOT NULL,
    backstory TEXT NOT NULL,
    openness FLOAT NOT NULL,
    conscientiousness FLOAT NOT NULL,
    extraversion FLOAT NOT NULL,
    agreeableness FLOAT NOT NULL,
    neuroticism FLOAT NOT NULL,
    humor FLOAT NOT NULL,
    formality FLOAT NOT NULL,
    prompt_template TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_personas_name ON personas(name);
"""
        return schema
    
    def generate_migration_script(self, json_file: str) -> str:
        """Generate a Python script to migrate data from JSON to SQL"""
        script = f"""
import json
import psycopg2
import os
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    database=os.environ.get("DB_NAME", "orchestra"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "")
)

# Load JSON data
with open("{json_file}", "r") as f:
    data = json.load(f)

# Insert personas
with conn.cursor() as cur:
    for persona in data["personas"]:
        cur.execute('''
            INSERT INTO personas (
                name, role, backstory, 
                openness, conscientiousness, extraversion, agreeableness, neuroticism,
                humor, formality, prompt_template
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                role = EXCLUDED.role,
                backstory = EXCLUDED.backstory,
                openness = EXCLUDED.openness,
                conscientiousness = EXCLUDED.conscientiousness,
                extraversion = EXCLUDED.extraversion,
                agreeableness = EXCLUDED.agreeableness,
                neuroticism = EXCLUDED.neuroticism,
                humor = EXCLUDED.humor,
                formality = EXCLUDED.formality,
                prompt_template = EXCLUDED.prompt_template,
                updated_at = NOW()
        ''', (
            persona["name"],
            persona["role"],
            persona["backstory"],
            persona["ocean_traits"]["openness"],
            persona["ocean_traits"]["conscientiousness"],
            persona["ocean_traits"]["extraversion"],
            persona["ocean_traits"]["agreeableness"],
            persona["ocean_traits"]["neuroticism"],
            persona["communication_style"]["humor"],
            persona["communication_style"]["formality"],
            persona["prompt_template"]
        ))

# Commit changes
conn.commit()
print(f"Migrated {len(data['personas'])} personas to database")
"""
        return script
```

**Deliverable:** Utilities for exporting persona data for future migration.

## Implementation Timeline

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Foundation Setup | Notion database, Environment configuration |
| 2-3 | Core Integration | Persona Service API, Dynamic Persona Manager |
| 4-5 | Orchestrator Enhancement | Enhanced Orchestrators, LLM Integration |
| 6-7 | CrewAI Integration | Orchestrated Crew Manager, API Integration |
| 8 | Testing and Refinement | Integration Tests, Performance Optimization |
| 9-10 | Admin Interface Preparation | Admin API Endpoints, Data Export Utilities |

## Success Metrics

1. **Persona Distinctiveness**
   - Each orchestrator exhibits consistent personality traits
   - Responses reflect OCEAN traits and communication styles
   - Users can distinguish between orchestrators without explicit identification

2. **Integration Performance**
   - Notion API calls optimized with caching
   - Response times under 2 seconds for persona-driven operations
   - Successful handling of concurrent requests

3. **Crew Effectiveness**
   - Crews assembled with appropriate domain expertise
   - Orchestrator reviews provide valuable guidance
   - Task completion rates above 95%

4. **Maintainability**
   - Persona configurations easily updated in Notion
   - Clear separation of concerns in codebase
   - Comprehensive test coverage

## Next Steps After Implementation

1. **User Testing**
   - Conduct user testing to evaluate persona distinctiveness
   - Gather feedback on orchestrator effectiveness
   - Identify areas for improvement

2. **Continuous Improvement**
   - Refine persona traits based on user feedback
   - Enhance prompt templates for better responses
   - Optimize performance based on usage patterns

3. **Admin Interface Development**
   - Develop React-based admin interface
   - Migrate from Notion to dedicated database
   - Implement more advanced persona management features

4. **Advanced Features**
   - Implement persona learning from feedback
   - Add more sophisticated memory systems
   - Develop cross-persona collaboration mechanisms
