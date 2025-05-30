from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTStrategy
from fastapi_users.manager import BaseUserManager
from core.auth.models import User
from core.auth.db import AsyncSessionLocal

SECRET = "change-me"

class UserManager(BaseUserManager[User, str]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def get_by_email(self, email: str):
        return None

async def get_user_db():
    async with AsyncSessionLocal() as session:
        yield session

auth_router = APIRouter()

jwt = JWTStrategy(secret=SECRET, lifetime_seconds=3600)
fastapi_users = FastAPIUsers(UserManager(get_user_db), [jwt])

auth_router.include_router(fastapi_users.get_auth_router(jwt), prefix="/auth")
