# Synthesized Architecture: Notion-Powered Persona Hub for Orchestra AI

## Overview

This document synthesizes the Notion-based persona management approach with our existing Orchestra AI architecture, creating a cohesive system where Cherry, Sophia, and Karen can function as dynamic, lifelike orchestrators with distinct personalities.

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Notion Data Layer                    │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │   Cherry    │   │   Sophia    │   │    Karen    │    │
│  │  Persona    │   │   Persona   │   │   Persona   │    │
│  │ Configuration│   │Configuration│   │Configuration│    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                  Orchestra AI Core                       │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │   Cherry    │   │   Sophia    │   │    Karen    │    │
│  │Orchestrator │   │Orchestrator │   │Orchestrator │    │
│  │    Logic    │   │    Logic    │   │    Logic    │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Dynamic Persona Manager               │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 Domain Supervisors                       │
│                                                         │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│  │    Sales    │   │  Research   │   │   Content   │    │
│  │  Supervisor │   │  Supervisor │   │  Supervisor │    │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│                  AI Agent Teams                          │
│                  (via CrewAI)                           │
└─────────────────────────────────────────────────────────┘
```

## Key Integration Points

### 1. Persona Configuration in Notion

The Notion database serves as the central configuration hub for orchestrator personas, storing:

- **Personality Traits**: OCEAN model parameters (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- **Communication Styles**: Humor and formality levels
- **Backstories**: Rich character definitions that inform behavior
- **Prompt Templates**: Dynamic templates that guide orchestrator responses

This approach allows for:
- Easy updates to persona characteristics without code changes
- Version control of persona configurations
- Collaborative refinement of orchestrator personalities
- Future migration to an admin interface

### 2. Dynamic Persona Manager

A new component in the Orchestra AI core that:

- Fetches persona configurations from Notion in real-time
- Translates OCEAN traits and communication styles into behavior parameters
- Dynamically adjusts prompt templates based on context
- Maintains persona consistency across interactions
- Enables orchestrators to evolve over time based on feedback

### 3. Enhanced Orchestrator Logic

Each orchestrator (Cherry, Sophia, Karen) will have enhanced logic that:

- Incorporates personality traits into decision-making processes
- Applies communication styles to response generation
- Maintains consistent "character" across interactions
- Leverages backstory for contextual understanding
- Uses prompt templates as a foundation for responses

### 4. Integration with Existing Components

The persona-driven approach integrates with:

- **Domain Supervisors**: Orchestrators communicate with supervisors in their distinct styles
- **CrewAI Teams**: Orchestrators assemble and direct teams with personality-consistent approaches
- **Knowledge Graph**: Personality traits influence how knowledge is interpreted and applied
- **Memory Systems**: Persona-specific memories are stored and retrieved with appropriate context

## Technical Implementation

### 1. Notion API Integration

```python
from notion_client import Client
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from functools import lru_cache

# Models
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

# Notion client setup
@lru_cache()
def get_notion_client():
    return Client(auth=os.environ.get("NOTION_API_KEY"))

# FastAPI app
app = FastAPI()

# Persona service
class PersonaService:
    def __init__(self, notion_client: Client):
        self.notion_client = notion_client
        self.database_id = os.environ.get("NOTION_PERSONAS_DB_ID")
        self.persona_cache = {}
        self.cache_expiry = {}
    
    async def get_persona(self, name: str) -> PersonaConfig:
        """Get persona configuration from Notion"""
        # Check cache first (with 5-minute expiry)
        import time
        current_time = time.time()
        if name in self.persona_cache and self.cache_expiry.get(name, 0) > current_time:
            return self.persona_cache[name]
        
        # Query Notion
        results = self.notion_client.databases.query(
            database_id=self.database_id,
            filter={"property": "Name", "title": {"equals": name}}
        )
        
        if not results["results"]:
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
        
        # Update cache with 5-minute expiry
        self.persona_cache[name] = persona_config
        self.cache_expiry[name] = current_time + 300  # 5 minutes
        
        return persona_config

