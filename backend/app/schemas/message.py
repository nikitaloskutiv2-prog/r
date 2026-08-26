from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    chat_id: int
    content: Optional[str] = None
    file_id: Optional[int] = None
    reply_to_id: Optional[int] = None
    voice_duration: int | None = None
    waveform: Optional[list[int]] = None



class FileInfo(BaseModel):
    id: int
    path: str
    thumbnail_path: Optional[str] = None
    mime_type: str
    original_name: str
    size: int

    class Config:
        from_attributes = True

class ReplyMessageResponse(BaseModel):
    id: int
    content: Optional[str] = None
    sender_id: int
    file: Optional[FileInfo] = None
    voice_duration: Optional[int] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    content: Optional[str] = None

    voice_duration: Optional[int] = None
    waveform: list[int] | None = None
    voice_played: Optional[bool] = False

    reactions: dict | None = None

    reply_to_id: Optional[int] = None
    reply_to: Optional[ReplyMessageResponse] = None
    edited: bool = False

    created_at: datetime
    is_read: bool = False
    read_at: Optional[datetime] = None

    file_id: Optional[int] = None
    file: Optional[FileInfo] = None

    class Config:
        from_attributes = True

class MarkMessageAsReadRequest(BaseModel):
    """Запрос на отметить сообщение как прочитанное"""
    pass

class UnreadCountResponse(BaseModel):
    """Ответ с количеством непрочитанных сообщений"""
    chat_id: int
    unread_count: int



