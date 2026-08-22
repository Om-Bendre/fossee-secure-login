import uuid
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    display_name = Column(String(255), default="")
    bio = Column(Text, default="")
    role = Column(String(50), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, default=0)
    storage_path = Column(String(1000), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    owner = relationship("User", back_populates="files")

class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    jti = Column(UUID(as_uuid=True), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
