"""Authentication utilities for Cherry AI"""

import os
import logging
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from typing_extensions import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "10080"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def create_admin_user(username: str, password: str, email: str) -> Dict[str, Any]:
    """Create an admin user in the database"""
    from src.database import UnifiedDatabase
    
    db = UnifiedDatabase()
    
    try:
        # Check if user already exists
        # TODO: Run EXPLAIN ANALYZE on this query
        existing = await db.execute(
            "SELECT id FROM users WHERE username = :username",
            {"username": username}
        )
        
        if existing:
            logger.info(f"Admin user {username} already exists")
            return {"status": "exists", "username": username}
        
        # Create the user
        hashed_password = get_password_hash(password)
        user_id = await db.insert("users", {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "is_admin": True,
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"Created admin user {username} with ID {user_id}")
        return {
            "status": "created",
            "username": username,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        await db.close()