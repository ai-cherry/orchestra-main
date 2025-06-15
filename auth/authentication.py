"""
Orchestra AI - Secure Authentication System
Implements JWT-based authentication with proper user validation
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from security.secret_manager import secret_manager

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = secret_manager.get_secret("JWT_SECRET_KEY")
if not SECRET_KEY:
    # Generate a secure random key if none exists
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
    secret_manager.set_local_secret("JWT_SECRET_KEY", SECRET_KEY)
    
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class User:
    def __init__(self, user_id: str, username: str, email: str, is_active: bool = True):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.is_active = is_active

# Mock user database - replace with real database in production
USERS_DB = {
    "admin": {
        "user_id": "admin-001",
        "username": "admin",
        "email": "admin@orchestra-ai.com",
        "hashed_password": pwd_context.hash("admin123"),  # Change in production
        "is_active": True
    },
    "demo": {
        "user_id": "demo-001", 
        "username": "demo",
        "email": "demo@orchestra-ai.com",
        "hashed_password": pwd_context.hash("demo123"),  # Change in production
        "is_active": True
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[dict]:
    """Get user from database"""
    return USERS_DB.get(username)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user credentials"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validate JWT token and return current user ID
    Replaces the insecure placeholder implementation
    """
    try:
        # Decode JWT token
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise AuthenticationError("Invalid token: missing subject")
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise AuthenticationError("Token has expired")
            
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    
    # Get user from database
    user = get_user(username)
    if user is None:
        raise AuthenticationError("User not found")
        
    if not user["is_active"]:
        raise AuthenticationError("User account is disabled")
        
    return user["user_id"]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user object"""
    user_id = await get_current_user_id(credentials)
    
    # Find user by ID
    for username, user_data in USERS_DB.items():
        if user_data["user_id"] == user_id:
            return User(
                user_id=user_data["user_id"],
                username=user_data["username"], 
                email=user_data["email"],
                is_active=user_data["is_active"]
            )
    
    raise AuthenticationError("User not found")

# Optional: Admin-only access
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

