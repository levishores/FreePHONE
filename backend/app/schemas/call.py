from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class CallBase(BaseModel):
    uuid: str
    direction: Optional[str] = None
    caller_id_number: Optional[str] = None
    caller_id_name: Optional[str] = None
    destination_number: Optional[str] = None
    state: Optional[str] = None


class CallCreate(CallBase):
    extension_id: Optional[str] = None
    conference_id: Optional[str] = None
    call_metadata: Optional[Dict[str, Any]] = {}


class CallUpdate(BaseModel):
    direction: Optional[str] = None
    caller_id_number: Optional[str] = None
    caller_id_name: Optional[str] = None
    destination_number: Optional[str] = None
    state: Optional[str] = None
    extension_id: Optional[str] = None
    conference_id: Optional[str] = None
    park_orbit: Optional[str] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    call_metadata: Optional[Dict[str, Any]] = None


class CallRead(CallBase):
    id: str
    extension_id: Optional[str] = None
    conference_id: Optional[str] = None
    park_orbit: Optional[str] = None
    created_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    call_metadata: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True


class CallTransferRequest(BaseModel):
    uuid: str
    destination: str


class CallParkRequest(BaseModel):
    uuid: str
    orbit: str


class CallHangupRequest(BaseModel):
    uuid: str