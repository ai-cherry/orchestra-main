"""
Simple auth endpoints for the orchestrator API.
"""

import os
from datetime import datetime, timedelta
from typing import Dict

import jwt
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "orchestra-admin-jwt-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720  # 12 hours

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_email: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/token", response_model=Token)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token endpoint."""
    if form_data.username == "scoobyjava" and form_data.password == "Huskers1983$":
        access_token = jwt.encode(
            {
                "sub": form_data.username,
                "email": "admin@orchestra.ai",
                "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_email="admin@orchestra.ai"
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/auth/login")
async def login_json(credentials: LoginRequest):
    """JSON login endpoint for frontend compatibility."""
    if credentials.username == "scoobyjava" and credentials.password == "Huskers1983$":
        access_token = jwt.encode(
            {
                "sub": credentials.username,
                "email": "admin@orchestra.ai",
                "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_email": "admin@orchestra.ai"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me")
async def get_current_user():
    """Get current user info - simplified version."""
    return {
        "username": "scoobyjava",
        "email": "admin@orchestra.ai",
        "is_active": True
    }