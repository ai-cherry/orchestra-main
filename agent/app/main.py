"""
Orchestra AI FastAPI Application
Main entry point for the Orchestra API server
"""

import os
import time

import structlog
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Import routers
from agent.app.routers.admin import router as admin_router
from agent.app.routers.agents import router as agents_router
from agent.app.routers.workflows import router as workflows_router
from agent.app.routers.resources import router as resources_router
from agent.app.routers.system import router as system_router
from agent.app.routers.audit import router as audit_router
from agent.app.routers.automation import router as automation_router
from agent.app.routers.natural_language import router as natural_language_router
from agent.app.routers.intent import router as intent_router
from agent.app.routers.suggestions import router as suggestions_router
from agent.app.routers.llm import router as llm_router
from agent.app.routers.personas_admin import router as personas_admin_router
from agent.app.routers.llm_admin import router as llm_admin_router
from agent.app.routers.llm_orchestration import router as llm_orchestration_router

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

app = FastAPI(title="Orchestra API", version="1.0.0")

# Include the admin router
app.include_router(admin_router)
app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(resources_router)
app.include_router(system_router)
app.include_router(audit_router)
app.include_router(automation_router)
app.include_router(natural_language_router)
app.include_router(intent_router)
app.include_router(suggestions_router)
app.include_router(llm_router)
app.include_router(personas_admin_router)
app.include_router(llm_admin_router)
app.include_router(llm_orchestration_router)

# Middleware for logging requests and latency

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request_received", method=request.method, path=request.url.path)
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # in milliseconds
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=f"{process_time:.2f}",
    )
    return response

class QueryRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("health_check_accessed")
    return {"status": "ok"}

@app.post("/query")
async def process_query(query_request: QueryRequest):
    """Processes a query prompt by calling OpenAI ChatCompletion."""
    logger.info("query_endpoint_called", prompt=query_request.prompt)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("openai_api_key_not_found")
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured.")

    # TODO: Implement actual OpenAI ChatCompletion call
    # For now, we'll just simulate a response.
    # Example (replace with actual openai client usage):
    # try:
    #     client = openai.OpenAI(api_key=api_key)
    #     chat_completion = await client.chat.completions.create( # Use await if using async client
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": query_request.prompt,
    #             }
    #         ],
    #         model="gpt-3.5-turbo", # Or your preferred model
    #     )
    #     response_content = chat_completion.choices[0].message.content
    #     logger.info("openai_call_successful")
    #     return {"response": response_content}
    # except Exception as e:
    #     logger.error("openai_call_failed", error=str(e))
    #     raise HTTPException(status_code=500, detail=f"Error communicating with OpenAI: {str(e)}")

    logger.info("openai_call_mocked")
    return {
        "response": f"Mock response to prompt: '{query_request.prompt}' using API key ending with ...{api_key[-4:] if api_key else 'N/A'}"
    }

# Initialize an __init__.py file in the app directory if it doesn't exist,
# to ensure the module can be found by Uvicorn.
# This will be done as a separate step if needed.

if __name__ == "__main__":
    # This part is for local development and debugging,
    # Uvicorn will run the app directly in production.
    import uvicorn

    logger.info("starting_uvicorn_dev_server", host="0.0.0.0", port=8080)
    uvicorn.run(app, host="0.0.0.0", port=8080)
