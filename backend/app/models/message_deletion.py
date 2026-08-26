from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, Index
from app.db.base_class import Base
from datetime import datetime


class MessageDeletion(Base):
    __tablename__ = "message_deletions"

    id = Column(Integer, primary_key=True, index=True)

    message_id = Column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_message_deletion_user"
        ),
        Index(
            "idx_message_deletion_user",
            "user_id",
            "message_id"
        ),
    )