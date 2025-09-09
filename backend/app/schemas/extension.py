from pydantic import BaseModel
from typing import Optional
import uuid


class ExtensionBase(BaseModel):
    extension_number: str
    display_name: Optional[str] = None
    is_active: bool = True


class ExtensionCreate(ExtensionBase):
    user_id: Optional[uuid.UUID] = None


class ExtensionUpdate(BaseModel):
    extension_number: Optional[str] = None
    display_name: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class ExtensionRead(ExtensionBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    
    class Config:
        from_attributes = True
