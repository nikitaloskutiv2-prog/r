
from sqlalchemy.orm import Session, joinedload
import json
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Query
)
from app.db.session import get_db
from app.services import message_service, auth_service
from app.websocket.chat_ws import manager, notification_manager
from app.models.user import User
from app.schemas.message import MessageCreate
from app.models.chat import Chat
from app.models.message import Message
from app.models.chat_deletion import ChatDeletion
from app.models.reaction import MessageReaction
from app.models.pinned_message import PinnedMessage
from datetime import datetime
from jose import jwt, JWTError
from app.models.message_deletion import MessageDeletion
from app.services import chat_service
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def authenticate_websocket(
    websocket: WebSocket,
    token: str,
    db: Session
):
    if not token:
        logger.warning("WebSocket authentication failed: token missing")
        await websocket.close(
            code=1008,
            reason="No token provided"
        )
        return None

    try:

        payload = jwt.decode(
            token,
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM]
        )

        accountid = payload.get("sub")

        if accountid is None:
            logger.warning(
                "WebSocket authentication failed: token subject missing"
            )
            await websocket.close(
                code=1008,
                reason="Invalid token"
            )
            return None

        user = (
            db.query(User)
            .filter(User.accountid == accountid)
            .first()
        )

        if user is None:
            logger.warning(
                "WebSocket authentication failed: user not found accountid=%s",
                accountid,
            )
            await websocket.close(
                code=1008,
                reason="User not found"
            )
            return None

        return user

    except JWTError:
        logger.warning("WebSocket authentication failed: invalid token")
        await websocket.close(
            code=1008,
            reason="Invalid token"
        )

        return None

