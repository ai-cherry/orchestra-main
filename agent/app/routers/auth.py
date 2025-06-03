"""
"""
router = APIRouter(prefix="/api", tags=["auth"])

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "orchestra-admin-jwt-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))  # 12 hours default

# Admin credentials from environment
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "orchestra-admin-2024")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@orchestra.ai")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_email: str

class TokenData(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class User(BaseModel):
    username: str
    email: str
    is_active: bool = True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    """Generate password hash."""
    """Authenticate user credentials."""
    """Create JWT access token."""
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token."""
        username: str = payload.get("sub")
        email: str = payload.get("email")
        if username is None:
            return None
        return TokenData(username=username, email=email)
    except Exception:

        pass
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token."""
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    # For single admin setup, return admin user if token is valid
    if token_data.username == ADMIN_USERNAME:
        return User(username=ADMIN_USERNAME, email=ADMIN_EMAIL)
    
    raise credentials_exception

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns JWT access token."""
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user_email=user.email
    )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
@router.post("/verify")
async def verify_access_token(request: dict):
    """Verify if a token is valid."""
    token = request.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "username": token_data.username,
        "email": token_data.email
    }

@router.post("/refresh")
async def refresh_access_token(current_user: User = Depends(get_current_user)):
    """Refresh access token for authenticated user."""
        data={"sub": current_user.username, "email": current_user.email},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_email=current_user.email
    ) 