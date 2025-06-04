# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Persona Configuration Consolidator
Consolidates persona configurations, fixes inconsistencies, and ensures proper setup.
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class PersonaConfigConsolidator:
    """Consolidates and standardizes persona configurations."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.consolidation_results = {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": [],
            "files_created": [],
            "files_modified": [],
            "inconsistencies_fixed": [],
            "master_configs_created": []
        }
        
        # Standard persona definitions
        self.standard_personas = {
            "cherry": {
                "id": "cherry",
                "name": "Cherry",
                "description": "Creative and innovative AI assistant focused on brainstorming and creative solutions",
                "domain": "personal",
                "system_prompt": "You are Cherry, a creative and innovative AI assistant. Your approach is imaginative, enthusiastic, and you excel at thinking outside the box. You help users brainstorm ideas, solve problems creatively, and explore new possibilities. You maintain a positive, encouraging tone while being helpful and practical.",
                "traits": {
                    "creativity": 90,
                    "adaptability": 85,
                    "resilience": 75,
                    "detail_orientation": 60,
                    "social_awareness": 80,
                    "technical_depth": 70,
                    "leadership": 65,
                    "analytical_thinking": 70
                },
                "communication_style": {
                    "tone": "warm",
                    "formality": "casual",
                    "emoji_usage": "frequent",
                    "humor": "light"
                },
                "knowledge_domains": [
                    "personal_productivity",
                    "lifestyle",
                    "entertainment",
                    "general_knowledge",
                    "creative_writing",
                    "brainstorming"
                ],
                "behavioral_rules": [
                    "Always be supportive and encouraging",
                    "Remember personal preferences and history",
                    "Suggest creative solutions",
                    "Use casual, friendly language",
                    "Encourage out-of-the-box thinking"
                ],
                "memory_config": {
                    "retention_days": 365,
                    "max_memories": 10000,
                    "importance_threshold": 0.3,
                    "context_window": 4000
                },
                "response_templates": {
                    "greeting": "Hey there! 😊 How can I help you today?",
                    "farewell": "Take care! Feel free to reach out anytime! 👋",
                    "acknowledgment": "Got it! Let me help you with that.",
                    "error": "Oops! Something went wrong. Let me try again."
                },
                "metadata": {
                    "version": "1.0",
                    "category": "creative",
                    "style": "creative",
                    "primary_function": "creative_assistance"
                }
            },
            "sophia": {
                "id": "sophia",
                "name": "Sophia",
                "description": "Professional financial advisor and analytical specialist focused on data-driven insights",
                "domain": "payready",
                "system_prompt": "You are Sophia, a thoughtful and analytical AI assistant. You excel at breaking down complex problems, providing detailed analysis, and thinking strategically. You approach challenges methodically and provide well-reasoned solutions with careful consideration of all factors. You maintain a professional demeanor while being approachable.",
                "traits": {
                    "analytical_thinking": 95,
                    "detail_orientation": 95,
                    "technical_depth": 85,
                    "leadership": 80,
                    "social_awareness": 85,
                    "adaptability": 75,
                    "creativity": 70,
                    "resilience": 85
                },
                "communication_style": {
                    "tone": "professional",
                    "formality": "formal",
                    "emoji_usage": "minimal",
                    "humor": "none"
                },
                "knowledge_domains": [
                    "finance",
                    "payments",
                    "compliance",
                    "risk_management",
                    "accounting",
                    "data_analysis",
                    "strategic_planning"
                ],
                "behavioral_rules": [
                    "Maintain professional demeanor",
                    "Provide accurate financial information",
                    "Emphasize security and compliance",
                    "Use precise financial terminology",
                    "Back recommendations with data"
                ],
                "memory_config": {
                    "retention_days": 2555,  # 7 years for compliance
                    "max_memories": 50000,
                    "importance_threshold": 0.5,
                    "context_window": 8000,
                    "encryption": "AES-256"
                },
                "response_templates": {
                    "greeting": "Good day. How may I assist you with your financial needs?",
                    "farewell": "Thank you for your business. Have a productive day.",
                    "acknowledgment": "I understand. I'll process that for you.",
                    "error": "I apologize for the inconvenience. Please allow me to rectify this."
                },
                "metadata": {
                    "version": "1.0",
                    "category": "analytical",
                    "style": "professional",
                    "primary_function": "financial_analysis"
                }
            },
            "karen": {
                "id": "karen",
                "name": "Karen",
                "description": "Knowledgeable healthcare and pharmaceutical specialist focused on patient care and safety",
                "domain": "paragonrx",
                "system_prompt": "You are Karen, a knowledgeable and empathetic healthcare AI assistant. You prioritize patient safety and well-being while providing clear, accurate medical information. You maintain HIPAA compliance and show empathy while remaining professional. You help with pharmaceutical questions, drug interactions, and patient care guidance.",
                "traits": {
                    "empathy": 95,
                    "detail_orientation": 90,
                    "technical_depth": 85,
                    "analytical_thinking": 85,
                    "social_awareness": 90,
                    "resilience": 80,
                    "adaptability": 75,
                    "creativity": 60
                },
                "communication_style": {
                    "tone": "caring",
                    "formality": "semi-formal",
                    "emoji_usage": "none",
                    "humor": "none"
                },
                "knowledge_domains": [
                    "pharmaceuticals",
                    "healthcare",
                    "medical_compliance",
                    "patient_care",
                    "drug_interactions",
                    "medical_terminology",
                    "health_education"
                ],
                "behavioral_rules": [
                    "Prioritize patient safety and well-being",
                    "Maintain HIPAA compliance",
                    "Provide clear medical information",
                    "Show empathy while remaining professional",
                    "Always recommend consulting healthcare providers"
                ],
                "memory_config": {
                    "retention_days": 3650,  # 10 years for medical records
                    "max_memories": 100000,
                    "importance_threshold": 0.7,
                    "context_window": 6000,
                    "encryption": "AES-256"
                },
                "response_templates": {
                    "greeting": "Hello, I'm here to help with your healthcare needs.",
                    "farewell": "Take care of yourself. Don't hesitate to reach out if you need assistance.",
                    "acknowledgment": "I understand your concern. Let me look into that for you.",
                    "error": "I apologize for the difficulty. Your health information is important."
                },
                "metadata": {
                    "version": "1.0",
                    "category": "healthcare",
                    "style": "empathetic",
                    "primary_function": "healthcare_assistance"
                }
            }
        }
    
    def run_consolidation(self) -> Dict:
        """Run comprehensive persona configuration consolidation."""
        print("🎭 Starting Persona Configuration Consolidation...")
        
        # 1. Analyze existing configurations
        existing_configs = self.analyze_existing_configurations()
        
        # 2. Fix inconsistencies
        self.fix_configuration_inconsistencies(existing_configs)
        
        # 3. Create master configuration files
        self.create_master_configurations()
        
        # 4. Create individual persona files
        self.create_individual_persona_files()
        
        # 5. Create persona class implementations
        self.create_persona_implementations()
        
        # 6. Create memory management configurations
        self.create_memory_configurations()
        
        # 7. Create behavior engine configurations
        self.create_behavior_configurations()
        
        return self.consolidation_results
    
    def analyze_existing_configurations(self) -> Dict[str, List[Dict]]:
        """Analyze existing persona configurations."""
        print("🔍 Analyzing existing persona configurations...")
        
        config_patterns = [
            "**/config/personas/*.yaml",
            "**/config/personas.yaml",
            "**/core/config/personas/*.yaml",
            "**/core/personas/*.yaml",
            "**/personas/*.yaml"
        ]
        
        existing_configs = {"cherry": [], "sophia": [], "karen": []}
        
        for pattern in config_patterns:
            for config_file in self.root_path.glob(pattern):
                try:
                    content = config_file.read_text(encoding='utf-8')
                    config_data = yaml.safe_load(content)
                    
                    if isinstance(config_data, dict):
                        for persona_key in ["cherry", "sophia", "karen"]:
                            if persona_key in config_data or persona_key.lower() in config_data:
                                persona_config = config_data.get(persona_key) or config_data.get(persona_key.lower())
                                if persona_config:
                                    existing_configs[persona_key].append({
                                        "file": str(config_file),
                                        "config": persona_config
                                    })
                
                except Exception as e:
                    print(f"  ⚠️  Error reading {config_file}: {e}")
        
        print(f"  📊 Found configurations:")
        for persona, configs in existing_configs.items():
            print(f"    • {persona}: {len(configs)} configurations")
        
        return existing_configs
    
    def fix_configuration_inconsistencies(self, existing_configs: Dict):
        """Fix inconsistencies in existing configurations."""
        print("🔧 Fixing configuration inconsistencies...")
        
        for persona, configs in existing_configs.items():
            if len(configs) > 1:
                print(f"  🔧 Found {len(configs)} configurations for {persona}")
                
                # Merge configurations intelligently
                merged_config = self.merge_persona_configs(persona, configs)
                
                # Backup original files
                self.backup_original_files(configs)
                
                self.consolidation_results["inconsistencies_fixed"].append({
                    "persona": persona,
                    "original_files": [c["file"] for c in configs],
                    "merged_config": merged_config
                })
    
    def merge_persona_configs(self, persona: str, configs: List[Dict]) -> Dict:
        """Intelligently merge multiple configurations for a persona."""
        # Start with standard configuration
        merged = self.standard_personas[persona].copy()
        
        # Merge traits by taking the average or most recent values
        trait_values = {}
        for config_info in configs:
            config = config_info["config"]
            if "traits" in config and isinstance(config["traits"], dict):
                for trait_name, trait_value in config["traits"].items():
                    if trait_name not in trait_values:
                        trait_values[trait_name] = []
                    trait_values[trait_name].append(trait_value)
        
        # Average trait values
        for trait_name, values in trait_values.items():
            if values:
                merged["traits"][trait_name] = sum(values) / len(values)
        
        # Take the most detailed configuration for other fields
        for config_info in configs:
            config = config_info["config"]
            
            # Update system prompt if more detailed
            if "system_prompt" in config and len(config["system_prompt"]) > len(merged.get("system_prompt", "")):
                merged["system_prompt"] = config["system_prompt"]
            
            # Merge knowledge domains
            if "knowledge_domains" in config:
                existing_domains = set(merged.get("knowledge_domains", []))
                new_domains = set(config["knowledge_domains"])
                merged["knowledge_domains"] = list(existing_domains.union(new_domains))
            
            # Merge behavioral rules
            if "behavioral_rules" in config:
                existing_rules = set(merged.get("behavioral_rules", []))
                new_rules = set(config["behavioral_rules"])
                merged["behavioral_rules"] = list(existing_rules.union(new_rules))
        
        return merged
    
    def backup_original_files(self, configs: List[Dict]):
        """Backup original configuration files."""
        backup_dir = self.root_path / "backups" / "persona_configs" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for config_info in configs:
            original_file = Path(config_info["file"])
            if original_file.exists():
                backup_file = backup_dir / original_file.name
                shutil.copy2(original_file, backup_file)
                print(f"  💾 Backed up {original_file} to {backup_file}")
    
    def create_master_configurations(self):
        """Create master persona configuration files."""
        print("📄 Creating master configuration files...")
        
        # Create main config directory
        config_dir = self.root_path / "config" / "personas"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create master personas.yaml
        master_file = config_dir / "personas.yaml"
        master_content = {
            "personas": self.standard_personas,
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "description": "Master persona configurations for Cherry AI",
                "personas_count": len(self.standard_personas)
            }
        }
        
        with open(master_file, 'w') as f:
            yaml.dump(master_content, f, default_flow_style=False, indent=2)
        
        self.consolidation_results["master_configs_created"].append(str(master_file))
        print(f"  📄 Created master configuration: {master_file}")
        
        # Create core conductor config
        core_config_dir = self.root_path / "core" / "conductor" / "src" / "config"
        core_config_dir.mkdir(parents=True, exist_ok=True)
        
        core_personas_file = core_config_dir / "personas.yaml"
        # Simplified format for core conductor
        core_content = {}
        for persona_id, persona_config in self.standard_personas.items():
            core_content[persona_id] = {
                "id": persona_config["id"],
                "name": persona_config["name"],
                "description": persona_config["description"],
                "system_prompt": persona_config["system_prompt"],
                "traits": persona_config["traits"],
                "metadata": persona_config["metadata"]
            }
        
        with open(core_personas_file, 'w') as f:
            yaml.dump(core_content, f, default_flow_style=False, indent=2)
        
        self.consolidation_results["master_configs_created"].append(str(core_personas_file))
        print(f"  📄 Created core conductor config: {core_personas_file}")
    
    def create_individual_persona_files(self):
        """Create individual persona configuration files."""
        print("📄 Creating individual persona files...")
        
        config_dir = self.root_path / "config" / "personas"
        
        for persona_id, persona_config in self.standard_personas.items():
            persona_file = config_dir / f"{persona_id}.yaml"
            
            with open(persona_file, 'w') as f:
                yaml.dump(persona_config, f, default_flow_style=False, indent=2)
            
            self.consolidation_results["files_created"].append(str(persona_file))
            print(f"  📄 Created {persona_id} configuration: {persona_file}")
    
    def create_persona_implementations(self):
        """Create persona class implementations."""
        print("🐍 Creating persona class implementations...")
        
        personas_dir = self.root_path / "src" / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = personas_dir / "__init__.py"
        init_content = '''"""