# Dependency
def get_persona_service(notion_client: Client = Depends(get_notion_client)):
    return PersonaService(notion_client)

# Endpoints
@app.get("/personas/{name}", response_model=PersonaConfig)
async def get_persona_config(name: str, service: PersonaService = Depends(get_persona_service)):
    return await service.get_persona(name)

@app.get("/personas", response_model=List[str])
async def list_personas(service: PersonaService = Depends(get_persona_service)):
    results = service.notion_client.databases.query(database_id=service.database_id)
    return [page["properties"]["Name"]["title"][0]["text"]["content"] for page in results["results"]]
```

### 2. Dynamic Persona Manager Implementation

```python
from typing import Dict, Any, Optional, List
import os
import json
from pydantic import BaseModel
import httpx
import asyncio

# Models from previous section (PersonaConfig, OCEANTraits, CommunicationStyle)

class DynamicPersonaManager:
    def __init__(self):
        self.api_base_url = os.environ.get("ORCHESTRA_API_URL", "http://localhost:8000")
        self.personas = {}
        self.last_refresh = 0
        self.refresh_interval = 300  # 5 minutes
    
    async def refresh_personas(self):
        """Refresh all persona configurations from the API"""
        import time
        current_time = time.time()
        
        # Only refresh if interval has passed
        if current_time - self.last_refresh < self.refresh_interval:
            return
        
        async with httpx.AsyncClient() as client:
            # Get list of personas
            response = await client.get(f"{self.api_base_url}/personas")
            persona_names = response.json()
            
            # Get each persona's config
            for name in persona_names:
                persona_response = await client.get(f"{self.api_base_url}/personas/{name}")
                self.personas[name] = PersonaConfig(**persona_response.json())
        
        self.last_refresh = current_time
    
    async def get_persona(self, name: str) -> Optional[PersonaConfig]:
        """Get a specific persona configuration"""
        await self.refresh_personas()
        return self.personas.get(name)
    
    async def get_prompt(self, name: str, context: Dict[str, Any]) -> str:
        """Generate a prompt for a specific persona with context"""
        persona = await self.get_persona(name)
        if not persona:
            raise ValueError(f"Persona {name} not found")
        
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

### 3. Enhanced Orchestrator Implementation

```python
from typing import Dict, Any, List, Optional
import asyncio
from pydantic import BaseModel

# Import from previous sections
# from persona_manager import DynamicPersonaManager, PersonaConfig

class EnhancedOrchestrator:
    def __init__(self, name: str, persona_manager: DynamicPersonaManager):
        self.name = name
        self.persona_manager = persona_manager
        self.memory = []  # Simplified memory for this example
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task according to this orchestrator's persona"""
        # Get persona configuration
        persona = await self.persona_manager.get_persona(self.name)
        if not persona:
            raise ValueError(f"Persona configuration for {self.name} not found")
        
        # Prepare context for prompt
        context = {
            "task": task.get("description", ""),
            "domain": task.get("domain", ""),
            "priority": task.get("priority", "medium"),
            "historical_decisions": self._get_relevant_memories(task),
            "client_history": task.get("client_history", "")
        }
        
        # Generate persona-specific prompt
        prompt = await self.persona_manager.get_prompt(self.name, context)
        
        # Here you would send the prompt to your LLM of choice
        # For this example, we'll simulate a response
        response = self._simulate_llm_response(prompt, persona)
        
        # Store in memory
        self._store_in_memory(task, response)
        
        return {
            "task_id": task.get("id"),
            "response": response,
            "orchestrator": self.name,
            "status": "completed"
        }
    
    def _get_relevant_memories(self, task: Dict[str, Any]) -> str:
        """Get relevant memories for this task"""
        # In a real implementation, this would query a vector database
        # For simplicity, we'll just return the last 2 memories as a string
        relevant_memories = self.memory[-2:] if len(self.memory) > 1 else self.memory
        return "\n".join([f"- {memory['task']}: {memory['decision']}" for memory in relevant_memories])
    
    def _store_in_memory(self, task: Dict[str, Any], response: str):
        """Store task and response in memory"""
        self.memory.append({
            "task": task.get("description", ""),
            "decision": response[:100] + "..." if len(response) > 100 else response,
            "timestamp": "2025-06-09T06:00:00Z"  # In real implementation, use actual timestamp
        })
        
        # Limit memory size
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]
    
    def _simulate_llm_response(self, prompt: str, persona: PersonaConfig) -> str:
        """Simulate an LLM response based on persona traits"""
        # This is a placeholder - in a real implementation, you would call your LLM
        
        # Simulate different responses based on persona name
        if self.name == "Cherry":
            return "After analyzing the strategic implications, I recommend proceeding with option B. It aligns with our long-term goals while minimizing short-term disruption. Let's not waste time on option A - it's clearly inferior."
        elif self.name == "Sophia":
            return "Based on my analysis of 15 similar cases, option B has a 78% success rate compared to 43% for option A. The data clearly shows B is superior (p<0.01). I'm excited to see how this plays out!"
        elif self.name == "Karen":
            return "Hey there! I think option B would be perfect for you. It addresses your needs while staying within budget. I've seen this work wonders for clients in similar situations. Let's make it happen!"
        
        return "Generic response - persona not recognized"
```

