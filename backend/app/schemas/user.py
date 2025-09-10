from fastapi_users import schemas
from pydantic import BaseModel
from typing import Optional
import uuid


class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: bool = False


class UserCreate(schemas.BaseUserCreate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: bool = False


class UserUpdate(schemas.BaseUserUpdate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: Optional[bool] = None