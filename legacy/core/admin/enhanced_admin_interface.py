"""
Enhanced Admin Interface for AI Assistant Ecosystem
Comprehensive management interface for Cherry, Sophia, and Karen personas
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.personas.enhanced_personality_engine import PersonalityEngine, PersonalityDimension, EmotionalState
from core.coordination.cross_domain_coordinator import CrossDomainCoordinator, InformationType, PrivacyLevel, CoordinationTrigger
from core.voice.voice_integration_framework import VoiceIntegrationFramework


class AdminAction(Enum):
    """Administrative actions for persona management"""
    UPDATE_PERSONALITY = "update_personality"
    ADJUST_PRIVACY = "adjust_privacy"
    TRIGGER_COORDINATION = "trigger_coordination"
    GRANT_PERMISSION = "grant_permission"
    UPDATE_VOICE_SETTINGS = "update_voice_settings"
    RESET_MEMORY = "reset_memory"
    EXPORT_DATA = "export_data"
    IMPORT_CONFIGURATION = "import_configuration"


class DashboardMetric(Enum):
    """Key metrics for admin dashboard"""
    INTERACTION_COUNT = "interaction_count"
    RELATIONSHIP_DEPTH = "relationship_depth"
    RESPONSE_TIME = "response_time"
    USER_SATISFACTION = "user_satisfaction"
    COORDINATION_EVENTS = "coordination_events"
    PRIVACY_VIOLATIONS = "privacy_violations"
    VOICE_GENERATION_TIME = "voice_generation_time"
    MEMORY_USAGE = "memory_usage"


@dataclass
class PersonaStatus:
    """Current status of an AI persona"""
    name: str
    active: bool
    current_emotional_state: str
    relationship_depth: float
    last_interaction: Optional[datetime]
    interaction_count_today: int
    pending_permissions: int
    memory_usage_mb: float
    voice_generation_enabled: bool
    coordination_events_today: int


@dataclass
class SystemHealth:
    """Overall system health metrics"""
    total_interactions_today: int
    average_response_time_ms: float
    memory_usage_percentage: float
    voice_synthesis_success_rate: float
    coordination_success_rate: float
    privacy_compliance_score: float
    uptime_percentage: float
    active_personas: int


class EnhancedAdminInterface:
    """Comprehensive admin interface for AI assistant ecosystem management"""
    
    def __init__(
        self,
        memory_router: MemoryRouter,
        personality_engine: PersonalityEngine,
        coordinator: CrossDomainCoordinator,
        voice_framework: VoiceIntegrationFramework
    ):
        self.memory_router = memory_router
        self.personality_engine = personality_engine
        self.coordinator = coordinator
        self.voice_framework = voice_framework
        self.logger = logging.getLogger(__name__)
        self.admin_sessions = {}
        self.audit_log = []
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview"""
        
        # Get persona statuses
        persona_statuses = {}
        for persona_name in ["cherry", "sophia", "karen"]:
            status = await self._get_persona_status(persona_name)
            persona_statuses[persona_name] = asdict(status)
        
        # Get system health
        system_health = await self._get_system_health()
        
        # Get recent coordination events
        recent_events = await self._get_recent_coordination_events(limit=10)
        
        # Get pending permissions
        pending_permissions = await self._get_pending_permissions()
        
        # Get performance metrics
        performance_metrics = await self._get_performance_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "persona_statuses": persona_statuses,
            "system_health": asdict(system_health),
            "recent_coordination_events": recent_events,
            "pending_permissions": pending_permissions,
            "performance_metrics": performance_metrics,
            "dashboard_version": "2.0.0"
        }
    
    async def _get_persona_status(self, persona_name: str) -> PersonaStatus:
        """Get detailed status for a specific persona"""
        
        # Get personality insights
        insights = await self.personality_engine.get_personality_insights(persona_name)
        
        # Get interaction history from memory
        interaction_history = await self.memory_router.retrieve_memory(
            f"{persona_name}_interaction_log",
            MemoryLayer.CONVERSATIONAL
        )
        
        # Calculate today's interactions
        today = datetime.now().date()
        today_interactions = 0
        last_interaction = None
        
        if interaction_history:
            for interaction in interaction_history:
                interaction_date = datetime.fromisoformat(interaction["timestamp"]).date()
                if interaction_date == today:
                    today_interactions += 1
                if not last_interaction or datetime.fromisoformat(interaction["timestamp"]) > last_interaction:
                    last_interaction = datetime.fromisoformat(interaction["timestamp"])
        
        # Get pending permissions
        pending_permissions = len([
            p for p in self.coordinator.pending_permissions.values()
            if p["target_persona"] == persona_name or p["info_packet"].source_persona == persona_name
        ])
        
        # Get coordination events today
        coordination_events = await self._count_coordination_events_today(persona_name)
        
        # Get voice generation status
        voice_info = await self.voice_framework.get_voice_profile_info(persona_name)
        voice_enabled = voice_info.get("voice_id") is not None
        
        return PersonaStatus(
            name=persona_name,
            active=True,  # Would be determined by actual activity
            current_emotional_state=insights.get("current_emotional_state", "supportive"),
            relationship_depth=insights.get("relationship_depth", 0.0),
            last_interaction=last_interaction,
            interaction_count_today=today_interactions,
            pending_permissions=pending_permissions,
            memory_usage_mb=await self._calculate_memory_usage(persona_name),
            voice_generation_enabled=voice_enabled,
            coordination_events_today=coordination_events
        )
    
    async def _get_system_health(self) -> SystemHealth:
        """Calculate overall system health metrics"""
        
        # Get total interactions today
        total_interactions = 0
        for persona in ["cherry", "sophia", "karen"]:
            status = await self._get_persona_status(persona)
            total_interactions += status.interaction_count_today
        
        # Calculate average response time (simulated - would be real metrics)
        avg_response_time = 250.0  # ms
        
        # Calculate memory usage
        memory_usage = await self._calculate_total_memory_usage()
        
        # Voice synthesis success rate (would be tracked from actual attempts)
        voice_success_rate = 0.98
        
        # Coordination success rate
        coordination_success_rate = 0.95
        
        # Privacy compliance score
        privacy_score = await self._calculate_privacy_compliance_score()
        
        # Uptime (would be tracked from actual system monitoring)
        uptime = 99.9
        
        return SystemHealth(
            total_interactions_today=total_interactions,
            average_response_time_ms=avg_response_time,
            memory_usage_percentage=memory_usage,
            voice_synthesis_success_rate=voice_success_rate,
            coordination_success_rate=coordination_success_rate,
            privacy_compliance_score=privacy_score,
            uptime_percentage=uptime,
            active_personas=3
        )
    
    async def _get_recent_coordination_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cross-domain coordination events"""
        
        events = await self.memory_router.retrieve_memory(
            "coordination_event_log",
            MemoryLayer.FOUNDATIONAL
        )
        
        if not events:
            return []
        
        # Sort by timestamp and limit
        if isinstance(events, list):
            sorted_events = sorted(events, key=lambda x: x["timestamp"], reverse=True)
            return sorted_events[:limit]
        else:
            return [events]  # Single event
    
    async def _get_pending_permissions(self) -> List[Dict[str, Any]]:
        """Get all pending permission requests"""
        
        pending = []
        for key, request in self.coordinator.pending_permissions.items():
            pending.append({
                "permission_key": key,
                "source_persona": request["info_packet"].source_persona,
                "target_persona": request["target_persona"],
                "information_type": request["info_packet"].information_type.value,
                "timestamp": request["timestamp"],
                "status": request["status"]
            })
        
        return pending
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        
        return {
            "memory_layers": {
                "conversational": await self._get_memory_layer_stats(MemoryLayer.CONVERSATIONAL),
                "contextual": await self._get_memory_layer_stats(MemoryLayer.CONTEXTUAL),
                "foundational": await self._get_memory_layer_stats(MemoryLayer.FOUNDATIONAL)
            },
            "voice_synthesis": {
                "cache_hit_rate": 0.75,
                "average_generation_time_ms": 1200,
                "total_audio_generated_mb": 45.2
            },
            "coordination": {
                "total_events_today": await self._count_total_coordination_events_today(),
                "privacy_violations": 0,
                "successful_information_shares": 23
            }
        }
    
    async def update_persona_personality(
        self,
        persona_name: str,
        dimension: str,
        new_value: float,
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Update personality dimension for a persona"""
        
        try:
            # Convert string to enum
            personality_dimension = PersonalityDimension(dimension.lower())
            
            # Validate value range
            if not 0.0 <= new_value <= 1.0:
                raise ValueError("Personality dimension values must be between 0.0 and 1.0")
            
            # Update personality
            await self.personality_engine.update_personality_dimension(
                persona_name, personality_dimension, new_value
            )
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.UPDATE_PERSONALITY,
                admin_user=admin_user,
                target_persona=persona_name,
                details={
                    "dimension": dimension,
                    "new_value": new_value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "persona": persona_name,
                "dimension": dimension,
                "new_value": new_value,
                "updated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error updating personality for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def adjust_privacy_boundary(
        self,
        information_type: str,
        persona: str,
        new_privacy_level: str,
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Adjust privacy boundary for information sharing"""
        
        try:
            # Convert strings to enums
            info_type = InformationType(information_type.lower())
            privacy_level = PrivacyLevel(int(new_privacy_level))
            
            # Update privacy boundary
            result = await self.coordinator.update_privacy_boundary(
                info_type, persona, privacy_level
            )
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.ADJUST_PRIVACY,
                admin_user=admin_user,
                target_persona=persona,
                details={
                    "information_type": information_type,
                    "new_privacy_level": new_privacy_level,
                    "result": result
                }
            )
            
            return {
                "success": True,
                "update_result": result
            }
        
        except Exception as e:
            self.logger.error(f"Error adjusting privacy boundary: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def trigger_manual_coordination(
        self,
        trigger: str,
        context: Dict[str, Any],
        initiating_persona: Optional[str] = None,
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Manually trigger cross-domain coordination"""
        
        try:
            # Convert string to enum
            coordination_trigger = CoordinationTrigger(trigger.lower())
            
            # Trigger coordination
            result = await self.coordinator.trigger_coordination(
                coordination_trigger, context, initiating_persona
            )
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.TRIGGER_COORDINATION,
                admin_user=admin_user,
                target_persona=initiating_persona,
                details={
                    "trigger": trigger,
                    "context": context,
                    "result": result
                }
            )
            
            return {
                "success": True,
                "coordination_result": result
            }
        
        except Exception as e:
            self.logger.error(f"Error triggering coordination: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def grant_information_permission(
        self,
        source_persona: str,
        target_persona: str,
        information_type: str,
        granted: bool = True,
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Grant or deny permission for confidential information sharing"""
        
        try:
            # Convert string to enum
            info_type = InformationType(information_type.lower())
            
            # Grant permission
            result = await self.coordinator.grant_permission(
                source_persona, target_persona, info_type, granted
            )
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.GRANT_PERMISSION,
                admin_user=admin_user,
                target_persona=f"{source_persona}_to_{target_persona}",
                details={
                    "information_type": information_type,
                    "granted": granted,
                    "result": result
                }
            )
            
            return {
                "success": True,
                "permission_result": result
            }
        
        except Exception as e:
            self.logger.error(f"Error granting permission: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def update_voice_settings(
        self,
        persona_name: str,
        voice_updates: Dict[str, Any],
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Update voice synthesis settings for a persona"""
        
        try:
            # Update voice profile
            result = await self.voice_framework.update_voice_profile(
                persona_name, voice_updates
            )
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.UPDATE_VOICE_SETTINGS,
                admin_user=admin_user,
                target_persona=persona_name,
                details={
                    "voice_updates": voice_updates,
                    "result": result
                }
            )
            
            return {
                "success": True,
                "voice_update_result": result
            }
        
        except Exception as e:
            self.logger.error(f"Error updating voice settings for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_persona_detailed_analytics(self, persona_name: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific persona"""
        
        # Get personality insights
        personality_insights = await self.personality_engine.get_personality_insights(persona_name)
        
        # Get voice profile info
        voice_info = await self.voice_framework.get_voice_profile_info(persona_name)
        
        # Get interaction patterns
        interaction_patterns = await self._analyze_interaction_patterns(persona_name)
        
        # Get coordination involvement
        coordination_stats = await self._get_coordination_statistics(persona_name)
        
        # Get memory usage breakdown
        memory_breakdown = await self._get_memory_breakdown(persona_name)
        
        return {
            "persona_name": persona_name,
            "personality_insights": personality_insights,
            "voice_profile": voice_info,
            "interaction_patterns": interaction_patterns,
            "coordination_statistics": coordination_stats,
            "memory_breakdown": memory_breakdown,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def export_persona_configuration(self, persona_name: str) -> Dict[str, Any]:
        """Export complete configuration for a persona"""
        
        # Get personality configuration
        personality_insights = await self.personality_engine.get_personality_insights(persona_name)
        
        # Get voice configuration
        voice_info = await self.voice_framework.get_voice_profile_info(persona_name)
        
        # Get privacy boundaries
        privacy_config = {}
        for info_type in InformationType:
            boundary = self.coordinator.privacy_boundaries.get(info_type)
            if boundary:
                privacy_config[info_type.value] = {
                    "default_level": boundary.default_privacy_level.value,
                    "persona_specific": boundary.persona_specific_levels.get(persona_name, boundary.default_privacy_level).value
                }
        
        return {
            "persona_name": persona_name,
            "export_timestamp": datetime.now().isoformat(),
            "export_version": "1.0.0",
            "personality_configuration": personality_insights,
            "voice_configuration": voice_info,
            "privacy_configuration": privacy_config,
            "export_metadata": {
                "exported_by": "admin_interface",
                "export_type": "full_configuration"
            }
        }
    
    async def import_persona_configuration(
        self,
        persona_name: str,
        configuration: Dict[str, Any],
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """Import configuration for a persona"""
        
        try:
            import_results = {
                "personality": None,
                "voice": None,
                "privacy": None
            }
            
            # Import personality configuration
            if "personality_configuration" in configuration:
                personality_config = configuration["personality_configuration"]
                if "personality_dimensions" in personality_config:
                    for dimension, value in personality_config["personality_dimensions"].items():
                        result = await self.update_persona_personality(
                            persona_name, dimension, value, admin_user
                        )
                        import_results["personality"] = result
            
            # Import voice configuration
            if "voice_configuration" in configuration:
                voice_config = configuration["voice_configuration"]
                if "technical_settings" in voice_config:
                    result = await self.update_voice_settings(
                        persona_name, voice_config["technical_settings"], admin_user
                    )
                    import_results["voice"] = result
            
            # Import privacy configuration
            if "privacy_configuration" in configuration:
                privacy_config = configuration["privacy_configuration"]
                privacy_results = []
                for info_type, settings in privacy_config.items():
                    if "persona_specific" in settings:
                        result = await self.adjust_privacy_boundary(
                            info_type, persona_name, str(settings["persona_specific"]), admin_user
                        )
                        privacy_results.append(result)
                import_results["privacy"] = privacy_results
            
            # Log admin action
            await self._log_admin_action(
                action=AdminAction.IMPORT_CONFIGURATION,
                admin_user=admin_user,
                target_persona=persona_name,
                details={
                    "configuration_source": configuration.get("export_metadata", {}),
                    "import_results": import_results
                }
            )
            
            return {
                "success": True,
                "import_results": import_results,
                "imported_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error importing configuration for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_system_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get system audit log"""
        
        # Sort audit log by timestamp (most recent first)
        sorted_log = sorted(self.audit_log, key=lambda x: x["timestamp"], reverse=True)
        return sorted_log[:limit]
    
    async def _log_admin_action(
        self,
        action: AdminAction,
        admin_user: str,
        target_persona: Optional[str] = None,
        details: Dict[str, Any] = None
    ):
        """Log administrative action for audit trail"""
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "admin_user": admin_user,
            "target_persona": target_persona,
            "details": details or {},
            "session_id": self.admin_sessions.get(admin_user, "unknown")
        }
        
        self.audit_log.append(log_entry)
        
        # Also store in persistent memory
        await self.memory_router.store_memory(
            "admin_audit_log",
            log_entry,
            MemoryLayer.FOUNDATIONAL
        )
    
    async def _calculate_memory_usage(self, persona_name: str) -> float:
        """Calculate memory usage for a persona (in MB)"""
        
        # This would calculate actual memory usage
        # For now, return simulated values
        base_usage = {
            "cherry": 12.5,
            "sophia": 8.3,
            "karen": 9.7
        }
        
        return base_usage.get(persona_name, 10.0)
    
    async def _calculate_total_memory_usage(self) -> float:
        """Calculate total system memory usage percentage"""
        
        # This would calculate actual memory usage
        # For now, return simulated value
        return 45.2  # 45.2% of available memory
    
    async def _calculate_privacy_compliance_score(self) -> float:
        """Calculate privacy compliance score"""
        
        # This would analyze actual privacy violations
        # For now, return high compliance score
        return 0.98  # 98% compliance
    
    async def _count_coordination_events_today(self, persona_name: str) -> int:
        """Count coordination events involving a persona today"""
        
        events = await self.memory_router.retrieve_memory(
            "coordination_event_log",
            MemoryLayer.FOUNDATIONAL
        )
        
        if not events:
            return 0
        
        today = datetime.now().date()
        count = 0
        
        events_list = events if isinstance(events, list) else [events]
        
        for event in events_list:
            event_date = datetime.fromisoformat(event["timestamp"]).date()
            if event_date == today:
                if (event.get("source_persona") == persona_name or 
                    persona_name in event.get("target_personas", [])):
                    count += 1
        
        return count
    
    async def _count_total_coordination_events_today(self) -> int:
        """Count total coordination events today"""
        
        events = await self.memory_router.retrieve_memory(
            "coordination_event_log",
            MemoryLayer.FOUNDATIONAL
        )
        
        if not events:
            return 0
        
        today = datetime.now().date()
        count = 0
        
        events_list = events if isinstance(events, list) else [events]
        
        for event in events_list:
            event_date = datetime.fromisoformat(event["timestamp"]).date()
            if event_date == today:
                count += 1
        
        return count
    
    async def _get_memory_layer_stats(self, layer: MemoryLayer) -> Dict[str, Any]:
        """Get statistics for a memory layer"""
        
        # This would get actual memory layer statistics
        # For now, return simulated values
        stats = {
            MemoryLayer.CONVERSATIONAL: {"entries": 156, "size_mb": 2.3},
            MemoryLayer.CONTEXTUAL: {"entries": 89, "size_mb": 5.7},
            MemoryLayer.FOUNDATIONAL: {"entries": 234, "size_mb": 12.1}
        }
        
        return stats.get(layer, {"entries": 0, "size_mb": 0.0})
    
    async def _analyze_interaction_patterns(self, persona_name: str) -> Dict[str, Any]:
        """Analyze interaction patterns for a persona"""
        
        # This would analyze actual interaction data
        # For now, return simulated analysis
        patterns = {
            "cherry": {
                "peak_hours": ["19:00-22:00", "07:00-09:00"],
                "average_session_length_minutes": 15.3,
                "most_common_topics": ["life_goals", "relationships", "travel"],
                "emotional_state_distribution": {
                    "playful": 0.35,
                    "affectionate": 0.28,
                    "supportive": 0.22,
                    "excited": 0.15
                }
            },
            "sophia": {
                "peak_hours": ["09:00-12:00", "14:00-17:00"],
                "average_session_length_minutes": 8.7,
                "most_common_topics": ["business_metrics", "strategy", "client_analysis"],
                "emotional_state_distribution": {
                    "professional": 0.45,
                    "confident": 0.35,
                    "focused": 0.20
                }
            },
            "karen": {
                "peak_hours": ["08:00-10:00", "16:00-18:00"],
                "average_session_length_minutes": 12.1,
                "most_common_topics": ["health_tracking", "wellness", "medical_research"],
                "emotional_state_distribution": {
                    "caring": 0.40,
                    "empathetic": 0.35,
                    "professional": 0.25
                }
            }
        }
        
        return patterns.get(persona_name, {})
    
    async def _get_coordination_statistics(self, persona_name: str) -> Dict[str, Any]:
        """Get coordination statistics for a persona"""
        
        # This would analyze actual coordination data
        # For now, return simulated statistics
        stats = {
            "cherry": {
                "total_coordination_events": 45,
                "initiated_events": 28,
                "received_events": 17,
                "most_common_triggers": ["major_life_event", "stress_indicator"],
                "coordination_success_rate": 0.96
            },
            "sophia": {
                "total_coordination_events": 23,
                "initiated_events": 15,
                "received_events": 8,
                "most_common_triggers": ["business_milestone", "schedule_conflict"],
                "coordination_success_rate": 0.98
            },
            "karen": {
                "total_coordination_events": 31,
                "initiated_events": 19,
                "received_events": 12,
                "most_common_triggers": ["health_concern", "wellness_alert"],
                "coordination_success_rate": 0.94
            }
        }
        
        return stats.get(persona_name, {})
    
    async def _get_memory_breakdown(self, persona_name: str) -> Dict[str, Any]:
        """Get memory usage breakdown for a persona"""
        
        # This would analyze actual memory usage
        # For now, return simulated breakdown
        breakdown = {
            "cherry": {
                "conversational_memory_mb": 3.2,
                "contextual_memory_mb": 5.8,
                "foundational_memory_mb": 3.5,
                "total_entries": 234,
                "relationship_data_mb": 2.1,
                "interaction_history_mb": 4.9
            },
            "sophia": {
                "conversational_memory_mb": 1.8,
                "contextual_memory_mb": 3.2,
                "foundational_memory_mb": 3.3,
                "total_entries": 156,
                "business_data_mb": 2.7,
                "interaction_history_mb": 2.6
            },
            "karen": {
                "conversational_memory_mb": 2.1,
                "contextual_memory_mb": 4.1,
                "foundational_memory_mb": 3.5,
                "total_entries": 189,
                "health_data_mb": 3.8,
                "interaction_history_mb": 3.9
            }
        }
        
        return breakdown.get(persona_name, {})


# Admin Interface Service for API endpoints
class AdminInterfaceService:
    """Service layer for admin interface API endpoints"""
    
    def __init__(self, admin_interface: EnhancedAdminInterface):
        self.admin_interface = admin_interface
        self.logger = logging.getLogger(__name__)
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """API endpoint for dashboard data"""
        
        try:
            dashboard_data = await self.admin_interface.get_dashboard_overview()
            return {"success": True, "dashboard": dashboard_data}
        
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def update_persona_settings(
        self,
        persona_name: str,
        settings: Dict[str, Any],
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """API endpoint for updating persona settings"""
        
        try:
            results = {}
            
            # Update personality dimensions
            if "personality" in settings:
                for dimension, value in settings["personality"].items():
                    result = await self.admin_interface.update_persona_personality(
                        persona_name, dimension, value, admin_user
                    )
                    results[f"personality_{dimension}"] = result
            
            # Update voice settings
            if "voice" in settings:
                result = await self.admin_interface.update_voice_settings(
                    persona_name, settings["voice"], admin_user
                )
                results["voice_settings"] = result
            
            # Update privacy boundaries
            if "privacy" in settings:
                privacy_results = []
                for info_type, privacy_level in settings["privacy"].items():
                    result = await self.admin_interface.adjust_privacy_boundary(
                        info_type, persona_name, str(privacy_level), admin_user
                    )
                    privacy_results.append(result)
                results["privacy_settings"] = privacy_results
            
            return {
                "success": True,
                "update_results": results,
                "updated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error updating persona settings: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_persona_analytics(self, persona_name: str) -> Dict[str, Any]:
        """API endpoint for persona analytics"""
        
        try:
            analytics = await self.admin_interface.get_persona_detailed_analytics(persona_name)
            return {"success": True, "analytics": analytics}
        
        except Exception as e:
            self.logger.error(f"Error getting persona analytics: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def handle_permission_request(
        self,
        permission_data: Dict[str, Any],
        admin_user: str = "admin"
    ) -> Dict[str, Any]:
        """API endpoint for handling permission requests"""
        
        try:
            result = await self.admin_interface.grant_information_permission(
                source_persona=permission_data["source_persona"],
                target_persona=permission_data["target_persona"],
                information_type=permission_data["information_type"],
                granted=permission_data.get("granted", True),
                admin_user=admin_user
            )
            
            return {"success": True, "permission_result": result}
        
        except Exception as e:
            self.logger.error(f"Error handling permission request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


# Example usage and testing
if __name__ == "__main__":
    async def test_admin_interface():
        """Test the enhanced admin interface"""
        
        # This would normally be injected
        from core.memory.advanced_memory_system import MemoryRouter
        from core.personas.enhanced_personality_engine import PersonalityEngine
        from core.coordination.cross_domain_coordinator import CrossDomainCoordinator
        from core.voice.voice_integration_framework import VoiceIntegrationFramework
        
        memory_router = MemoryRouter()
        personality_engine = PersonalityEngine(memory_router)
        coordinator = CrossDomainCoordinator(memory_router, personality_engine)
        voice_framework = VoiceIntegrationFramework()
        
        admin_interface = EnhancedAdminInterface(
            memory_router, personality_engine, coordinator, voice_framework
        )
        
        # Test dashboard overview
        dashboard = await admin_interface.get_dashboard_overview()
        print("Dashboard Overview:")
        print(json.dumps(dashboard, indent=2, default=str))
        
        # Test persona analytics
        cherry_analytics = await admin_interface.get_persona_detailed_analytics("cherry")
        print("\nCherry Analytics:")
        print(json.dumps(cherry_analytics, indent=2, default=str))
        
        # Test configuration export
        cherry_config = await admin_interface.export_persona_configuration("cherry")
        print("\nCherry Configuration Export:")
        print(json.dumps(cherry_config, indent=2, default=str))
        
        print("\nAdmin Interface initialized and tested successfully!")
    
    # Run test
    asyncio.run(test_admin_interface())

