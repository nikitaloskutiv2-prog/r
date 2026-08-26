# app/models/reaction.py

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    UniqueConstraint
)

from app.db.base_class import Base


class MessageReaction(Base):

    __tablename__ = "message_reactions"

    id = Column(
        Integer,
        primary_key=True
    )

    message_id = Column(
        Integer,
        ForeignKey("messages.id")
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    emoji = Column(
        String(10)
    )

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_message_user_reaction"
        ),
    )