from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.schemas.chat import ChatResponse, PrivateChatCreate
from app.services import chat_service, pin_service
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.message import Message
from app.models.message_deletion import MessageDeletion
from app.websocket.chat_ws import manager, notification_manager

from app.models.chat import Chat
from app.models.user import User
import logging

router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

logger = logging.getLogger(__name__)

@router.get("/", response_model=List[ChatResponse])
def get_my_chats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    chats = chat_service.get_user_chats(
        db,
        current_user.id
    )
    chat_ids = [chat.id for chat in chats]
    result = []
    deleted_rows = (
        db.query(
            MessageDeletion.message_id,
            Message.chat_id
        )
        .join(
            Message,
            Message.id == MessageDeletion.message_id
        )
        .filter(
            MessageDeletion.user_id == current_user.id,
            Message.chat_id.in_(chat_ids)
        )
        .all()
    )
    deleted_message_ids_by_chat = {}

    for message_id, chat_id in deleted_rows:

        deleted_message_ids_by_chat.setdefault(
            chat_id,
            set()
        ).add(message_id)

    for chat in chats:

        deleted_message_ids = (
            deleted_message_ids_by_chat.get(
                chat.id,
                set()
            )
        )

        chat_name = chat_service.get_chat_name(
            chat,
            current_user.id
        )

        last_message = None
        chat_avatar = None

        other_user = None

        if chat.is_favorite:
            chat_avatar = "/storage/bookmark.png"

        elif chat.is_private:

            other_user = next(
                (
                    member
                    for member in chat.members
                    if member.id != current_user.id
                ),
                None
            )

            if other_user:
                chat_avatar = other_user.avatar


        visible_messages = [
            message
            for message in chat.messages
            if message.id not in deleted_message_ids
        ]

        if visible_messages:
            msg = max(
                visible_messages,
                key=lambda m: m.created_at
            )

            last_message = {
                "id": msg.id,
                "content": msg.content,
                "created_at": msg.created_at,
                "sender_id": msg.sender_id,
                "is_read": msg.is_read,
                "voice_duration": msg.voice_duration,
                "file": None
            }

            if msg.file:
                last_message["file"] = {
                    "id": msg.file.id,
                    "original_name": msg.file.original_name,
                    "mime_type": msg.file.mime_type,
                    "path": msg.file.path,
                    "voice_duration": msg.voice_duration,
                }
            

        result.append({
            "id": chat.id,
            "name": chat_name,
            "is_private": chat.is_private,
            "is_favorite": chat.is_favorite,
            "members": [
                member.id
                for member in chat.members
            ],
            "last_message": last_message,
            "avatar": chat_avatar,
            "deleted": (
                other_user is not None
                and getattr(other_user, "is_deleted", False)
            ),
        })

    return result

