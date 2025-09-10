from pydantic import BaseModel
from typing import Optional
import uuid


class ExtensionBase(BaseModel):
    extension_number: str
    display_name: Optional[str] = None
    is_active: bool = True


class ExtensionCreate(ExtensionBase):
    user_id: Optional[str] = None


class ExtensionUpdate(BaseModel):
    extension_number: Optional[str] = None
    display_name: Optional[str] = None
    user_id: Optional[str] = None
    is_active: Optional[bool] = None


class ExtensionRead(ExtensionBase):
    id: str
    user_id: Optional[str] = None
    
    class Config:
        from_attributes = True