from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id = Column(Integer, primary_key=True)

    blocker_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    blocked_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "blocker_id",
            "blocked_id",
            name="uq_user_block"
        ),
    )

    blocker = relationship(
        "User",
        foreign_keys=[blocker_id]
    )

    blocked = relationship(
        "User",
        foreign_keys=[blocked_id]
    )