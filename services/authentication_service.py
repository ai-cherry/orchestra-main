"""
Authentication Service
Handles all authentication logic following Single Responsibility Principle
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import asyncpg
from fastapi import HTTPException, status

class AuthenticationService:
    """Service for handling authentication operations"""
    
    def __init__(self, db_pool: asyncpg.Pool, config: Dict[str, Any]):
        self.db_pool = db_pool
        self.secret_key = config['secret_key']
        self.algorithm = config['algorithm']
        self.token_expire_hours = config['token_expire_hours']
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.token_expire_hours)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE username = $1 AND is_active = true",
                username
            )
            
            if not user or not self.verify_password(password, user['password_hash']):
                return None
            
            return dict(user)
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user from token"""
        payload = self.decode_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE id = $1 AND is_active = true",
                user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
        
        return dict(user)