@router.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(
    chat_id: int,
    websocket: WebSocket,
    token: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """WebSocket для сообщений в чате"""
    
    user = await authenticate_websocket(
        websocket,
        token,
        db
    )

    if not user:
        return

    chat = (
        db.query(Chat)
        .options(joinedload(Chat.members))
        .filter(
            Chat.id == chat_id,
            Chat.members.any(User.id == user.id)
        )
        .first()
    )

    if not chat:
        logger.warning(
            "Chat WebSocket access denied: chat not found or user is not member "
            "chat_id=%s user_id=%s",
            chat_id,
            user.id,
        )
        await websocket.close(code=1008)
        return


    await manager.connect(chat_id, websocket, user.id)
    logger.info(
        "Chat WebSocket connected: chat_id=%s user_id=%s",
        chat_id,
        user.id,
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event_data = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(
                    "Invalid WebSocket JSON: chat_id=%s user_id=%s",
                    chat_id,
                    user.id,
                )
                continue

            event_type = event_data.get("type")
            
            if event_type == "message_read":
                message_id = event_data.get("message_id")

                if not message_id:
                    continue

                message = message_service.mark_message_as_read(
                    db,
                    message_id,
                    user.id
                )

                if not message:
                    continue

                await manager.broadcast(
                    chat_id,
                    {
                        "type": "message_read",
                        "message_id": message_id,
                        "user_id": user.id
                    }
                )
            elif event_type == "typing":

                await manager.broadcast_except(
                    chat_id,
                    {
                        "type": "typing",
                        "user_id": user.id
                    },
                    exclude_user_id=user.id
                )
            elif event_type == "voice_recording":

                await manager.broadcast_except(
                    chat_id,
                    {
                        "type": "voice_recording",
                        "user_id": user.id
                    },
                    exclude_user_id=user.id
                )

            elif event_type == "voice_recording_stop":

                await manager.broadcast_except(
                    chat_id,
                    {
                        "type": "voice_recording_stop",
                        "user_id": user.id
                    },
                    exclude_user_id=user.id
                )

            # Обработка отметить весь чат как прочитанный
            elif event_type == "chat_read_all":
                message_service.mark_chat_as_read(db, chat_id, user.id)
                
                await manager.broadcast(chat_id, {
                    "type": "chat_read_all",
                    "chat_id": chat_id,
                    "user_id": user.id
                })

            elif event_type == "voice_played":

                message_id = event_data.get("message_id")

                if not message_id:
                    continue

                message = message_service.mark_voice_played(
                    db,
                    message_id,
                    user.id
                )

                if not message:
                    continue

                await manager.broadcast(
                    chat_id,
                    {
                        "type": "voice_played",
                        "message_id": message.id
                    }
                )

            elif event_type == "edit_message":

                message_id = event_data.get(
                    "message_id"
                )

                content = event_data.get(
                    "content"
                )

                message = (
                    db.query(Message)
                    .filter(
                        Message.id == message_id,
                        Message.chat_id == chat_id,
                        Message.sender_id == user.id
                    )
                    .first()
                )

                if (
                    message
                    and
                    message.sender_id == user.id
                ):

                    message.content = content
                    message.edited = True
                    db.commit()

                    await manager.broadcast(
                        chat_id,
                        {
                            "type": "message_edited",
                            "message_id": message.id,
                            "content": content,
                            "edited": True
                        }
                    )
                    logger.info(
                        "Message edited: message_id=%s chat_id=%s user_id=%s",
                        message.id,
                        chat_id,
                        user.id,
                    )

            elif event_type == "delete_chat_self":
                chat = (
                    db.query(Chat)
                    .filter(
                        Chat.id == chat_id,
                        Chat.members.any(User.id == user.id)
                    )
                    .first()
                )

                if not chat:
                    continue

                # Проверяем, нет ли уже удаления
                existing_deletion = (
                    db.query(ChatDeletion)
                    .filter(
                        ChatDeletion.chat_id == chat_id,
                        ChatDeletion.user_id == user.id
                    )
                    .first()
                )

                if not existing_deletion:

                    deletion = ChatDeletion(
                        chat_id=chat_id,
                        user_id=user.id
                    )

                    db.add(deletion)
                    db.commit()

                # Сообщаем notification websocket,
                # чтобы sidebar удалил чат у этого пользователя
                await notification_manager.send_to_user(
                    user.id,
                    {
                        "type": "chat_deleted",
                        "chat_id": chat_id,
                        "delete_for": "self"
                    }
                )

                # Сообщаем открытому chat websocket,
                # чтобы UI очистил текущий чат
                await manager.broadcast(
                    chat_id,
                    {
                        "type": "chat_deleted",
                        "chat_id": chat_id,
                        "delete_for": "self",
                        "user_id": user.id
                    }
                )

            elif event_type == "delete_chat_all":

                # Получаем чат и убеждаемся,
                # что текущий пользователь является его участником
                chat = (
                    db.query(Chat)
                    .options(joinedload(Chat.members))
                    .filter(
                        Chat.id == chat_id,
                        Chat.members.any(User.id == user.id)
                    )
                    .first()
                )

                if not chat:
                    continue

                if chat.is_favorite:
                    continue

                if not chat.is_private:
                    continue

                if len(chat.members) != 2:
                    continue

                # Запоминаем участников ДО удаления чата
                member_ids = [
                    member.id
                    for member in chat.members
                ]

                # Получаем все сообщения чата
                message_ids = [
                    message.id
                    for message in (
                        db.query(Message.id)
                        .filter(
                            Message.chat_id == chat_id
                        )
                        .all()
                    )
                ]

                # -----------------------------------------
                # Удаляем зависимости сообщений
                # -----------------------------------------

                if message_ids:

                    db.query(MessageDeletion).filter(
                        MessageDeletion.message_id.in_(message_ids)
                    ).delete(
                        synchronize_session=False
                    )

                    db.query(MessageReaction).filter(
                        MessageReaction.message_id.in_(message_ids)
                    ).delete(
                        synchronize_session=False
                    )

                    db.query(PinnedMessage).filter(
                        PinnedMessage.message_id.in_(message_ids)
                    ).delete(
                        synchronize_session=False
                    )

                # -----------------------------------------
                # Удаляем ChatDeletion
                # -----------------------------------------

                db.query(ChatDeletion).filter(
                    ChatDeletion.chat_id == chat_id
                ).delete(
                    synchronize_session=False
                )

                # -----------------------------------------
                # Удаляем сообщения
                # -----------------------------------------

                db.query(Message).filter(
                    Message.chat_id == chat_id
                ).delete(
                    synchronize_session=False
                )

                # -----------------------------------------
                # Удаляем сам чат
                # -----------------------------------------

                db.delete(chat)

                db.commit()

                # -----------------------------------------
                # Уведомляем обоих пользователей
                # -----------------------------------------

                for member_id in member_ids:

                    await notification_manager.send_to_user(
                        member_id,
                        {
                            "type": "chat_deleted",
                            "chat_id": chat_id,
                            "delete_for": "all",
                            "user_id": user.id
                        }
                    )

                # -----------------------------------------
                # Очищаем открытый чат
                # -----------------------------------------

                await manager.broadcast(
                    chat_id,
                    {
                        "type": "chat_deleted",
                        "chat_id": chat_id,
                        "delete_for": "all"
                    }
                )

            elif event_type == "delete_message_self":

                message_id = event_data.get("message_id")

                message = (
                    db.query(Message)
                    .filter(
                        Message.id == message_id,
                        Message.chat_id == chat_id
                    )
                    .first()
                )

                if not message:
                    continue

                existing_deletion = (
                    db.query(MessageDeletion)
                    .filter(
                        MessageDeletion.message_id == message_id,
                        MessageDeletion.user_id == user.id
                    )
                    .first()
                )

                if not existing_deletion:

                    deletion = MessageDeletion(
                        message_id=message_id,
                        user_id=user.id
                    )

                    db.add(deletion)
                    db.commit()

                last_message = (
                    db.query(Message)
                    .outerjoin(
                        MessageDeletion,
                        and_(
                            MessageDeletion.message_id == Message.id,
                            MessageDeletion.user_id == user.id
                        )
                    )
                    .filter(
                        Message.chat_id == chat_id,
                        MessageDeletion.id == None
                    )
                    .order_by(
                        Message.created_at.desc()
                    )
                    .first()
                )

                last_message_payload = None

                if last_message:

                    last_message_payload = {
                        "id": last_message.id,
                        "chat_id": last_message.chat_id,
                        "sender_id": last_message.sender_id,
                        "content": last_message.content,
                        "created_at": last_message.created_at.isoformat(),
                        "is_read": last_message.is_read,
                        "voice_duration": last_message.voice_duration,
                        "waveform": last_message.waveform,
                        "voice_played": last_message.voice_played,
                        "file": (
                            {
                                "id": last_message.file.id,
                                "original_name": last_message.file.original_name,
                                "mime_type": last_message.file.mime_type,
                                "path": last_message.file.path,
                            }
                            if last_message.file
                            else None
                        )
                    }

                await notification_manager.send_to_user(
                    user.id,
                    {
                        "type": "message_deleted",
                        "message_id": message_id,
                        "chat_id": chat_id,
                        "user_id": user.id,
                        "delete_for": "self",
                        "last_message": last_message_payload
                    }
                )
                logger.info(
                    "Message deleted for self: message_id=%s chat_id=%s user_id=%s",
                    message_id,
                    chat_id,
                    user.id,
                )


            elif event_type == "delete_message_all":

                message_id = event_data.get("message_id")

                message = (
                    db.query(Message)
                    .filter(
                        Message.id == message_id,
                        Message.chat_id == chat_id
                    )
                    .first()
                )

                if not message:
                    continue

                # Удаляем сообщение для всех
                db.delete(message)
                db.commit()

                # Получаем участников чата
                chat = (
                    db.query(Chat)
                    .options(joinedload(Chat.members))
                    .filter(
                        Chat.id == chat_id,
                        Chat.members.any(User.id == user.id)
                    )
                    .first()
                )

                if not chat:
                    continue

                # Для каждого пользователя отдельно определяем
                # его последнее видимое сообщение.
                for member in chat.members:

                    last_message = (
                        db.query(Message)
                        .options(
                            joinedload(Message.file)
                        )
                        .outerjoin(
                            MessageDeletion,
                            and_(
                                MessageDeletion.message_id == Message.id,
                                MessageDeletion.user_id == member.id
                            )
                        )
                        .filter(
                            Message.chat_id == chat_id,
                            MessageDeletion.id == None
                        )
                        .order_by(
                            Message.created_at.desc()
                        )
                        .first()
                    )

                    last_message_payload = None

                    if last_message:

                        last_message_payload = {
                            "id": last_message.id,
                            "chat_id": last_message.chat_id,
                            "sender_id": last_message.sender_id,
                            "content": last_message.content,
                            "created_at": last_message.created_at.isoformat(),
                            "is_read": last_message.is_read,
                            "voice_duration": last_message.voice_duration,
                            "waveform": last_message.waveform,
                            "voice_played": last_message.voice_played,
                            "file": (
                                {
                                    "id": last_message.file.id,
                                    "original_name": last_message.file.original_name,
                                    "mime_type": last_message.file.mime_type,
                                    "path": last_message.file.path,
                                }
                                if last_message.file
                                else None
                            )
                        }

                    # Главное: сайдбар получает событие через notification websocket
                    await notification_manager.send_to_user(
                        member.id,
                        {
                            "type": "message_deleted",
                            "message_id": message_id,
                            "chat_id": chat_id,
                            "user_id": user.id,
                            "delete_for": "all",
                            "last_message": last_message_payload
                        }
                    )

                # Удаляем сообщение из открытого чата у всех,
                # кто сейчас подключен к chat websocket
                await manager.broadcast(
                    chat_id,
                    {
                        "type": "message_deleted",
                        "message_id": message_id,
                        "chat_id": chat_id,
                        "delete_for": "all"
                    }
                )
                logger.info(
                    "Message deleted for all: message_id=%s chat_id=%s user_id=%s",
                    message_id,
                    chat_id,
                    user.id,
                )

            # Обычное сообщение
            elif event_type == "message":
                message_data = MessageCreate(
                    chat_id=chat_id,
                    content=event_data.get(
                        "content"

                    ),
                    file_id=event_data.get(
                        "file_id"
                    ),
                    reply_to_id=event_data.get(
                        "reply_to_id"
                    ),
                    voice_duration=event_data.get("voice_duration"),
                    waveform=event_data.get("waveform")
                    
                )

                message = message_service.send_message(
                    db,
                    message_data,
                    user.id
                )
                logger.info(
                    "Message sent via WebSocket: message_id=%s chat_id=%s user_id=%s",
                    message.id,
                    chat_id,
                    user.id,
                )
                if chat.is_favorite:
                    message.is_read = True
                    db.commit()
                    
                message = (
                    db.query(Message)
                    .options(
                        joinedload(Message.file),
                        joinedload(Message.reply_to)
                        .joinedload(Message.file)
                    )
                    .filter(Message.id == message.id)
                    .first()
                )
                
                chat = (
                    db.query(Chat)
                    .options(joinedload(Chat.members))
                    .filter(Chat.id == chat_id)
                    .first()
                )
                if not chat:
                    continue

                
                for member in chat.members:

                    # Для каждого получателя отдельно определяем,
                    # как должен называться чат и какой должен быть аватар.
                    member_chat_name = chat_service.get_chat_name(
                        chat,
                        member.id
                    )

                    member_other_user = None

                    if chat.is_private:

                        member_other_user = next(
                            (
                                chat_member
                                for chat_member in chat.members
                                if chat_member.id != member.id
                            ),
                            None
                        )

                    member_chat_avatar = (
                        member_other_user.avatar
                        if member_other_user
                        else None
                    )

                    member_chat_update_payload = {
                        "type": "chat_updated",

                        "chat": {
                            "id": chat.id,

                            "name": member_chat_name,

                            "is_private": chat.is_private,

                            "members": [
                                chat_member.id
                                for chat_member in chat.members
                            ],

                            "avatar": member_chat_avatar,

                            "last_message": {
                                "id": message.id,
                                "content": message.content,
                                "sender_id": message.sender_id,
                                "created_at": message.created_at.isoformat(),
                                "is_read": True if chat.is_favorite else message.is_read,
                                "chat_id": chat.id,
                                "voice_duration": message.voice_duration,
                                "waveform": message.waveform,
                                "voice_played": message.voice_played,

                                "file": (
                                    {
                                        "id": message.file.id,
                                        "original_name": message.file.original_name,
                                        "mime_type": message.file.mime_type,
                                        "path": message.file.path,
                                    }
                                    if message.file
                                    else None
                                )
                            }
                        }
                    }

                    if member.id != user.id:

                        await notification_manager.send_to_user(
                            member.id,
                            {
                                "type": "unread_update",
                                "chat_id": chat_id
                            }
                        )

                    await notification_manager.send_to_user(
                        member.id,
                        member_chat_update_payload
                    )
                await manager.broadcast_except(
                    chat_id,
                    {
                        "type": "stop_typing",
                        "user_id": user.id
                    },
                    exclude_user_id=user.id
                )
                await manager.broadcast_except(
                    chat_id,
                    {
                        "type": "voice_recording_stop",
                        "user_id": user.id
                    },
                    exclude_user_id=user.id
                )
                await manager.broadcast(
                    chat_id,
                    {
                        "type": "new_message",
                        "id": message.id,
                        "chat_id": message.chat_id,
                        "sender_id": message.sender_id,
                        "content": message.content,
                        "voice_duration": message.voice_duration,
                        "waveform": message.waveform,
                        "voice_played": message.voice_played,
                        "file_id": message.file_id,
                        "file": (
                            {
                                "id": message.file.id,
                                "path": message.file.path,
                                "mime_type": message.file.mime_type,
                                "original_name": message.file.original_name,
                                "thumbnail_path": message.file.thumbnail_path,
                                "size": message.file.size,
                            }
                            if message.file
                            else None
                        ),

                        "created_at": message.created_at.isoformat(),
                        "is_read": True if chat.is_favorite else message.is_read,
                        "edited": message.edited,

                        "reply_to": (
                        {
                            "id": message.reply_to.id,
                            "content": message.reply_to.content,
                            "sender_id": message.reply_to.sender_id,
                            "voice_duration": message.reply_to.voice_duration,
                            "file": (
                                {
                                    "id": message.reply_to.file.id,
                                    "original_name": message.reply_to.file.original_name,
                                    "mime_type": message.reply_to.file.mime_type,
                                    "path": message.reply_to.file.path,
                                    "thumbnail_path": message.reply_to.file.thumbnail_path,
                                    "size": message.reply_to.file.size,
                                }
                                if message.reply_to.file
                                else None
                            )
                        }
                        if message.reply_to
                        else None
                    )
                    }
                )
            
    except WebSocketDisconnect as e:
        logger.info(
            "Chat WebSocket disconnected: chat_id=%s user_id=%s code=%s",
            chat_id,
            user.id,
            e.code,
        )

    except Exception:
        logger.exception(
            "WebSocket error: chat_id=%s user_id=%s",
            chat_id,
            user.id,
        )

    finally:
        manager.disconnect(chat_id, websocket)
        logger.info(
            "Chat WebSocket disconnected: chat_id=%s user_id=%s",
            chat_id,
            user.id,
        )


@router.websocket("/ws/notifications")
async def notifications_ws(
    websocket: WebSocket,
    token: str | None = Query(None),
    db: Session = Depends(get_db)
):
    user = await authenticate_websocket(
        websocket,
        token,
        db
    )

    if not user:
        return

    await notification_manager.connect(
        user.id,
        websocket
    )
    logger.info(
        "Notification WebSocket connected: user_id=%s",
        user.id,
    )

    was_offline = (
        notification_manager.online_users.get(
            user.id,
            0
        ) == 1
    )

    if was_offline:

        user.status = "online"
        db.commit()

        chats = (
            db.query(Chat)
            .options(joinedload(Chat.members))
            .filter(
                Chat.members.any(User.id == user.id)
            )
            .all()
        )

        member_ids = set()

        for chat in chats:

            for member in chat.members:

                if member.id != user.id:
                    member_ids.add(member.id)

        await notification_manager.broadcast_user_status(
            user.id,
            "online",
            list(member_ids)
        )

    try:

        while True:

            data = await websocket.receive_text()

            try:
                event_data = json.loads(data)
            except json.JSONDecodeError:
                logger.warning(
                    "Invalid notification WebSocket JSON: user_id=%s",
                    user.id,
                )
                continue

            event_type = event_data.get("type")

            if event_type == "visibility_changed":

                status = event_data.get("status")

                if status not in ("online", "away"):
                    continue

                user.status = status
                db.commit()

                chats = (
                    db.query(Chat)
                    .options(joinedload(Chat.members))
                    .filter(
                        Chat.members.any(User.id == user.id)
                    )
                    .all()
                )

                member_ids = set()

                for chat in chats:

                    for member in chat.members:

                        if member.id != user.id:
                            member_ids.add(member.id)

                await notification_manager.broadcast_user_status(
                    user.id,
                    status,
                    list(member_ids)
                )

    except WebSocketDisconnect as e:
        logger.info(
            "Notification WebSocket disconnected: user_id=%s code=%s",
            user.id,
            e.code,
        )

    except Exception:
        logger.exception(
            "Notification WebSocket error: user_id=%s",
            user.id,
        )

    finally:

        became_offline = notification_manager.disconnect(
            user.id,
            websocket
        )
        logger.info(
            "Notification WebSocket disconnected: user_id=%s became_offline=%s",
            user.id,
            became_offline,
        )
        if became_offline:

            user.status = "offline"
            user.last_seen = datetime.utcnow()

            db.commit()

            chats = (
                db.query(Chat)
                .options(joinedload(Chat.members))
                .filter(
                    Chat.members.any(User.id == user.id)
                )
                .all()
            )

            member_ids = set()

            for chat in chats:

                for member in chat.members:

                    if member.id != user.id:
                        member_ids.add(member.id)

            await notification_manager.broadcast_user_status(
                user.id,
                "offline",
                list(member_ids)
            )