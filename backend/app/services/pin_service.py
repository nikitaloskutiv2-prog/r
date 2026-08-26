from sqlalchemy.orm import Session

from app.models.pinned_message import PinnedMessage
from app.models.message import Message
from app.models.chat import Chat
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def pin_message(
    db: Session,
    chat_id: int,
    message_id: int,
    user_id: int
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.members.any(User.id == user_id)
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Pin message failed: chat not found or access denied "
            "chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            user_id,
        )
        return []
    
    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.chat_id == chat_id
        )
        .first()
    )

    if not message:
        logger.warning(
            "Pin message failed: message not found "
            "chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            user_id,
        )
        return None

    existing = (
        db.query(PinnedMessage)
        .filter(
            PinnedMessage.chat_id == chat_id,
            PinnedMessage.message_id == message_id
        )
        .first()
    )

    if existing:
        logger.info(
            "Message already pinned: chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            user_id,
        )
        return existing

    pin = PinnedMessage(
        chat_id=chat_id,
        message_id=message_id,
        pinned_by=user_id
    )

    db.add(pin)
    db.commit()
    db.refresh(pin)
    logger.info(
        "Message pinned: chat_id=%s message_id=%s user_id=%s pin_id=%s",
        chat_id,
        message_id,
        user_id,
        pin.id,
    )
    return pin


def unpin_message(
    db: Session,
    chat_id: int,
    message_id: int,
    user_id: int
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.members.any(User.id == user_id)
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Unpin message failed: chat not found or access denied "
            "chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            user_id,
        )
        return None
    
    pin = (
        db.query(PinnedMessage)
        .filter(
            PinnedMessage.chat_id == chat_id,
            PinnedMessage.message_id == message_id
        )
        .first()
    )

    if not pin:
        return False

    db.delete(pin)
    db.commit()
    logger.info(
        "Message unpinned: chat_id=%s message_id=%s user_id=%s",
        chat_id,
        message_id,
        user_id,
    )
    return True


def get_chat_pins(
    db: Session,
    chat_id: int,
    user_id: int
):
    chat = (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.members.any(User.id == user_id)
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Get chat pins failed: chat not found or access denied "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return []
    
    pins = (
        db.query(PinnedMessage)
        .join(
            Message,
            Message.id == PinnedMessage.message_id
        )
        .filter(
            PinnedMessage.chat_id == chat_id
        )
        .order_by(
            Message.created_at.desc()
        )
        .all()
    )

    logger.info(
        "Chat pins loaded: chat_id=%s user_id=%s count=%s",
        chat_id,
        user_id,
        len(pins),
    )

    return pins