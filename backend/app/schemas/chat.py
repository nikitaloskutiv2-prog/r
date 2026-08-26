from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    name: Optional[str] = None


class FileResponse(BaseModel):
    id: int
    original_name: str
    mime_type: str
    path: str


class LastMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: Optional[str] = None
    created_at: datetime
    sender_id: int
    is_read: bool
    file: Optional[FileResponse] = None
    voice_duration: Optional[int] = None




class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    avatar: Optional[str] = None 
    is_private: bool = False
    members: list[int] = []
    last_message: Optional[LastMessageResponse] = None
    is_favorite: bool = False


class PrivateChatCreate(BaseModel):
    user_id: int
