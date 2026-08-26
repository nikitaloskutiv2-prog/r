from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from datetime import datetime

from app.db.base_class import Base


class File(Base):

    __tablename__ = "files"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    original_name = Column(
        String,
        nullable=False
    )

    stored_name = Column(
        String,
        nullable=False
    )

    path = Column(
        String,
        nullable=False
    )
    thumbnail_path = Column(
        String,
        nullable=True
    )
    mime_type = Column(
        String,
        nullable=False
    )

    size = Column(
        Integer,
        nullable=False
    )

    uploader_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )