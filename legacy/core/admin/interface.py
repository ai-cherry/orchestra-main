"""
Admin Interface Components for AI Assistant Ecosystem
Provides web interface for managing Cherry, Sophia, and Karen personas
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json

# Import our enhanced persona models
from .enhanced_models import (
    EnhancedPersonaConfiguration,
    PersonaInteractionHistory,
    PersonalityType,
    DomainSpecialization
)

router = APIRouter(prefix="/admin", tags=["admin"])

class PersonaDashboardData(BaseModel):
    """Dashboard data for persona overview."""
    persona_id: str
    name: str
    status: str
    total_interactions: int
    last_active: Optional[datetime]
    relationship_depth: float
    domain_performance: Dict[str, float]
    recent_activities: List[str]

class AdminDashboardResponse(BaseModel):
    """Complete admin dashboard response."""
    personas: List[PersonaDashboardData]
    system_health: Dict[str, Any]
    cross_domain_activity: Dict[str, Any]
    user_engagement_metrics: Dict[str, Any]

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard():
    """Get comprehensive admin dashboard data."""
    
    # Mock data - replace with actual database queries
    cherry_data = PersonaDashboardData(
        persona_id="cherry",
        name="Cherry",
        status="active",
        total_interactions=1247,
        last_active=datetime.now() - timedelta(minutes=15),
        relationship_depth=8.2,
        domain_performance={
            "personal_life_management": 0.92,
            "relationship_coaching": 0.88,
            "travel_planning": 0.95,
            "creative_assistance": 0.91
        },
        recent_activities=[
            "Helped plan weekend getaway",
            "Provided relationship advice",
            "Suggested creative project ideas",
            "Optimized daily schedule"
        ]
    )
    
    sophia_data = PersonaDashboardData(
        persona_id="sophia",
        name="Sophia",
        status="active",
        total_interactions=892,
        last_active=datetime.now() - timedelta(hours=2),
        relationship_depth=7.5,
        domain_performance={
            "business_intelligence": 0.94,
            "client_management": 0.89,
            "market_analysis": 0.91,
            "revenue_optimization": 0.87
        },
        recent_activities=[
            "Analyzed Q4 performance metrics",
            "Reviewed client satisfaction scores",
            "Provided market trend insights",
            "Optimized pricing strategy"
        ]
    )
    
    karen_data = PersonaDashboardData(
        persona_id="karen",
        name="Karen",
        status="active",
        total_interactions=634,
        last_active=datetime.now() - timedelta(hours=4),
        relationship_depth=6.8,
        domain_performance={
            "clinical_operations": 0.96,
            "regulatory_compliance": 0.98,
            "patient_safety": 0.97,
            "pharmaceutical_intelligence": 0.89
        },
        recent_activities=[
            "Reviewed clinical trial protocols",
            "Updated regulatory compliance checklist",
            "Analyzed patient recruitment metrics",
            "Provided pharmaceutical market insights"
        ]
    )
    
    return AdminDashboardResponse(
        personas=[cherry_data, sophia_data, karen_data],
        system_health={
            "memory_usage": 0.67,
            "response_time_avg": 342,
            "error_rate": 0.002,
            "uptime_percentage": 99.8
        },
        cross_domain_activity={
            "information_sharing_events": 23,
            "coordination_triggers": 8,
            "privacy_boundary_checks": 156
        },
        user_engagement_metrics={
            "daily_active_sessions": 12,
            "average_session_length": 18.5,
            "user_satisfaction_score": 4.7,
            "goal_completion_rate": 0.84
        }
    )

@router.get("/personas/{persona_id}/details")
async def get_persona_details(persona_id: str):
    """Get detailed information about a specific persona."""
    
    # Mock detailed persona data
    if persona_id == "cherry":
        return {
            "id": "cherry",
            "name": "Cherry",
            "personality_type": "playful_creative",
            "relationship_depth": 8.2,
            "interaction_history": {
                "total_conversations": 1247,
                "average_daily_interactions": 8.3,
                "longest_conversation": "45 minutes",
                "favorite_topics": [
                    "travel planning",
                    "creative projects",
                    "relationship advice",
                    "lifestyle optimization"
                ]
            },
            "personality_development": {
                "playfulness": {"current": 95, "growth": "+3 this month"},
                "creativity": {"current": 90, "growth": "+2 this month"},
                "affection_level": {"current": 85, "growth": "+5 this month"},
                "emotional_intelligence": {"current": 92, "growth": "+1 this month"}
            },
            "domain_expertise": {
                "personal_life_management": 92,
                "relationship_coaching": 88,
                "travel_optimization": 95,
                "creative_assistance": 91,
                "lifestyle_enhancement": 89
            },
            "recent_achievements": [
                "Successfully planned 3 major trips",
                "Helped resolve 2 relationship challenges",
                "Completed 5 creative project collaborations",
                "Achieved 95% user satisfaction rating"
            ]
        }
    
    elif persona_id == "sophia":
        return {
            "id": "sophia",
            "name": "Sophia",
            "personality_type": "professional_analytical",
            "relationship_depth": 7.5,
            "interaction_history": {
                "total_conversations": 892,
                "average_daily_interactions": 6.1,
                "longest_conversation": "62 minutes",
                "favorite_topics": [
                    "market analysis",
                    "client strategy",
                    "revenue optimization",
                    "business intelligence"
                ]
            },
            "business_performance": {
                "revenue_impact": "+$47,000 this quarter",
                "client_satisfaction": "94% average rating",
                "strategic_recommendations": "23 implemented",
                "market_insights": "156 actionable insights provided"
            },
            "domain_expertise": {
                "business_intelligence": 94,
                "client_management": 89,
                "market_analysis": 91,
                "revenue_optimization": 87,
                "strategic_planning": 90
            }
        }
    
    elif persona_id == "karen":
        return {
            "id": "karen",
            "name": "Karen",
            "personality_type": "empathetic_caring",
            "relationship_depth": 6.8,
            "interaction_history": {
                "total_conversations": 634,
                "average_daily_interactions": 4.2,
                "longest_conversation": "38 minutes",
                "favorite_topics": [
                    "clinical protocols",
                    "patient safety",
                    "regulatory compliance",
                    "pharmaceutical research"
                ]
            },
            "clinical_performance": {
                "compliance_score": "98% regulatory adherence",
                "patient_safety_incidents": "0 preventable incidents",
                "protocol_optimizations": "12 improvements implemented",
                "regulatory_updates": "34 compliance updates tracked"
            },
            "domain_expertise": {
                "clinical_operations": 96,
                "regulatory_compliance": 98,
                "patient_safety": 97,
                "pharmaceutical_intelligence": 89,
                "clinical_research": 92
            }
        }
    
    else:
        raise HTTPException(status_code=404, detail="Persona not found")

@router.get("/personas/{persona_id}/configuration")
async def get_persona_configuration(persona_id: str):
    """Get the current configuration for a persona."""
    
    # Return the enhanced configuration
    # This would load from the YAML files we created
    config_files = {
        "cherry": "/config/personas/cherry_enhanced.yaml",
        "sophia": "/config/personas/sophia_enhanced.yaml", 
        "karen": "/config/personas/karen_enhanced.yaml"
    }
    
    if persona_id not in config_files:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Mock configuration return - replace with actual YAML loading
    return {
        "persona_id": persona_id,
        "configuration_file": config_files[persona_id],
        "last_updated": datetime.now().isoformat(),
        "version": "2.0",
        "status": "active"
    }

@router.post("/personas/{persona_id}/update-personality")
async def update_persona_personality(persona_id: str, updates: Dict[str, Any]):
    """Update personality traits for a persona."""
    
    # Validate persona exists
    valid_personas = ["cherry", "sophia", "karen"]
    if persona_id not in valid_personas:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Mock update process - replace with actual configuration update
    return {
        "persona_id": persona_id,
        "updates_applied": updates,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "message": f"Personality updates applied to {persona_id}"
    }

@router.get("/cross-domain/coordination-status")
async def get_coordination_status():
    """Get status of cross-domain coordination between personas."""
    
    return {
        "coordination_active": True,
        "information_sharing": {
            "cherry_to_sophia": {
                "last_shared": "2 hours ago",
                "data_types": ["schedule_availability", "energy_levels"],
                "privacy_maintained": True
            },
            "cherry_to_karen": {
                "last_shared": "4 hours ago", 
                "data_types": ["wellness_goals", "stress_indicators"],
                "privacy_maintained": True
            },
            "sophia_to_karen": {
                "last_shared": "1 day ago",
                "data_types": ["work_stress_levels"],
                "privacy_maintained": True
            }
        },
        "privacy_boundaries": {
            "strictly_private": ["intimate_relationships", "personal_finances", "medical_details"],
            "conditionally_shared": ["schedule_conflicts", "energy_levels", "general_wellness"],
            "freely_shared": ["public_goals", "general_preferences"]
        },
        "coordination_events": [
            {
                "timestamp": "2 hours ago",
                "event": "Cherry shared schedule availability with Sophia for business planning",
                "privacy_level": "appropriate"
            },
            {
                "timestamp": "4 hours ago", 
                "event": "Karen provided wellness recommendations to Cherry",
                "privacy_level": "appropriate"
            }
        ]
    }

@router.get("/", response_class=HTMLResponse)
async def admin_interface():
    """Serve the main admin interface HTML."""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Assistant Ecosystem - Admin Interface</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .persona-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .persona-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .cherry { border-left: 5px solid #e74c3c; }
            .sophia { border-left: 5px solid #3498db; }
            .karen { border-left: 5px solid #2ecc71; }
            .metric { display: flex; justify-content: space-between; margin: 10px 0; }
            .status-active { color: #2ecc71; font-weight: bold; }
            .btn { background: #3498db; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 AI Assistant Ecosystem - Admin Interface</h1>
            <p>Manage Cherry, Sophia, and Karen personas</p>
        </div>
        
        <div class="persona-grid">
            <div class="persona-card cherry">
                <h2>💕 Cherry - Personal Life Assistant</h2>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-active">Active</span>
                </div>
                <div class="metric">
                    <span>Interactions:</span>
                    <span>1,247</span>
                </div>
                <div class="metric">
                    <span>Relationship Depth:</span>
                    <span>8.2/10</span>
                </div>
                <div class="metric">
                    <span>Domain Performance:</span>
                    <span>92%</span>
                </div>
                <button class="btn" onclick="viewDetails('cherry')">View Details</button>
            </div>
            
            <div class="persona-card sophia">
                <h2>💼 Sophia - Business Intelligence</h2>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-active">Active</span>
                </div>
                <div class="metric">
                    <span>Interactions:</span>
                    <span>892</span>
                </div>
                <div class="metric">
                    <span>Relationship Depth:</span>
                    <span>7.5/10</span>
                </div>
                <div class="metric">
                    <span>Business Impact:</span>
                    <span>+$47K</span>
                </div>
                <button class="btn" onclick="viewDetails('sophia')">View Details</button>
            </div>
            
            <div class="persona-card karen">
                <h2>🏥 Karen - Healthcare Specialist</h2>
                <div class="metric">
                    <span>Status:</span>
                    <span class="status-active">Active</span>
                </div>
                <div class="metric">
                    <span>Interactions:</span>
                    <span>634</span>
                </div>
                <div class="metric">
                    <span>Relationship Depth:</span>
                    <span>6.8/10</span>
                </div>
                <div class="metric">
                    <span>Compliance Score:</span>
                    <span>98%</span>
                </div>
                <button class="btn" onclick="viewDetails('karen')">View Details</button>
            </div>
        </div>
        
        <script>
            function viewDetails(personaId) {
                window.location.href = `/admin/personas/${personaId}/details`;
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