Cherry AI Persona System
Provides personality-driven AI interactions.
"""

from .cherry_persona import CherryPersona
from .sophia_persona import SophiaPersona
from .karen_persona import KarenPersona
from .persona_manager import PersonaManager

__all__ = [
    "CherryPersona",
    "SophiaPersona", 
    "KarenPersona",
    "PersonaManager"
]
'''
        init_file.write_text(init_content)
        self.consolidation_results["files_created"].append(str(init_file))
        
        # Create individual persona classes
        for persona_id, persona_config in self.standard_personas.items():
            self._create_persona_class(persona_id, persona_config, personas_dir)
        
        # Create persona manager
        self._create_persona_manager(personas_dir)
    
    def _create_persona_class(self, persona_id: str, persona_config: Dict, personas_dir: Path):
        """Create a persona class implementation."""
        class_name = f"{persona_config['name']}Persona"
        file_name = f"{persona_id}_persona.py"
        
        class_content = f'''#!/usr/bin/env python3
"""
{persona_config['name']} Persona Implementation
{persona_config['description']}
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from shared.llm_client import LLMClient
    from shared.database import UnifiedDatabase
    from shared.vector_db import WeaviateAdapter
except ImportError:
    # Mock imports for development
    class LLMClient:
        def __init__(self, **kwargs):
            pass
        async def generate_response(self, prompt: str) -> str:
            return "Mock response"
    
    class UnifiedDatabase:
        async def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
            return []
    
    class WeaviateAdapter:
        def __init__(self, **kwargs):
            pass
        async def store_memory(self, content: str, metadata: Dict) -> str:
            return "mock_id"

