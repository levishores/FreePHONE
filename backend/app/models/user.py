from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import String as SQLString
from app.database import Base
import uuid


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
    
    first_name = Column(String(50))
    last_name = Column(String(50))
    department = Column(String(100))
    is_admin = Column(Boolean, default=False)
    
    # Relationship to extensions
    extensions = relationship("Extension", back_populates="user")


class Extension(Base):
    __tablename__ = "extensions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    extension_number = Column(String(20), unique=True, nullable=False)
    display_name = Column(String(100))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", back_populates="extensions")
    calls = relationship("Call", foreign_keys="Call.extension_id", back_populates="extension")