### 4. Integration with CrewAI

```python
from crewai import Agent, Task, Crew, Process
from typing import List, Dict, Any

# Import from previous sections
# from persona_manager import DynamicPersonaManager
# from enhanced_orchestrator import EnhancedOrchestrator

class OrchestratedCrewManager:
    def __init__(self, persona_manager: DynamicPersonaManager):
        self.persona_manager = persona_manager
        self.orchestrators = {
            "Cherry": EnhancedOrchestrator("Cherry", persona_manager),
            "Sophia": EnhancedOrchestrator("Sophia", persona_manager),
            "Karen": EnhancedOrchestrator("Karen", persona_manager)
        }
    
    async def create_agent(self, role: str, domain: str, seniority: str = "mid") -> Agent:
        """Create a CrewAI agent with appropriate tools and capabilities"""
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
        
        # Create and run the crew
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential
        )
        
        # Get the orchestrator for this domain
        orchestrator_name = self._get_orchestrator_for_domain(domain)
        orchestrator = self.orchestrators[orchestrator_name]
        
        # Have the orchestrator review the crew's plan
        orchestrator_review = await orchestrator.process_task({
            "description": f"Review and approve crew plan for: {task_description}",
            "domain": domain,
            "complexity": complexity
        })
        
        # Execute the crew
        result = crew.kickoff()
        
        # Have the orchestrator review the results
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

## Alignment with Existing Architecture

This implementation aligns with and enhances our existing architecture in several ways:

1. **Maintains Hierarchical Structure**: Preserves Cherry as the "Queen Bee" orchestrator with Sophia and Karen as secondary orchestrators

2. **Enhances Persona Distinctiveness**: Adds rich personality traits and communication styles to make orchestrators more lifelike and dynamic

3. **Leverages Notion Integration**: Builds on existing Notion data layer for seamless integration

4. **Supports Dynamic Teams**: Enhances CrewAI integration with personality-influenced team assembly

5. **Enables Continuous Improvement**: Provides a framework for orchestrators to learn and evolve over time

6. **Maintains Domain Specialization**: Reinforces domain-specific expertise while adding personality dimensions

7. **Simplifies Maintenance**: Centralizes persona configuration in Notion for easy updates

## Benefits of This Approach

1. **Lifelike Orchestrators**: Cherry, Sophia, and Karen become truly distinctive personas with consistent personalities

2. **Flexible Configuration**: Persona traits can be adjusted without code changes

3. **Consistent Behavior**: Orchestrators maintain their unique "voice" across interactions

4. **Improved User Experience**: Interactions feel more natural and engaging

5. **Evolutionary Capability**: Framework supports orchestrators that learn and improve over time

6. **Simplified Development**: Clear separation between persona configuration and implementation logic

7. **Future-Proof Design**: Ready for migration to admin interface when needed