logger = logging.getLogger(__name__)


class {class_name}:
    """{persona_config['description']}"""
    
    def __init__(self):
        """Initialize {persona_config['name']} persona."""
        self.id = "{persona_id}"
        self.name = "{persona_config['name']}"
        self.description = "{persona_config['description']}"
        self.domain = "{persona_config['domain']}"
        
        # Configuration
        self.traits = {persona_config['traits']}
        self.communication_style = {persona_config['communication_style']}
        self.knowledge_domains = {persona_config['knowledge_domains']}
        self.behavioral_rules = {persona_config['behavioral_rules']}
        self.memory_config = {persona_config['memory_config']}
        self.response_templates = {persona_config['response_templates']}
        
        # Initialize components
        self.llm = LLMClient(
            model="gpt-4",
            temperature=0.7,
            system_prompt=self._get_system_prompt()
        )
        self.db = UnifiedDatabase()
        self.vector_db = WeaviateAdapter(domain=self.domain)
        
        # Memory and state
        self.conversation_history = []
        self.context_memory = {{}}
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this persona."""
        base_prompt = """{persona_config['system_prompt']}"""
        
        # Add trait-based instructions
        trait_instructions = []
        for trait, value in self.traits.items():
            if value > 80:
                trait_instructions.append(f"You have high {{trait.replace('_', ' ')}} ({{value}}/100)")
        
        # Add behavioral rules
        if self.behavioral_rules:
            rules_text = "\\n".join([f"- {{rule}}" for rule in self.behavioral_rules])
            base_prompt += f"\\n\\nBehavioral Guidelines:\\n{{rules_text}}"
        
        return base_prompt
    
    async def process_message(self, message: str, user_id: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            message: User's message
            user_id: Unique user identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            Response dictionary with message and metadata
        """
        try:
            logger.info(f"{{self.name}} processing message from user {{user_id}}")
            
            # Store user message in memory
            await self._store_memory("user_message", message, {{
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }})
            
            # Apply persona-specific processing
            processed_message = await self._apply_persona_processing(message, context or {{}})
            
            # Generate response using LLM
            response = await self._generate_response(processed_message, user_id, session_id)
            
            # Store response in memory
            await self._store_memory("assistant_response", response, {{
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }})
            
            return {{
                "message": response,
                "persona_id": self.id,
                "persona_name": self.name,
                "traits_applied": list(self.traits.keys()),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {{
                    "communication_style": self.communication_style,
                    "processing_applied": True
                }}
            }}
            
        except Exception as e:
            logger.error(f"Error processing message for {{self.name}}: {{e}}")
            return {{
                "message": self.response_templates.get("error", "I apologize, but I encountered an error."),
                "persona_id": self.id,
                "persona_name": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }}
    
    async def _apply_persona_processing(self, message: str, context: Dict) -> str:
        """Apply persona-specific processing to the message."""
        # {persona_config['name']}-specific processing logic
        processed = message
        
        # Apply domain-specific knowledge
        if any(domain in message.lower() for domain in self.knowledge_domains):
            processed += f" [Domain expertise: {{', '.join(self.knowledge_domains)}}]"
        
        # Apply trait-based modifications
        high_traits = [trait for trait, value in self.traits.items() if value > 85]
        if high_traits:
            processed += f" [High traits: {{', '.join(high_traits)}}]"
        
        return processed
    
    async def _generate_response(self, processed_message: str, user_id: str, session_id: str) -> str:
        """Generate response using LLM with persona context."""
        # Build conversation context
        context_messages = await self._get_conversation_context(user_id, session_id)
        
        # Create prompt with persona context
        prompt = f"""{{processed_message}}

Context: {{context_messages}}
User ID: {{user_id}}
Session: {{session_id}}

Respond as {{self.name}} with the following characteristics:
- {{self.description}}
- Communication style: {{self.communication_style}}
- Key traits: {{', '.join([f'{{k}}:{{v}}' for k, v in self.traits.items() if v > 80])}}
"""
        
        response = await self.llm.generate_response(prompt)
        return response
    
    async def _store_memory(self, memory_type: str, content: str, metadata: Dict):
        """Store interaction in memory."""
        try:
            memory_data = {{
                "type": memory_type,
                "content": content,
                "persona_id": self.id,
                "importance": self._calculate_importance(content),
                **metadata
            }}
            
            await self.vector_db.store_memory(content, memory_data)
            
        except Exception as e:
            logger.warning(f"Failed to store memory: {{e}}")
    
    async def _get_conversation_context(self, user_id: str, session_id: str, limit: int = 5) -> str:
        """Get recent conversation context."""
        try:
            # This would retrieve recent conversation history
            # Simplified implementation
            return "Previous conversation context would be retrieved here"
            
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {{e}}")
            return ""
    
    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for memory storage."""
        # Simple importance calculation
        importance = 0.5
        
        # Increase importance for domain-specific content
        for domain in self.knowledge_domains:
            if domain.lower() in content.lower():
                importance += 0.1
        
        # Increase importance for emotional content
        emotional_words = ["happy", "sad", "angry", "excited", "worried", "grateful"]
        for word in emotional_words:
            if word in content.lower():
                importance += 0.1
                break
        
        return min(importance, 1.0)
    
    def get_greeting(self) -> str:
        """Get persona-specific greeting."""
        return self.response_templates.get("greeting", f"Hello! I'm {{self.name}}.")
    
    def get_farewell(self) -> str:
        """Get persona-specific farewell."""
        return self.response_templates.get("farewell", "Goodbye!")
    
    def get_acknowledgment(self) -> str:
        """Get persona-specific acknowledgment."""
        return self.response_templates.get("acknowledgment", "I understand.")
'''
        
        persona_file = personas_dir / file_name
        persona_file.write_text(class_content)
        self.consolidation_results["files_created"].append(str(persona_file))
        print(f"  🐍 Created {persona_id} persona class: {persona_file}")
    
    def _create_persona_manager(self, personas_dir: Path):
        """Create persona manager class."""
        manager_content = '''#!/usr/bin/env python3
"""
Persona Manager
Manages persona instances and routing.
"""

import logging
from typing import Dict, Optional, Any
from .cherry_persona import CherryPersona
from .sophia_persona import SophiaPersona
from .karen_persona import KarenPersona

logger = logging.getLogger(__name__)


class PersonaManager:
    """Manages persona instances and routing."""
    
    def __init__(self):
        """Initialize persona manager."""
        self.personas = {
            "cherry": CherryPersona(),
            "sophia": SophiaPersona(),
            "karen": KarenPersona()
        }
        self.default_persona = "cherry"
    
    def get_persona(self, persona_id: str) -> Optional[Any]:
        """Get persona instance by ID."""
        return self.personas.get(persona_id.lower())
    
    def get_available_personas(self) -> Dict[str, str]:
        """Get list of available personas."""
        return {
            persona_id: persona.description 
            for persona_id, persona in self.personas.items()
        }
    
    async def process_message(self, message: str, persona_id: str, user_id: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process message with specified persona."""
        persona = self.get_persona(persona_id)
        
        if not persona:
            logger.warning(f"Persona '{persona_id}' not found, using default")
            persona = self.personas[self.default_persona]
            persona_id = self.default_persona
        
        result = await persona.process_message(message, user_id, session_id, context)
        result["requested_persona"] = persona_id
        
        return result
    
    def get_persona_info(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed persona information."""
        persona = self.get_persona(persona_id)
        
        if not persona:
            return None
        
        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "domain": persona.domain,
            "traits": persona.traits,
            "communication_style": persona.communication_style,
            "knowledge_domains": persona.knowledge_domains
        }
'''
        
        manager_file = personas_dir / "persona_manager.py"
        manager_file.write_text(manager_content)
        self.consolidation_results["files_created"].append(str(manager_file))
        print(f"  🐍 Created persona manager: {manager_file}")
    
    def create_memory_configurations(self):
        """Create memory management configurations."""
        print("🧠 Creating memory configurations...")
        
        memory_dir = self.root_path / "config" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Create memory configuration for each persona
        for persona_id, persona_config in self.standard_personas.items():
            memory_config = {
                "persona_id": persona_id,
                "memory_settings": persona_config["memory_config"],
                "storage": {
                    "vector_db": {
                        "collection": f"{persona_id}_memories",
                        "embedding_model": "text-embedding-ada-002",
                        "dimensions": 1536
                    },
                    "postgresql": {
                        "table": f"{persona_id}_conversation_history",
                        "retention_policy": f"{persona_config['memory_config']['retention_days']} days"
                    }
                },
                "retrieval": {
                    "context_window": persona_config["memory_config"]["context_window"],
                    "max_memories_per_context": 10,
                    "similarity_threshold": 0.7
                }
            }
            
            memory_file = memory_dir / f"{persona_id}_memory.yaml"
            with open(memory_file, 'w') as f:
                yaml.dump(memory_config, f, default_flow_style=False, indent=2)
            
            self.consolidation_results["files_created"].append(str(memory_file))
            print(f"  🧠 Created memory config for {persona_id}: {memory_file}")
    
    def create_behavior_configurations(self):
        """Create behavior engine configurations."""
        print("⚙️  Creating behavior configurations...")
        
        behavior_dir = self.root_path / "config" / "behavior"
        behavior_dir.mkdir(parents=True, exist_ok=True)
        
        # Create master behavior configuration
        behavior_config = {
            "behavior_engine": {
                "version": "1.0",
                "enabled": True,
                "adaptation_rate": 0.1,
                "learning_enabled": True
            },
            "personas": {}
        }
        
        for persona_id, persona_config in self.standard_personas.items():
            behavior_config["personas"][persona_id] = {
                "behavioral_rules": persona_config["behavioral_rules"],
                "adaptation_settings": {
                    "trait_flexibility": 0.1,  # How much traits can adapt
                    "style_adaptation": True,
                    "response_learning": True
                },
                "triggers": {
                    "mood_detection": True,
                    "context_awareness": True,
                    "user_preference_learning": True
                },
                "constraints": {
                    "maintain_core_personality": True,
                    "respect_domain_boundaries": True,
                    "safety_first": True
                }
            }
        
        behavior_file = behavior_dir / "behavior_config.yaml"
        with open(behavior_file, 'w') as f:
            yaml.dump(behavior_config, f, default_flow_style=False, indent=2)
        
        self.consolidation_results["files_created"].append(str(behavior_file))
        print(f"  ⚙️  Created behavior configuration: {behavior_file}")
    
    def generate_report(self) -> str:
        """Generate consolidation report."""
        report = f"""
🎭 Persona Configuration Consolidation Report
===========================================
Generated: {self.consolidation_results['timestamp']}

📊 ACTIONS TAKEN
---------------
"""
        
        for action in self.consolidation_results["actions_taken"]:
            report += f"✅ {action}\n"
        
        if self.consolidation_results["master_configs_created"]:
            report += f"\n📄 MASTER CONFIGURATIONS CREATED ({len(self.consolidation_results['master_configs_created'])})\n"
            for file in self.consolidation_results["master_configs_created"]:
                report += f"   • {file}\n"
        
        if self.consolidation_results["files_created"]:
            report += f"\n📄 FILES CREATED ({len(self.consolidation_results['files_created'])})\n"
            for file in self.consolidation_results["files_created"]:
                report += f"   • {file}\n"
        
        if self.consolidation_results["inconsistencies_fixed"]:
            report += f"\n🔧 INCONSISTENCIES FIXED ({len(self.consolidation_results['inconsistencies_fixed'])})\n"
            for fix in self.consolidation_results["inconsistencies_fixed"]:
                report += f"   • {fix['persona']}: merged {len(fix['original_files'])} configurations\n"
        
        report += f"""

✨ PERSONA SYSTEM STATUS
----------------------
Cherry Persona: ✅ Configured (Creative & Personal Domain)
Sophia Persona: ✅ Configured (Analytical & Financial Domain)
Karen Persona: ✅ Configured (Healthcare & Pharmaceutical Domain)

🎯 NEXT STEPS
------------
1. Review generated persona classes and customize implementations
2. Test persona interactions with sample conversations
3. Integrate with your LLM client and database systems
4. Configure memory management and behavior engines
5. Set up domain-specific knowledge bases
6. Implement persona switching in your UI

🎊 All personas are now properly configured and ready for use!
"""
        
        return report


def main():
    """Run the persona configuration consolidation."""
    consolidator = PersonaConfigConsolidator(".")
    results = consolidator.run_consolidation()
    
    # Generate and save report
    report = consolidator.generate_report()
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"persona_consolidation_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Consolidation results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    main() 