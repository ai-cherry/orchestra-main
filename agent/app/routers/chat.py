# Placeholder for chat router
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def handle_chat():
    return {"response": "Hello from chat"}
