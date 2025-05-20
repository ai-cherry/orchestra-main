# Placeholder for FastAPI app definition
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Agent up"}
