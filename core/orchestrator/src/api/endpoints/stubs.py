"""
"""
    status: str = "active"
    created_at: str
    updated_at: str

class Persona(BaseModel):
    id: str
    name: str
    description: str
    avatar: str = ""
    traits: Dict[str, Any] = {}
    is_active: bool = True
    created_at: str
    updated_at: str

class Workflow(BaseModel):
    id: str
    name: str
    description: str
    status: str = "active"
    steps: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str

@router.get("/agents", response_model=List[Agent])
async def get_agents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None)
):
    """Return empty list of agents to prevent frontend crash."""
@router.get("/personas", response_model=List[Persona])
async def get_personas(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Return empty list of personas to prevent frontend crash."""
@router.get("/workflows", response_model=List[Workflow])
async def get_workflows(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(None)
):
    """Return empty list of workflows to prevent frontend crash."""
@router.get("/integrations")
async def get_integrations():
    """Return empty list of integrations to prevent frontend crash."""
@router.get("/resources")
async def get_resources():
    """Return empty list of resources to prevent frontend crash."""
@router.get("/logs")
async def get_logs(limit: int = Query(50, ge=1, le=1000)):
    """Return empty list of logs to prevent frontend crash."""
@router.get("/query")
async def query_endpoint():
    """Return empty query response to prevent frontend crash."""
    return {"results": [], "status": "ok"}

@router.post("/query")
async def query_post_endpoint(body: Dict[str, Any]):
    """Return empty query response to prevent frontend crash."""
    return {"results": [], "status": "ok", "query": body.get("query", "")}

@router.get("/upload")
async def get_upload():
    """Return empty upload response to prevent frontend crash."""
    return {"uploads": [], "status": "ok"}