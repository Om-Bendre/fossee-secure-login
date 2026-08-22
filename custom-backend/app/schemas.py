from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    user: dict

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    profile: dict

class FileOut(BaseModel):
    id: UUID
    ownerId: UUID
    fileName: str
    mimeType: str
    sizeBytes: int
    uploadedAt: datetime | None
