from typing import Dict, List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # chat_id -> список подключений
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, chat_id: int, websocket: WebSocket):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        logger.info(
            "WebSocket connected: chat_id=%s connections=%s",
            chat_id,
            len(self.active_connections[chat_id]),
        )

    def disconnect(self, chat_id: int, websocket: WebSocket):
        if chat_id not in self.active_connections:
            return

        if websocket not in self.active_connections[chat_id]:
            return

        self.active_connections[chat_id].remove(websocket)

        logger.info(
            "WebSocket disconnected: chat_id=%s remaining_connections=%s",
            chat_id,
            len(self.active_connections[chat_id]),
        )

        if not self.active_connections[chat_id]:
            del self.active_connections[chat_id]

            logger.debug(
                "No active WebSocket connections: chat_id=%s",
                chat_id,
            )

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket
    ):
        try:
            await websocket.send_text(message)

        except Exception:
            logger.warning(
                "Failed to send personal WebSocket message",
                exc_info=True,
            )
            raise

    async def broadcast(
        self,
        chat_id: int,
        message: str
    ):
        if chat_id not in self.active_connections:
            logger.debug(
                "Broadcast skipped: no active connections chat_id=%s",
                chat_id,
            )
            return

        connections = list(
            self.active_connections[chat_id]
        )

        logger.debug(
            "Broadcasting WebSocket message: chat_id=%s connections=%s",
            chat_id,
            len(connections),
        )

        for connection in connections:

            try:
                await connection.send_text(message)

            except Exception:
                logger.warning(
                    "Failed to broadcast WebSocket message: chat_id=%s",
                    chat_id,
                    exc_info=True,
                )

                if chat_id in self.active_connections:
                    if connection in self.active_connections[chat_id]:
                        self.active_connections[chat_id].remove(connection)