from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FileResponse(BaseModel):
    id: int
    original_name: str
    path: str
    thumbnail_path: Optional[str] = None
    mime_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True