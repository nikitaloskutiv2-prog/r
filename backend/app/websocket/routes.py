from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from app.websocket.manager import ConnectionManager
from app.core.deps import get_current_user
from app.schemas.message import MessageResponse
from app.services import message_service
from app.db.session import get_db
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    logger.info(
        "Chat WebSocket connection requested: chat_id=%s user_id=%s",
        chat_id,
        current_user.id,
    )
    await manager.connect(chat_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(
                "WebSocket message received: chat_id=%s user_id=%s",
                chat_id,
                current_user.id,
            )
            # сохраняем сообщение в БД
            message = message_service.send_message(
                db, 
                message_data={"chat_id": chat_id, "content": data}, 
                sender_id=current_user.id
            )
            logger.info(
                "WebSocket message saved: message_id=%s chat_id=%s user_id=%s",
                message.id,
                chat_id,
                current_user.id,
            )
            # формируем JSON
            message_json = json.dumps({
                "id": message.id,
                "chat_id": message.chat_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": str(message.created_at)
            })
            logger.debug(
                "Broadcasting WebSocket message: message_id=%s chat_id=%s",
                message.id,
                chat_id,
            )
            # рассылаем всем подключённым к чату
            await manager.broadcast(chat_id, message_json)
    except WebSocketDisconnect:
        logger.info(
            "Chat WebSocket disconnected: chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )

        manager.disconnect(
            chat_id,
            websocket
        )
    except Exception:
        logger.exception(
            "Unexpected WebSocket error: chat_id=%s user_id=%s",
            chat_id,
            current_user.id,
        )

        manager.disconnect(
            chat_id,
            websocket
        )