from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from app.models.message import Message
from app.schemas.message import MessageCreate
from datetime import datetime
from typing import Dict
from app.models.reaction import MessageReaction
from app.services import block_service
from fastapi import HTTPException
from app.models.chat import Chat
from app.models.message_deletion import MessageDeletion
from app.models.chat_deletion import ChatDeletion
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def send_message(
    db: Session,
    message_data: MessageCreate,
    sender_id: int
) -> Message:

    chat = (
        db.query(Chat)
        .options(joinedload(Chat.members))
        .filter(
            Chat.id == message_data.chat_id,
            Chat.members.any(User.id == sender_id)
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Send message failed: chat not found or access denied "
            "chat_id=%s sender_id=%s",
            message_data.chat_id,
            sender_id,
        )
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    other_user_id = None

    for members in chat.members:

        if members.id != sender_id:
            other_user_id = members.id
            break

    if other_user_id:

        if block_service.are_users_blocked(
            db,
            sender_id,
            other_user_id
        ):
            logger.warning(
                "Send message blocked: sender_id=%s other_user_id=%s chat_id=%s",
                sender_id,
                other_user_id,
                message_data.chat_id,
            )
            raise HTTPException(
                status_code=403,
                detail="User is blocked"
            )

    new_message = Message(
        chat_id=message_data.chat_id,
        content=message_data.content,
        file_id=message_data.file_id,
        sender_id=sender_id,
        reply_to_id=message_data.reply_to_id,
        voice_duration=message_data.voice_duration,
        waveform=message_data.waveform,
        is_read=False
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    logger.info(
        "Message sent: message_id=%s chat_id=%s sender_id=%s "
        "file_id=%s reply_to_id=%s",
        new_message.id,
        new_message.chat_id,
        sender_id,
        new_message.file_id,
        new_message.reply_to_id,
    )
    return new_message

def get_messages(
    db: Session,
    chat_id: int,
    user_id: int,
    limit: int = 50,
    before_id: int | None = None
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
            "Get messages failed: chat not found or access denied "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )
    
    deleted_message_ids = (
        db.query(MessageDeletion.message_id)
        .filter(
            MessageDeletion.user_id == user_id
        )
        .subquery()
    )

    chat_deletion = (
        db.query(ChatDeletion)
        .filter(
            ChatDeletion.chat_id == chat_id,
            ChatDeletion.user_id == user_id
        )
        .first()
    )

    query = (
        db.query(Message)
        .options(
            joinedload(Message.file),

            joinedload(Message.reply_to)
            .joinedload(Message.file)
        )
        .filter(
            Message.chat_id == chat_id,
            ~Message.id.in_(deleted_message_ids)
        )
    )

    if before_id:
        query = query.filter(
            Message.id < before_id
        )
    
    if chat_deletion:
        query = query.filter(
            Message.created_at > chat_deletion.created_at
        )

    messages = (
        query
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )

    messages.reverse()

    logger.info(
        "Messages loaded: chat_id=%s user_id=%s count=%s limit=%s before_id=%s",
        chat_id,
        user_id,
        len(messages),
        limit,
        before_id,
    )

    message_ids = [m.id for m in messages]

    all_reactions = []

    if message_ids:
        all_reactions = (
            db.query(MessageReaction)
            .filter(
                MessageReaction.message_id.in_(message_ids)
            )
            .all()
        )

    reactions_map = {}

    for reaction in all_reactions:

        msg_reactions = reactions_map.setdefault(
            reaction.message_id,
            {}
        )

        emoji_data = msg_reactions.setdefault(
            reaction.emoji,
            {
                "count": 0,
                "users": set()
            }
        )

        emoji_data["count"] += 1
        emoji_data["users"].add(
            reaction.user_id
        )

    result = []

    for msg in messages:

        raw_reactions = reactions_map.get(
            msg.id,
            {}
        )

        reactions = {}

        for emoji, data in raw_reactions.items():

            reactions[emoji] = {
                "count": data["count"],
                "mine": user_id in data["users"]
            }

        result.append({

            "id": msg.id,
            "chat_id": msg.chat_id,
            "sender_id": msg.sender_id,

            "content": msg.content,

            "voice_duration": msg.voice_duration,
            "waveform": msg.waveform,
            "voice_played": msg.voice_played,

            "file_id": msg.file_id,

            "reactions": reactions,

            "file": (
                {
                    "id": msg.file.id,
                    "path": msg.file.path,
                    "mime_type": msg.file.mime_type,
                    "original_name": msg.file.original_name,
                    "thumbnail_path": msg.file.thumbnail_path,
                    "size": msg.file.size,
                }
                if msg.file
                else None
            ),

            "reply_to_id": msg.reply_to_id,

            "reply_to": (
                {
                    "id": msg.reply_to.id,
                    "content": msg.reply_to.content,
                    "sender_id": msg.reply_to.sender_id,
                    "voice_duration": msg.reply_to.voice_duration,

                    "file": (
                        {
                            "id": msg.reply_to.file.id,
                            "original_name": msg.reply_to.file.original_name,
                            "mime_type": msg.reply_to.file.mime_type,
                            "path": msg.reply_to.file.path,
                            "thumbnail_path": msg.reply_to.file.thumbnail_path,
                            "size": msg.reply_to.file.size,
                        }
                        if msg.reply_to.file
                        else None
                    )
                }
                if msg.reply_to
                else None
            ),

            "edited": msg.edited,

            "created_at": msg.created_at,
            "is_read": msg.is_read,
            "read_at": msg.read_at

        })

    return result


def mark_message_as_read(
    db: Session,
    message_id: int,
    user_id: int
) -> Message:

    message = (
        db.query(Message)
        .join(Chat, Chat.id == Message.chat_id)
        .filter(
            Message.id == message_id,
            Chat.members.any(User.id == user_id),
            Message.sender_id != user_id
        )
        .first()
    )

    if message:
        message.is_read = True
        message.read_at = datetime.utcnow()

        db.commit()
        db.refresh(message)
        logger.info(
            "Message marked as read: message_id=%s user_id=%s",
            message.id,
            user_id,
        )
    return message

# ✅ Отметить все сообщения в чате как прочитанные
def mark_chat_as_read(
    db: Session,
    chat_id: int,
    user_id: int
) -> Dict:

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
            "Mark chat as read failed: chat not found or access denied "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        raise HTTPException(
            status_code=404,
            detail="Chat not found"
        )

    updated_at = datetime.utcnow()

    count = (
        db.query(Message)
        .filter(
            Message.chat_id == chat_id,
            Message.is_read.is_(False),
            Message.sender_id != user_id
        )
        .update(
            {
                Message.is_read: True,
                Message.read_at: updated_at
            },
            synchronize_session=False
        )
    )

    db.commit()
    logger.info(
        "Chat marked as read: chat_id=%s user_id=%s marked_count=%s",
        chat_id,
        user_id,
        count,
    )
    return {
        "chat_id": chat_id,
        "marked_count": count
    }

# ✅ Получить количество непрочитанных сообщений для каждого чата
def get_unread_counts(
    db: Session,
    user_id: int
) -> Dict[int, int]:

    results = (
        db.query(
            Message.chat_id,
            func.count(Message.id).label("unread_count")
        )
        .join(
            Chat,
            Chat.id == Message.chat_id
        )
        .filter(
            Chat.members.any(User.id == user_id),
            Message.is_read.is_(False),
            Message.sender_id != user_id
        )
        .group_by(Message.chat_id)
        .all()
    )
    logger.info(
        "Unread counts loaded: user_id=%s chat_count=%s",
        user_id,
        len(results),
    )
    return {
        chat_id: count
        for chat_id, count in results
    }

def mark_voice_played(
    db: Session,
    message_id: int,
    user_id: int
) -> Message:

    message = (
        db.query(Message)
        .join(Chat, Chat.id == Message.chat_id)
        .filter(
            Message.id == message_id,
            Chat.members.any(User.id == user_id),
            Message.sender_id != user_id
        )
        .first()
    )

    if message and not message.voice_played:
        message.voice_played = True
        db.commit()
        db.refresh(message)
        logger.info(
            "Voice message marked as played: message_id=%s user_id=%s",
            message.id,
            user_id,
        )
    return message