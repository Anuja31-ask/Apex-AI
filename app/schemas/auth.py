from pydantic import BaseModel, EmailStr
from uuid import UUID


class UserRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "ENGINEER"


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"