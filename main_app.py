import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import litellm

try:
    from core.logging_config import get_logger, setup_logging
    # Set up structured JSON logging
    # Determine if running in production (Cloud Run) or development
    is_production = os.environ.get("K_SERVICE") is not None
    setup_logging(json_format=is_production)
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging config not available
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestra AI API", version="1.0.0")

# Pydantic models for request/response
class QueryRequest(BaseModel):
    user_id: Optional[str] = None
    query: str

class LLMRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"

@app.get("/")
async def home():
    return {
        "status": "success",
        "message": "Orchestra AI deployment successful!",
        "environment": "Development",
        "project": os.environ.get("LAMBDA_PROJECT_ID", "local"),
        "service_account": os.environ.get("GOOGLE_SERVICE_ACCOUNT", "none"),
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/info")
async def info():
    return {
        "app": "Orchestra AI",
        "version": "1.0.0",
        "framework": "FastAPI",
        "python_version": "3.10",
    }

@app.post("/query")
async def handle_query(request: QueryRequest):
    logger.info("User query received", extra={"user_id": request.user_id, "query_length": len(request.query)})
    return {"status": "ok", "message": "Query received"}

@app.post("/call-llm")
async def call_llm(request: LLMRequest):
    try:
        # Use litellm for LLM API calls
        response = litellm.completion(
            model=request.model, 
            messages=[{"role": "user", "content": request.prompt}]
        )
        
        logger.info("LLM API call successful", extra={"model": request.model})
        return {
            "status": "success", 
            "response": response.choices[0].message.content
        }
    except Exception as e:
        logger.error(
            "LLM API call failed",
            exc_info=True,
            extra={"api_endpoint": request.model, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="LLM API call failed")

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "app": "running",
            "gcp_project": os.environ.get("LAMBDA_PROJECT_ID", "not_set"),
            "api_keys_loaded": {
                "openai": bool(os.environ.get("OPENAI_API_KEY")),
                "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            },
        },
    }
    return health_status

@app.exception_handler(Exception)
async def handle_exception(request, exc):
    # Don't expose stack traces in production
    is_production = os.environ.get("K_SERVICE") is not None
    
    if is_production:
        logger.error(
            "Unhandled exception",
            exc_info=True,  # Log full details server-side
            extra={"path": str(request.url), "method": request.method},
        )
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
    else:
        # In development, return more details
        logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={
                "path": str(request.url),
                "method": request.method,
                "client": request.client.host if request.client else None,
            },
        )
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
