# Orchestra AI Persona Management API
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import psycopg2
import json
from datetime import datetime
import uuid

# Request/Response Models
class PersonaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    persona_type: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class PersonaCreate(PersonaBase):
    domain_leanings: Optional[Dict[str, Any]] = {}
    voice_settings: Optional[Dict[str, Any]] = {}
    api_access_config: Optional[Dict[str, Any]] = {}
    search_preferences: Optional[Dict[str, Any]] = {}

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    domain_leanings: Optional[Dict[str, Any]] = None
    voice_settings: Optional[Dict[str, Any]] = None
    api_access_config: Optional[Dict[str, Any]] = None
    search_preferences: Optional[Dict[str, Any]] = None

class PersonaResponse(PersonaBase):
    id: str
    domain_leanings: Dict[str, Any]
    voice_settings: Dict[str, Any]
    api_access_config: Dict[str, Any]
    search_preferences: Dict[str, Any]
    learning_data: Dict[str, Any]
    usage_stats: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class PersonaAnalytics(BaseModel):
    id: str
    name: str
    persona_type: str
    total_messages: int
    total_searches: int
    total_creative_projects: int
    total_voice_generations: int
    total_estimated_cost: float
    last_updated: datetime

class DomainLeaningUpdate(BaseModel):
    keywords: List[str]
    preferences: List[str]
    weight: Optional[float] = 1.0

class VoiceSettingsUpdate(BaseModel):
    voice_id: str
    stability: float = Field(ge=0.0, le=1.0)
    similarity_boost: float = Field(ge=0.0, le=1.0)
    style: float = Field(ge=0.0, le=1.0)
    use_speaker_boost: bool = True

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="orchestra_prod",
            user="orchestra",
            password="Orchestra_Prod_2025_Secure"
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Persona Management Functions
class PersonaManager:
    
    @staticmethod
    def get_all_personas() -> List[PersonaResponse]:
        """Get all personas with their configurations"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, persona_type, description, domain_leanings, 
                       voice_settings, api_access_config, search_preferences,
                       learning_data, usage_stats, is_active, created_at, updated_at
                FROM orchestra.personas 
                WHERE is_active = true
                ORDER BY name
            """)
            
            personas = []
            for row in cursor.fetchall():
                personas.append(PersonaResponse(
                    id=str(row[0]),
                    name=row[1],
                    persona_type=row[2],
                    description=row[3] or "",
                    domain_leanings=row[4] or {},
                    voice_settings=row[5] or {},
                    api_access_config=row[6] or {},
                    search_preferences=row[7] or {},
                    learning_data=row[8] or {},
                    usage_stats=row[9] or {},
                    is_active=row[10],
                    created_at=row[11],
                    updated_at=row[12]
                ))
            
            return personas
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_persona_by_id(persona_id: str) -> PersonaResponse:
        """Get a specific persona by ID"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, persona_type, description, domain_leanings, 
                       voice_settings, api_access_config, search_preferences,
                       learning_data, usage_stats, is_active, created_at, updated_at
                FROM orchestra.personas 
                WHERE id = %s AND is_active = true
            """, (persona_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Persona not found")
            
            return PersonaResponse(
                id=str(row[0]),
                name=row[1],
                persona_type=row[2],
                description=row[3] or "",
                domain_leanings=row[4] or {},
                voice_settings=row[5] or {},
                api_access_config=row[6] or {},
                search_preferences=row[7] or {},
                learning_data=row[8] or {},
                usage_stats=row[9] or {},
                is_active=row[10],
                created_at=row[11],
                updated_at=row[12]
            )
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create_persona(persona_data: PersonaCreate) -> PersonaResponse:
        """Create a new persona"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            persona_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO orchestra.personas 
                (id, name, persona_type, description, domain_leanings, voice_settings, 
                 api_access_config, search_preferences, learning_data, usage_stats)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING created_at, updated_at
            """, (
                persona_id,
                persona_data.name,
                persona_data.persona_type,
                persona_data.description,
                json.dumps(persona_data.domain_leanings),
                json.dumps(persona_data.voice_settings),
                json.dumps(persona_data.api_access_config),
                json.dumps(persona_data.search_preferences),
                json.dumps({"interaction_count": 0, "preference_updates": [], "feedback_scores": []}),
                json.dumps({"total_messages": 0, "total_searches": 0, "creative_projects": 0, "voice_generations": 0})
            ))
            
            created_at, updated_at = cursor.fetchone()
            conn.commit()
            
            return PersonaResponse(
                id=persona_id,
                name=persona_data.name,
                persona_type=persona_data.persona_type,
                description=persona_data.description or "",
                domain_leanings=persona_data.domain_leanings,
                voice_settings=persona_data.voice_settings,
                api_access_config=persona_data.api_access_config,
                search_preferences=persona_data.search_preferences,
                learning_data={"interaction_count": 0, "preference_updates": [], "feedback_scores": []},
                usage_stats={"total_messages": 0, "total_searches": 0, "creative_projects": 0, "voice_generations": 0},
                is_active=True,
                created_at=created_at,
                updated_at=updated_at
            )
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_persona(persona_id: str, persona_data: PersonaUpdate) -> PersonaResponse:
        """Update an existing persona"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            update_values = []
            
            if persona_data.name is not None:
                update_fields.append("name = %s")
                update_values.append(persona_data.name)
            
            if persona_data.description is not None:
                update_fields.append("description = %s")
                update_values.append(persona_data.description)
            
            if persona_data.domain_leanings is not None:
                update_fields.append("domain_leanings = %s")
                update_values.append(json.dumps(persona_data.domain_leanings))
            
            if persona_data.voice_settings is not None:
                update_fields.append("voice_settings = %s")
                update_values.append(json.dumps(persona_data.voice_settings))
            
            if persona_data.api_access_config is not None:
                update_fields.append("api_access_config = %s")
                update_values.append(json.dumps(persona_data.api_access_config))
            
            if persona_data.search_preferences is not None:
                update_fields.append("search_preferences = %s")
                update_values.append(json.dumps(persona_data.search_preferences))
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            update_fields.append("updated_at = NOW()")
            update_values.append(persona_id)
            
            query = f"""
                UPDATE orchestra.personas 
                SET {', '.join(update_fields)}
                WHERE id = %s AND is_active = true
                RETURNING updated_at
            """
            
            cursor.execute(query, update_values)
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Persona not found")
            
            conn.commit()
            
            # Return updated persona
            return PersonaManager.get_persona_by_id(persona_id)
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete_persona(persona_id: str) -> bool:
        """Soft delete a persona"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orchestra.personas 
                SET is_active = false, updated_at = NOW()
                WHERE id = %s AND is_active = true
            """, (persona_id,))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Persona not found")
            
            conn.commit()
            return True
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_persona_analytics() -> List[PersonaAnalytics]:
        """Get analytics for all personas"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orchestra.persona_analytics ORDER BY name")
            
            analytics = []
            for row in cursor.fetchall():
                analytics.append(PersonaAnalytics(
                    id=str(row[0]),
                    name=row[1],
                    persona_type=row[2],
                    total_messages=row[3],
                    total_searches=row[4],
                    total_creative_projects=row[5],
                    total_voice_generations=row[6],
                    total_estimated_cost=float(row[7]) if row[7] else 0.0,
                    last_updated=row[8]
                ))
            
            return analytics
            
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_domain_leanings(persona_id: str, leanings: DomainLeaningUpdate) -> PersonaResponse:
        """Update domain leanings for a persona"""
        current_persona = PersonaManager.get_persona_by_id(persona_id)
        
        # Merge with existing domain leanings
        updated_leanings = current_persona.domain_leanings.copy()
        updated_leanings.update({
            "keywords": leanings.keywords,
            "preferences": leanings.preferences,
            "weight": leanings.weight,
            "last_updated": datetime.now().isoformat()
        })
        
        return PersonaManager.update_persona(
            persona_id, 
            PersonaUpdate(domain_leanings=updated_leanings)
        )
    
    @staticmethod
    def update_voice_settings(persona_id: str, voice_settings: VoiceSettingsUpdate) -> PersonaResponse:
        """Update voice settings for a persona"""
        updated_settings = {
            "voice_id": voice_settings.voice_id,
            "stability": voice_settings.stability,
            "similarity_boost": voice_settings.similarity_boost,
            "style": voice_settings.style,
            "use_speaker_boost": voice_settings.use_speaker_boost,
            "last_updated": datetime.now().isoformat()
        }
        
        return PersonaManager.update_persona(
            persona_id,
            PersonaUpdate(voice_settings=updated_settings)
        )

