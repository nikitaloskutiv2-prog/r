from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint
)

from datetime import datetime
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class PinnedMessage(Base):
    __tablename__ = "pinned_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    chat_id = Column(
        Integer,
        ForeignKey("chats.id"),
        nullable=False
    )

    message_id = Column(
        Integer,
        ForeignKey("messages.id"),
        nullable=False
    )

    pinned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    chat = relationship("Chat")
    message = relationship("Message")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "chat_id",
            "message_id",
            name="uq_chat_message_pin"
        ),
    )