@router.post("/private", response_model=ChatResponse)
def create_or_get_private_chat(
    data: PrivateChatCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Получить существующий чат.

    Если пользователь ранее удалил этот чат,
    старый чат не восстанавливаем.
    """

    chat = chat_service.get_or_create_private_chat(
        db,
        current_user.id,
        data.user_id
    )

    logger.info(
        "Private chat accessed: user_id=%s target_user_id=%s chat_id=%s",
        current_user.id,
        data.user_id,
        chat.id if chat else None,
    )

    if chat is None:
        return {
            "id": None,
            "name": "",
            "avatar": None,
            "is_private": True,
            "deleted": False,
            "members": []
        }

    chat_name = chat_service.get_chat_name(
        chat,
        current_user.id
    )

    other_user = next(
        (
            member
            for member in chat.members
            if member.id != current_user.id
        ),
        None
    )

    return {
        "id": chat.id,
        "name": chat_name,
        "avatar": other_user.avatar if other_user else None,
        "is_private": chat.is_private,
        "members": [
            member.id
            for member in chat.members
        ]
    }

@router.post("/favorite", response_model=ChatResponse)
def create_or_get_favorite_chat(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    chat = chat_service.get_or_create_favorite_chat(
        db,
        current_user.id
    )

    if not chat:
        logger.error(
            "Failed to create favorite chat: user_id=%s",
            current_user.id,
        )

        raise HTTPException(
            status_code=500,
            detail="Не удалось создать Избранное"
        )
    
    logger.info(
        "Favorite chat accessed: user_id=%s chat_id=%s",
        current_user.id,
        chat.id,
    )

    return {
        "id": chat.id,
        "name": "Избранное",
        "avatar": "/storage/bookmark.png",
        "is_private": True,
        "is_favorite": True,
        "members": [current_user.id],
        "last_message": None
    }

@router.delete("/{chat_id}/delete-for-me")
def delete_chat_for_me(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    success = chat_service.delete_chat_for_me(
        db,
        chat_id,
        current_user.id
    )

    if not success:
        logger.warning(
            "Chat deletion for user failed: chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )
        return {
            "success": False,
            "detail": "Чат не найден"
        }
    
    logger.info(
        "Chat deleted for user: chat_id=%s user_id=%s",
        chat_id,
        current_user.id,
    )
    return {
        "success": True
    }


@router.delete("/{chat_id}/delete-for-all")
async def delete_chat_for_all(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Получаем чат ДО удаления,
    # чтобы запомнить обоих участников
    chat = (
        db.query(Chat)
        .options(joinedload(Chat.members))
        .filter(
            Chat.id == chat_id,
            Chat.members.any(
                User.id == current_user.id
            )
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Delete chat for all failed: chat not found "
            "chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )
        return {
            "success": False,
            "detail": "Не удалось удалить чат"
        }

    if not chat.is_private:
        logger.warning(
            "Delete chat for all rejected: chat is not private "
            "chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )
        return {
            "success": False,
            "detail": "Удаление для всех доступно только для личных чатов"
        }

    if chat.is_favorite:
        logger.warning(
            "Delete chat for all rejected: favorite chat "
            "chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )
        return {
            "success": False,
            "detail": "Избранное можно удалить только у себя"
        }

    if len(chat.members) != 2:
        logger.warning(
            "Delete chat for all rejected: invalid member count "
            "chat_id=%s user_id=%s members=%s",
            chat_id,
            current_user.id,
            len(chat.members),
        )
        return {
            "success": False,
            "detail": "Некорректный приватный чат"
        }

    # Запоминаем участников ДО удаления
    member_ids = [
        member.id
        for member in chat.members
    ]

    # Удаляем чат через service
    success = chat_service.delete_chat_for_all(
        db,
        chat_id,
        current_user.id
    )

    if not success:
        logger.error(
            "Delete chat for all failed in service: "
            "chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )
        return {
            "success": False,
            "detail": "Не удалось удалить чат"
        }

    # Очень важно:
    # сообщаем каждому участнику,
    # что чат удалён для всех
    for member_id in member_ids:

        await notification_manager.send_to_user(
            member_id,
            {
                "type": "chat_deleted",
                "chat_id": chat_id,
                "delete_for": "all",
                "user_id": current_user.id
            }
        )

    logger.info(
        "Chat deleted for all: chat_id=%s user_id=%s members=%s",
        chat_id,
        current_user.id,
        member_ids,
    )
    return {
        "success": True
    }



@router.post("/{chat_id}/pins")
async def pin_message(
    chat_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    pin = pin_service.pin_message(
        db,
        chat_id,
        data["message_id"],
        current_user.id
    )

    if pin:

        await manager.broadcast(
            chat_id,
            {
                "type": "message_pinned"
            }
        )
        logger.info(
            "Message pinned: chat_id=%s message_id=%s user_id=%s",
            chat_id,
            data["message_id"],
            current_user.id,
        )
    else:
        logger.warning(
            "Message pin failed: chat_id=%s message_id=%s user_id=%s",
            chat_id,
            data["message_id"],
            current_user.id,
        )
    return {
        "success": pin is not None
    }

@router.delete("/{chat_id}/pins/{message_id}")
async def unpin_message(
    chat_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    success = pin_service.unpin_message(
        db,
        chat_id,
        message_id,
        current_user.id
    )

    if success:
        logger.info(
            "Message unpinned: chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            current_user.id,
        )
        await manager.broadcast(
            chat_id,
            {
                "type": "message_unpinned"
            }
        )
    else:
        logger.warning(
            "Message unpin failed: chat_id=%s message_id=%s user_id=%s",
            chat_id,
            message_id,
            current_user.id,
        )
    return {
        "success": success
    }


@router.get("/{chat_id}/pins")
def get_chat_pins(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    pins = pin_service.get_chat_pins(
        db,
        chat_id,
        current_user.id
    )

    message_ids = [
        pin.message_id
        for pin in pins
    ]

    messages = (
        db.query(Message)
        .options(
            joinedload(Message.file)
        )
        .filter(
            Message.id.in_(message_ids)
        )
        .all()
    )

    messages_map = {
        message.id: message
        for message in messages
    }

    result = []

    for pin in pins:

        msg = messages_map.get(
            pin.message_id
        )

        if not msg:
            continue

        result.append(
            {
                "message_id": msg.id,
                "content": msg.content,
                "sender_id": msg.sender_id,
                "created_at": msg.created_at.isoformat(),
                "voice_duration": msg.voice_duration,
                "file": (
                    {
                        "id": msg.file.id,
                        "original_name": msg.file.original_name,
                        "mime_type": msg.file.mime_type,
                        "path": msg.file.path,
                    }
                    if msg.file
                    else None
                )
            }
        )

    return result