# Add these endpoints to your main FastAPI app
def add_persona_management_endpoints(app: FastAPI):
    
    @app.get("/api/personas", response_model=List[PersonaResponse])
    async def get_personas():
        """Get all active personas"""
        return PersonaManager.get_all_personas()
    
    @app.get("/api/personas/{persona_id}", response_model=PersonaResponse)
    async def get_persona(persona_id: str):
        """Get a specific persona by ID"""
        return PersonaManager.get_persona_by_id(persona_id)
    
    @app.post("/api/personas", response_model=PersonaResponse)
    async def create_persona(persona_data: PersonaCreate):
        """Create a new persona"""
        return PersonaManager.create_persona(persona_data)
    
    @app.put("/api/personas/{persona_id}", response_model=PersonaResponse)
    async def update_persona(persona_id: str, persona_data: PersonaUpdate):
        """Update an existing persona"""
        return PersonaManager.update_persona(persona_id, persona_data)
    
    @app.delete("/api/personas/{persona_id}")
    async def delete_persona(persona_id: str):
        """Delete a persona"""
        PersonaManager.delete_persona(persona_id)
        return {"message": "Persona deleted successfully"}
    
    @app.get("/api/personas/analytics/summary", response_model=List[PersonaAnalytics])
    async def get_persona_analytics():
        """Get analytics summary for all personas"""
        return PersonaManager.get_persona_analytics()
    
    @app.put("/api/personas/{persona_id}/domain-leanings", response_model=PersonaResponse)
    async def update_persona_domain_leanings(persona_id: str, leanings: DomainLeaningUpdate):
        """Update domain leanings for a persona"""
        return PersonaManager.update_domain_leanings(persona_id, leanings)
    
    @app.put("/api/personas/{persona_id}/voice-settings", response_model=PersonaResponse)
    async def update_persona_voice_settings(persona_id: str, voice_settings: VoiceSettingsUpdate):
        """Update voice settings for a persona"""
        return PersonaManager.update_voice_settings(persona_id, voice_settings)

# Usage: Import and call add_persona_management_endpoints(app) in your main API file

