from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime


class Call(Base):
    __tablename__ = "calls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uuid = Column(String(100), unique=True, nullable=False)  # FreeSWITCH call UUID
    direction = Column(String(20))  # inbound, outbound, internal
    caller_id_number = Column(String(50))
    caller_id_name = Column(String(100))
    destination_number = Column(String(50))
    extension_id = Column(UUID(as_uuid=True), ForeignKey("extensions.id"))
    state = Column(String(50))  # NEW, RINGING, ACTIVE, HELD, PARKED, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    park_orbit = Column(String(20), nullable=True)
    conference_id = Column(UUID(as_uuid=True), ForeignKey("conferences.id"), nullable=True)
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    extension = relationship("Extension", back_populates="calls")
    conference = relationship("Conference", back_populates="calls")


class Conference(Base):
    __tablename__ = "conferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    room_number = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    max_participants = Column(Integer, default=50)
    
    # Relationships
    calls = relationship("Call", back_populates="conference")


class ParkOrbit(Base):
    __tablename__ = "park_orbits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orbit_number = Column(String(20), unique=True, nullable=False)
    is_occupied = Column(Boolean, default=False)
    occupied_by_call_uuid = Column(String(100), nullable=True)
    parked_at = Column(DateTime, nullable=True)
