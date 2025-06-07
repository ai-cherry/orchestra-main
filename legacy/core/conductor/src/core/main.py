"""
"""
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# API Models

class InteractionRequest(BaseModel):
    """Request model for interaction API."""
    message: str = Field(..., description="The user's message")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")
    persona_id: Optional[str] = Field(None, description="Persona identifier to use for this interaction")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the interaction")

class InteractionResponse(BaseModel):
    """Response model for interaction API."""
    message: str = Field(..., description="The response message")
    persona_id: str = Field(..., description="The persona identifier used")
    persona_name: str = Field(..., description="The persona name used")
    session_id: str = Field(..., description="The session identifier")
    interaction_id: str = Field(..., description="The interaction identifier")
    timestamp: str = Field(..., description="Timestamp of the interaction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class PersonaInfo(BaseModel):
    """Persona information model."""
    id: str = Field(..., description="The persona identifier")
    name: str = Field(..., description="The persona name")
    description: str = Field(..., description="The persona description")
    traits: List[str] = Field(default_factory=list, description="The persona traits")

class PersonaListResponse(BaseModel):
    """Response model for persona listing API."""
    personas: Dict[str, PersonaInfo] = Field(..., description="Dictionary of available personas")
    default_persona_id: str = Field(..., description="The default persona identifier")

# App Factory

def create_app() -> FastAPI:
    """
    """
        title="AI coordination System",
        description="API for AI coordination with personas and memory",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Define routes

    @app.post("/api/interact", response_model=InteractionResponse)
    async def interact(request: InteractionRequest):
        """
        """
            logger.error(f"Error processing interaction: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/personas", response_model=PersonaListResponse)
    async def list_personas():
        """
        """
            logger.error(f"Error listing personas: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/health")
    async def health_check():
        """
        """
            "status": "ok",
            "components": {"memory": "ok", "personas": "ok", "agents": "ok"},
        }

    return app

# Main entry point

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
