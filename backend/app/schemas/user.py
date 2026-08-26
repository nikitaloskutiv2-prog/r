from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    login: str
    username: str
    password: str


class UserLogin(BaseModel):
    login: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=100)
    usernameid: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=150)
    birthday: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    usernameid: Optional[str] = None
    accountid: str
    bio: str
    birthday: str
    avatar: Optional[str] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


class UserSearchResponse(BaseModel):
    id: int
    username: str
    usernameid: str
    bio: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    status: str
    last_seen: str