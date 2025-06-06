"""
Unified Admin Interface - Consolidation of All Admin Systems
Replaces 7 separate admin systems with single comprehensive interface
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import time

# Import core systems
from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.personas.enhanced_personality_engine import PersonalityEngine, PersonalityDimension
from core.coordination.cross_domain_coordinator import CrossDomainCoordinator
from core.voice.voice_integration_framework import VoiceIntegrationFramework
from core.rag.advanced_rag_system import AdvancedRAGSystem
from core.agents.multi_agent_swarm import MultiAgentSwarm

logger = logging.getLogger(__name__)

class AdminOperationType(Enum):
    """Types of admin operations"""
    PERSONA_UPDATE = "persona_update"
    SYSTEM_CONFIG = "system_config"
    MEMORY_MANAGEMENT = "memory_management"
    VOICE_CONFIG = "voice_config"
    COORDINATION_SETUP = "coordination_setup"
    PERFORMANCE_TUNING = "performance_tuning"

@dataclass
class AdminOperation:
    """Admin operation record"""
    operation_id: str
    operation_type: AdminOperationType
    user_id: str
    timestamp: datetime
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

@dataclass
class SystemHealthMetrics:
    """System health and performance metrics"""
    memory_usage_mb: float
    cpu_usage_percent: float
    active_connections: int
    response_time_ms: float
    error_rate_percent: float
    uptime_hours: float
    last_updated: datetime

@dataclass
class PersonaStatus:
    """Persona status information"""
    persona_id: str
    name: str
    is_active: bool
    interaction_count: int
    last_interaction: Optional[datetime]
    personality_health: float
    memory_usage_mb: float
    voice_status: str
    coordination_status: str

class UnifiedAdminInterface:
    """
    Unified Admin Interface - Single source for all admin operations
    Consolidates functionality from all previous admin systems
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.operation_history: List[AdminOperation] = []
        self.system_start_time = datetime.now()
        
        # Core system references (will be injected)
        self.memory_router: Optional[MemoryRouter] = None
        self.personality_engine: Optional[PersonalityEngine] = None
        self.coordination_system: Optional[CrossDomainCoordinator] = None
        self.voice_framework: Optional[VoiceIntegrationFramework] = None
        self.rag_system: Optional[AdvancedRAGSystem] = None
        self.agent_swarm: Optional[MultiAgentSwarm] = None
    
    async def initialize(self, 
                        memory_router: MemoryRouter,
                        personality_engine: PersonalityEngine,
                        coordination_system: CrossDomainCoordinator,
                        voice_framework: VoiceIntegrationFramework,
                        rag_system: AdvancedRAGSystem,
                        agent_swarm: MultiAgentSwarm):
        """Initialize admin interface with core systems"""
        
        self.memory_router = memory_router
        self.personality_engine = personality_engine
        self.coordination_system = coordination_system
        self.voice_framework = voice_framework
        self.rag_system = rag_system
        self.agent_swarm = agent_swarm
        
        self.logger.info("Unified Admin Interface initialized successfully")
    
    # ========================================
    # DASHBOARD & OVERVIEW METHODS
    # ========================================
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        
        try:
            # Get system health metrics
            health_metrics = await self._get_system_health_metrics()
            
            # Get persona statuses
            persona_statuses = await self._get_all_persona_statuses()
            
            # Get recent operations
            recent_operations = self.operation_history[-10:] if self.operation_history else []
            
            # Get coordination matrix status
            coordination_status = await self._get_coordination_status()
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_health": asdict(health_metrics),
                "persona_statuses": [asdict(status) for status in persona_statuses],
                "recent_operations": [asdict(op) for op in recent_operations],
                "coordination_status": coordination_status,
                "performance_metrics": performance_metrics,
                "uptime_hours": (datetime.now() - self.system_start_time).total_seconds() / 3600
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard overview: {e}")
            raise
    
    async def _get_system_health_metrics(self) -> SystemHealthMetrics:
        """Get current system health metrics"""
        
        import psutil
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Calculate response time (simulate)
        start_time = time.time()
        await asyncio.sleep(0.001)  # Minimal operation
        response_time = (time.time() - start_time) * 1000
        
        return SystemHealthMetrics(
            memory_usage_mb=memory.used / 1024 / 1024,
            cpu_usage_percent=cpu_percent,
            active_connections=len(self.operation_history),  # Simplified
            response_time_ms=response_time,
            error_rate_percent=self._calculate_error_rate(),
            uptime_hours=(datetime.now() - self.system_start_time).total_seconds() / 3600,
            last_updated=datetime.now()
        )
    
    async def _get_all_persona_statuses(self) -> List[PersonaStatus]:
        """Get status for all personas"""
        
        personas = ["cherry", "sophia", "karen"]
        statuses = []
        
        for persona_id in personas:
            try:
                # Get persona information
                personality_profile = await self.personality_engine.get_personality_profile(persona_id)
                
                # Get interaction stats from memory
                interaction_stats = await self._get_persona_interaction_stats(persona_id)
                
                # Get voice status
                voice_status = await self._get_persona_voice_status(persona_id)
                
                # Get coordination status
                coordination_status = await self._get_persona_coordination_status(persona_id)
                
                status = PersonaStatus(
                    persona_id=persona_id,
                    name=persona_id.title(),
                    is_active=True,  # Simplified - could check actual activity
                    interaction_count=interaction_stats.get("count", 0),
                    last_interaction=interaction_stats.get("last_interaction"),
                    personality_health=self._calculate_personality_health(personality_profile),
                    memory_usage_mb=interaction_stats.get("memory_usage_mb", 0),
                    voice_status=voice_status,
                    coordination_status=coordination_status
                )
                
                statuses.append(status)
                
            except Exception as e:
                self.logger.error(f"Error getting status for persona {persona_id}: {e}")
                # Add error status
                statuses.append(PersonaStatus(
                    persona_id=persona_id,
                    name=persona_id.title(),
                    is_active=False,
                    interaction_count=0,
                    last_interaction=None,
                    personality_health=0.0,
                    memory_usage_mb=0,
                    voice_status="error",
                    coordination_status="error"
                ))
        
        return statuses
    
    # ========================================
    # PERSONA MANAGEMENT METHODS
    # ========================================
    
    async def update_persona_personality(self, 
                                       persona_id: str, 
                                       dimension: str, 
                                       value: float, 
                                       admin_user: str) -> Dict[str, Any]:
        """Update persona personality dimension"""
        
        operation_id = f"personality_update_{int(time.time())}"
        
        try:
            # Validate inputs
            if not 0.0 <= value <= 1.0:
                raise ValueError("Personality dimension value must be between 0.0 and 1.0")
            
            # Convert dimension string to enum
            try:
                dimension_enum = PersonalityDimension(dimension.lower())
            except ValueError:
                raise ValueError(f"Invalid personality dimension: {dimension}")
            
            # Update personality
            result = await self.personality_engine.update_personality_dimension(
                persona_id, dimension_enum, value
            )
            
            # Record operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.PERSONA_UPDATE,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "persona_id": persona_id,
                    "dimension": dimension,
                    "old_value": result.get("old_value"),
                    "new_value": value
                },
                success=True
            )
            
            self.operation_history.append(operation)
            
            self.logger.info(f"Updated {persona_id} {dimension} to {value} by {admin_user}")
            
            return {
                "success": True,
                "operation_id": operation_id,
                "persona_id": persona_id,
                "dimension": dimension,
                "new_value": value,
                "old_value": result.get("old_value"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failed operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.PERSONA_UPDATE,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "persona_id": persona_id,
                    "dimension": dimension,
                    "attempted_value": value
                },
                success=False,
                error_message=str(e)
            )
            
            self.operation_history.append(operation)
            
            self.logger.error(f"Failed to update {persona_id} personality: {e}")
            
            return {
                "success": False,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_persona_personality_config(self, persona_id: str) -> Dict[str, Any]:
        """Get complete personality configuration for persona"""
        
        try:
            personality_profile = await self.personality_engine.get_personality_profile(persona_id)
            
            return {
                "persona_id": persona_id,
                "personality_dimensions": {
                    dim.value: value for dim, value in personality_profile.dimensions.items()
                },
                "emotional_state": personality_profile.emotional_state.value,
                "communication_style": personality_profile.communication_style,
                "relationship_depth": personality_profile.relationship_depth,
                "voice_characteristics": personality_profile.voice_characteristics,
                "domain_expertise": personality_profile.domain_expertise,
                "privacy_boundaries": personality_profile.privacy_boundaries
            }
            
        except Exception as e:
            self.logger.error(f"Error getting personality config for {persona_id}: {e}")
            raise
    
    # ========================================
    # VOICE MANAGEMENT METHODS
    # ========================================
    
    async def update_voice_settings(self, 
                                  persona_id: str, 
                                  voice_settings: Dict[str, Any], 
                                  admin_user: str) -> Dict[str, Any]:
        """Update voice settings for persona"""
        
        operation_id = f"voice_update_{int(time.time())}"
        
        try:
            # Update voice settings
            result = await self.voice_framework.update_persona_voice_settings(
                persona_id, voice_settings
            )
            
            # Record operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.VOICE_CONFIG,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "persona_id": persona_id,
                    "voice_settings": voice_settings
                },
                success=True
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": True,
                "operation_id": operation_id,
                "persona_id": persona_id,
                "updated_settings": voice_settings,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failed operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.VOICE_CONFIG,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "persona_id": persona_id,
                    "attempted_settings": voice_settings
                },
                success=False,
                error_message=str(e)
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": False,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================
    # COORDINATION MANAGEMENT METHODS
    # ========================================
    
    async def update_coordination_matrix(self, 
                                       coordination_config: Dict[str, Any], 
                                       admin_user: str) -> Dict[str, Any]:
        """Update cross-domain coordination configuration"""
        
        operation_id = f"coordination_update_{int(time.time())}"
        
        try:
            # Update coordination settings
            result = await self.coordination_system.update_coordination_config(coordination_config)
            
            # Record operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.COORDINATION_SETUP,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "coordination_config": coordination_config
                },
                success=True
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": True,
                "operation_id": operation_id,
                "updated_config": coordination_config,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failed operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.COORDINATION_SETUP,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "attempted_config": coordination_config
                },
                success=False,
                error_message=str(e)
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": False,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================
    # MEMORY MANAGEMENT METHODS
    # ========================================
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        
        try:
            # Get memory stats from all layers
            contextual_stats = await self.memory_router.get_layer_statistics(MemoryLayer.CONTEXTUAL)
            episodic_stats = await self.memory_router.get_layer_statistics(MemoryLayer.EPISODIC)
            semantic_stats = await self.memory_router.get_layer_statistics(MemoryLayer.SEMANTIC)
            
            return {
                "total_memories": (
                    contextual_stats.get("count", 0) + 
                    episodic_stats.get("count", 0) + 
                    semantic_stats.get("count", 0)
                ),
                "memory_layers": {
                    "contextual": contextual_stats,
                    "episodic": episodic_stats,
                    "semantic": semantic_stats
                },
                "memory_usage_mb": (
                    contextual_stats.get("size_mb", 0) + 
                    episodic_stats.get("size_mb", 0) + 
                    semantic_stats.get("size_mb", 0)
                ),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {e}")
            raise
    
    async def cleanup_memory(self, 
                           cleanup_config: Dict[str, Any], 
                           admin_user: str) -> Dict[str, Any]:
        """Perform memory cleanup operations"""
        
        operation_id = f"memory_cleanup_{int(time.time())}"
        
        try:
            # Perform memory cleanup
            cleanup_result = await self.memory_router.cleanup_memories(cleanup_config)
            
            # Record operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.MEMORY_MANAGEMENT,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "cleanup_config": cleanup_config,
                    "cleanup_result": cleanup_result
                },
                success=True
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": True,
                "operation_id": operation_id,
                "cleanup_result": cleanup_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failed operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.MEMORY_MANAGEMENT,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "attempted_cleanup": cleanup_config
                },
                success=False,
                error_message=str(e)
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": False,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================
    # SYSTEM MANAGEMENT METHODS
    # ========================================
    
    async def get_system_configuration(self) -> Dict[str, Any]:
        """Get current system configuration"""
        
        try:
            return {
                "personas": {
                    "cherry": await self.get_persona_personality_config("cherry"),
                    "sophia": await self.get_persona_personality_config("sophia"),
                    "karen": await self.get_persona_personality_config("karen")
                },
                "voice_framework": await self.voice_framework.get_configuration(),
                "coordination_system": await self.coordination_system.get_configuration(),
                "rag_system": await self.rag_system.get_configuration(),
                "agent_swarm": await self.agent_swarm.get_configuration(),
                "memory_system": await self.memory_router.get_configuration()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system configuration: {e}")
            raise
    
    async def update_system_configuration(self, 
                                        config_updates: Dict[str, Any], 
                                        admin_user: str) -> Dict[str, Any]:
        """Update system configuration"""
        
        operation_id = f"system_config_{int(time.time())}"
        
        try:
            results = {}
            
            # Update each system component
            for component, config in config_updates.items():
                if component == "personas":
                    for persona_id, persona_config in config.items():
                        result = await self._update_persona_config(persona_id, persona_config)
                        results[f"persona_{persona_id}"] = result
                
                elif component == "voice_framework":
                    result = await self.voice_framework.update_configuration(config)
                    results["voice_framework"] = result
                
                elif component == "coordination_system":
                    result = await self.coordination_system.update_configuration(config)
                    results["coordination_system"] = result
                
                elif component == "rag_system":
                    result = await self.rag_system.update_configuration(config)
                    results["rag_system"] = result
                
                elif component == "agent_swarm":
                    result = await self.agent_swarm.update_configuration(config)
                    results["agent_swarm"] = result
                
                elif component == "memory_system":
                    result = await self.memory_router.update_configuration(config)
                    results["memory_system"] = result
            
            # Record operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.SYSTEM_CONFIG,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "config_updates": config_updates,
                    "results": results
                },
                success=True
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": True,
                "operation_id": operation_id,
                "update_results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Record failed operation
            operation = AdminOperation(
                operation_id=operation_id,
                operation_type=AdminOperationType.SYSTEM_CONFIG,
                user_id=admin_user,
                timestamp=datetime.now(),
                details={
                    "attempted_updates": config_updates
                },
                success=False,
                error_message=str(e)
            )
            
            self.operation_history.append(operation)
            
            return {
                "success": False,
                "operation_id": operation_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate from recent operations"""
        
        if not self.operation_history:
            return 0.0
        
        recent_ops = self.operation_history[-100:]  # Last 100 operations
        failed_ops = sum(1 for op in recent_ops if not op.success)
        
        return (failed_ops / len(recent_ops)) * 100
    
    def _calculate_personality_health(self, personality_profile) -> float:
        """Calculate personality health score"""
        
        # Simple health calculation based on dimension balance
        dimensions = personality_profile.dimensions
        if not dimensions:
            return 0.0
        
        # Check for extreme values (too high or too low)
        extreme_count = sum(1 for value in dimensions.values() if value < 0.1 or value > 0.95)
        health_penalty = (extreme_count / len(dimensions)) * 0.3
        
        # Base health score
        base_health = 1.0 - health_penalty
        
        return max(0.0, min(1.0, base_health))
    
    async def _get_persona_interaction_stats(self, persona_id: str) -> Dict[str, Any]:
        """Get interaction statistics for persona"""
        
        try:
            # Get recent interactions from memory
            interactions = await self.memory_router.get_persona_interactions(
                persona_id, limit=1000
            )
            
            if not interactions:
                return {
                    "count": 0,
                    "last_interaction": None,
                    "memory_usage_mb": 0
                }
            
            # Calculate stats
            last_interaction = max(
                interaction.get("timestamp", datetime.min) 
                for interaction in interactions
            )
            
            # Estimate memory usage (simplified)
            memory_usage_mb = len(json.dumps(interactions)) / 1024 / 1024
            
            return {
                "count": len(interactions),
                "last_interaction": last_interaction,
                "memory_usage_mb": memory_usage_mb
            }
            
        except Exception as e:
            self.logger.error(f"Error getting interaction stats for {persona_id}: {e}")
            return {
                "count": 0,
                "last_interaction": None,
                "memory_usage_mb": 0
            }
    
    async def _get_persona_voice_status(self, persona_id: str) -> str:
        """Get voice status for persona"""
        
        try:
            voice_config = await self.voice_framework.get_persona_voice_config(persona_id)
            if voice_config and voice_config.get("enabled", False):
                return "active"
            else:
                return "inactive"
        except Exception:
            return "error"
    
    async def _get_persona_coordination_status(self, persona_id: str) -> str:
        """Get coordination status for persona"""
        
        try:
            coord_status = await self.coordination_system.get_persona_coordination_status(persona_id)
            return coord_status.get("status", "unknown")
        except Exception:
            return "error"
    
    async def _get_coordination_status(self) -> Dict[str, Any]:
        """Get overall coordination system status"""
        
        try:
            return await self.coordination_system.get_system_status()
        except Exception as e:
            self.logger.error(f"Error getting coordination status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        
        try:
            return {
                "memory_operations_per_second": await self._calculate_memory_ops_per_second(),
                "persona_response_time_ms": await self._calculate_persona_response_time(),
                "voice_generation_time_ms": await self._calculate_voice_generation_time(),
                "coordination_latency_ms": await self._calculate_coordination_latency()
            }
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    async def _calculate_memory_ops_per_second(self) -> float:
        """Calculate memory operations per second"""
        # Simplified calculation
        return 150.0  # Placeholder
    
    async def _calculate_persona_response_time(self) -> float:
        """Calculate average persona response time"""
        # Simplified calculation
        return 85.0  # Placeholder
    
    async def _calculate_voice_generation_time(self) -> float:
        """Calculate average voice generation time"""
        # Simplified calculation
        return 450.0  # Placeholder
    
    async def _calculate_coordination_latency(self) -> float:
        """Calculate coordination system latency"""
        # Simplified calculation
        return 25.0  # Placeholder
    
    async def _update_persona_config(self, persona_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update persona configuration"""
        
        try:
            # Update personality dimensions
            if "personality" in config:
                for dimension, value in config["personality"].items():
                    await self.personality_engine.update_personality_dimension(
                        persona_id, PersonalityDimension(dimension), value
                    )
            
            # Update other persona settings
            if "voice_settings" in config:
                await self.voice_framework.update_persona_voice_settings(
                    persona_id, config["voice_settings"]
                )
            
            return {"success": True, "persona_id": persona_id}
            
        except Exception as e:
            return {"success": False, "persona_id": persona_id, "error": str(e)}

# Global unified admin interface instance
unified_admin = UnifiedAdminInterface()

# Export for use by other modules
__all__ = [
    "UnifiedAdminInterface",
    "AdminOperationType", 
    "AdminOperation",
    "SystemHealthMetrics",
    "PersonaStatus",
    "unified_admin"
]

