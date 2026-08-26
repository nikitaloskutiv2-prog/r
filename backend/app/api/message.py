from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict

from app.schemas.message import MessageCreate, MessageResponse
from app.db.session import get_db
from app.core.deps import get_current_user

from app.services import reaction_service, file_service, message_service, block_service
from app.models.message import Message
from app.websocket.chat_ws import manager


from app.models.chat import Chat
import logging

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/messages",
    tags=["messages"]
)

def check_chat_blocked(db: Session, chat_id: int, current_user_id: int):
    chat = (
        db.query(Chat)
        .options(joinedload(Chat.members))
        .filter(Chat.id == chat_id)
        .first()
    )

    if not chat:
        logger.warning(
            "Chat access failed: chat not found chat_id=%s user_id=%s",
            chat_id,
            current_user_id,
        )
        raise HTTPException(
            status_code=404, 
            detail="Chat not found"
        )

    other_user = None

    for member in chat.members:
        if member.id != current_user_id:
            other_user = member
            break

    if other_user is None:
        return

    if other_user.is_deleted:
        logger.warning(
            "Chat action rejected: target user deleted "
            "chat_id=%s user_id=%s target_user_id=%s",
            chat_id,
            current_user_id,
            other_user.id,
        )
        raise HTTPException(
            status_code=403,
            detail="Пользователь удалил аккаунт."
        )
    
    if block_service.are_users_blocked(
        db,
        current_user_id,
        other_user.id
    ):
        logger.warning(
            "Chat action rejected: users blocked "
            "chat_id=%s user_id=%s target_user_id=%s",
            chat_id,
            current_user_id,
            other_user.id,
        )
        raise HTTPException(
            status_code=403,
            detail="User is blocked"
        )

@router.post("/", response_model=MessageResponse)
def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    check_chat_blocked(
        db,
        message.chat_id,
        current_user.id
    )

    new_message = message_service.send_message(
        db,
        message,
        current_user.id
    )

    logger.info(
        "Message sent: message_id=%s chat_id=%s user_id=%s",
        new_message.id,
        message.chat_id,
        current_user.id,
    )

    return new_message

@router.get("/", response_model=List[MessageResponse])
def get_messages(
    chat_id: int,
    limit: int = 50,
    before_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return message_service.get_messages(
        db,
        chat_id,
        current_user.id,
        limit,
        before_id
    )


# ✅ Отметить сообщение как прочитанное
@router.put("/{message_id}/read", response_model=MessageResponse)
def mark_message_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return message_service.mark_message_as_read(
        db,
        message_id,
        current_user.id
    )

# ✅ Отметить все сообщения в чате как прочитанные
@router.put("/chat/{chat_id}/read-all")
def mark_chat_as_read(chat_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return message_service.mark_chat_as_read(db, chat_id, current_user.id)

# ✅ Получить количество непрочитанных сообщений для всех чатов
@router.get("/unread/counts", response_model=Dict[int, int])
def get_unread_counts(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return message_service.get_unread_counts(db, current_user.id)



@router.post("/{message_id}/reaction")
async def toggle_reaction(
    message_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    message = (
        db.query(Message)
        .filter(
            Message.id == message_id
        )
        .first()
    )

    if not message:
        logger.warning(
            "Reaction failed: message not found "
            "message_id=%s user_id=%s",
            message_id,
            current_user.id,
        )

        return {
            "success": False
        }
    
    chat = (
        db.query(Chat)
        .options(joinedload(Chat.members))
        .filter(Chat.id == message.chat_id)
        .first()
    )

    other_user = next(
        m for m in chat.members
        if m.id != current_user.id
    )

    if other_user.is_deleted:
        logger.warning(
            "Reaction rejected: target user deleted "
            "message_id=%s chat_id=%s user_id=%s target_user_id=%s",
            message_id,
            message.chat_id,
            current_user.id,
            other_user.id,
        )

        raise HTTPException(
            status_code=403,
            detail="Пользователь удалил аккаунт."
        )
    
    if block_service.are_users_blocked(
        db,
        current_user.id,
        other_user.id
    ):
        logger.warning(
            "Reaction rejected: users blocked "
            "message_id=%s chat_id=%s user_id=%s target_user_id=%s",
            message_id,
            message.chat_id,
            current_user.id,
            other_user.id,
        )

        raise HTTPException(
            status_code=403,
            detail="Blocked"
        )
    
    result = reaction_service.toggle_reaction(
        db,
        message_id,
        current_user.id,
        data["emoji"]
    )

    logger.info(
        "Message reaction changed: message_id=%s chat_id=%s user_id=%s action=%s",
        message_id,
        message.chat_id,
        current_user.id,
        result,
    )

    reactions = reaction_service.get_message_reactions(
        db,
        message_id,
        current_user.id
    )

    await manager.broadcast(
        message.chat_id,
        {
            "type": "reaction_updated",
            "message_id": message_id,
            "reactions": reactions
        }
    )

    return {
        "success": True,
        "action": result
    }


@router.post("/voice")
async def upload_voice(
    chat_id: int = Form(...),
    voice: UploadFile = File(...),
    duration: int = Form(...),
    waveform: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not voice.content_type:
        logger.warning(
            "Voice upload rejected: MIME type missing "
            "user_id=%s chat_id=%s filename=%s",
            current_user.id,
            chat_id,
            voice.filename,
        )

        raise HTTPException(
            status_code=400,
            detail="Voice file type is required"
        )

    if not voice.content_type.startswith("audio/"):
        logger.warning(
            "Voice upload rejected: invalid MIME type "
            "user_id=%s chat_id=%s filename=%s mime_type=%s",
            current_user.id,
            chat_id,
            voice.filename,
            voice.content_type,
        )

        raise HTTPException(
            status_code=400,
            detail="Only audio files are allowed"
        )
    check_chat_blocked(
        db,
        chat_id,
        current_user.id
    )
    if duration < 0:
        logger.warning(
            "Voice upload rejected: negative duration "
            "user_id=%s chat_id=%s duration=%s",
            current_user.id,
            chat_id,
            duration,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid voice duration"
        )

    if duration > file_service.MAX_VOICE_DURATION:
        logger.warning(
            "Voice upload rejected: duration limit exceeded "
            "user_id=%s chat_id=%s duration=%s limit=%s",
            current_user.id,
            chat_id,
            duration,
            file_service.MAX_VOICE_DURATION,
        )

        raise HTTPException(
            status_code=413,
            detail="Voice message is too long"
        )
    try:
        message = file_service.upload_voice(
            db,
            voice,
            chat_id,
            current_user.id,
            duration,
            waveform
        )

    except ValueError as error:

        logger.warning(
            "Voice upload rejected: "
            "user_id=%s chat_id=%s filename=%s reason=%s",
            current_user.id,
            chat_id,
            voice.filename,
            str(error),
        )

        raise HTTPException(
            status_code=413,
            detail=str(error)
        )
    logger.info(
        "Voice file uploaded: file_id=%s chat_id=%s user_id=%s duration=%s filename=%s",
        message["file_id"],
        chat_id,
        current_user.id,
        duration,
        voice.filename,
    )

    return message


@router.post("/{message_id}/voice-played")
def voice_played(
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    message = message_service.mark_voice_played(
        db,
        message_id,
        current_user.id
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )

    return {
        "message_id": message.id,
        "voice_played": True
    }