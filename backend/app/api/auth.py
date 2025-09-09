import uuid
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTAuthentication,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

# Bearer token transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# JWT authentication
jwt_authentication = JWTAuthentication(
    secret=settings.secret_key,
    lifetime_seconds=3600,
    tokenUrl="auth/jwt/login",
)

# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=jwt_authentication.get_strategy,
)


async def get_user_db(session: AsyncSession = next(get_async_session())):
    yield SQLAlchemyUserDatabase(session, User)


# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_db,
    [auth_backend],
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
