from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[
            int,
            dict[int, set[WebSocket]]
        ] = {}

    async def connect(self, chat_id: int, websocket: WebSocket, user_id: int):
        await websocket.accept()

        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}

        if user_id not in self.active_connections[chat_id]:
            self.active_connections[chat_id][user_id] = set()

        self.active_connections[chat_id][user_id].add(
            websocket
        )
        logger.info(
            "WebSocket connected: chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )

    def disconnect(self,chat_id: int,websocket: WebSocket):
        logger.info(
            "WebSocket disconnecting: chat_id=%s",
            chat_id,
        )
        if chat_id not in self.active_connections:
            return

        users = self.active_connections[chat_id]

        empty_users = []

        for user_id, sockets in users.items():

            sockets.discard(websocket)

            if not sockets:
                empty_users.append(user_id)

        for user_id in empty_users:
            del users[user_id]

        if not users:
            logger.info(
                "Chat WebSocket connections cleared: chat_id=%s",
                chat_id,
            )
            del self.active_connections[chat_id]

    async def broadcast(self,chat_id: int,message: dict):
        if chat_id not in self.active_connections:
            return
        logger.debug(
            "Broadcasting chat event: chat_id=%s",
            chat_id,
        )
        for sockets in self.active_connections[chat_id].values():

            for ws in list(sockets):

                try:
                    await ws.send_json(message)

                except Exception:
                    logger.warning(
                        "Failed to send WebSocket message: chat_id=%s",
                        chat_id,
                        exc_info=True,
                    )
                    sockets.discard(ws)

    async def broadcast_except(self,chat_id: int,message: dict,exclude_user_id: int):
        if chat_id not in self.active_connections:
            return
        logger.debug(
            "Broadcasting chat event excluding user: chat_id=%s exclude_user_id=%s",
            chat_id,
            exclude_user_id,
        )
        for user_id, sockets in self.active_connections[chat_id].items():

            if user_id == exclude_user_id:
                continue

            for ws in list(sockets):

                try:
                    await ws.send_json(message)

                except Exception:
                    logger.warning(
                        "Failed to send WebSocket message: "
                        "chat_id=%s exclude_user_id=%s",
                        chat_id,
                        exclude_user_id,
                        exc_info=True,
                    )
                    sockets.discard(ws)

manager = ConnectionManager()


class NotificationManager:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}
        self.online_users: dict[int, int] = {}

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        self.online_users[user_id] = (
            self.online_users.get(user_id, 0) + 1
        )
        logger.info(
            "Notification WebSocket connected: user_id=%s connections=%s",
            user_id,
            self.online_users[user_id],
        )

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        if user_id in self.online_users:
            logger.info(
                "User went offline: user_id=%s",
                user_id,
            )
            self.online_users[user_id] -= 1

            if self.online_users[user_id] <= 0:

                del self.online_users[user_id]
                return True
            logger.debug(
                "Notification WebSocket disconnected: user_id=%s remaining_connections=%s",
                user_id,
                self.online_users[user_id],
            )
            return False
        
    def is_online(
        self,
        user_id: int
    ):
        return user_id in self.online_users

    async def broadcast_user_status(
        self,
        user_id: int,
        status: str,
        member_ids: list[int]
    ):
        payload = {
            "type": "user_status_changed",
            "user_id": user_id,
            "status": status
        }

        logger.info(
            "Broadcasting user status: user_id=%s status=%s members=%s",
            user_id,
            status,
            len(member_ids),
        )

        for member_id in member_ids:

            if member_id == user_id:
                continue

            await self.send_to_user(
                member_id,
                payload
            )

    async def send_to_user(self, user_id: int, data: dict):
        if user_id not in self.active_connections:
            return
        
        logger.debug(
            "Sending notification: user_id=%s",
            user_id,
        )

        for ws in list(self.active_connections[user_id]):
            try:
                await ws.send_json(data)
            except Exception:
                logger.warning(
                    "Failed to send notification WebSocket message: user_id=%s",
                    user_id,
                    exc_info=True,
                )

                self.active_connections[user_id].discard(ws)

                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

notification_manager = NotificationManager()

async def notify_block_changed(
    user1_id: int,
    user2_id: int
):
    logger.info(
        "Block status notification: user1_id=%s user2_id=%s",
        user1_id,
        user2_id,
    )
    payload = {
        "type": "block_status_changed"
    }
    await notification_manager.send_to_user(
        user1_id,
        payload
    )

    await notification_manager.send_to_user(
        user2_id,
        payload
    )

async def notify_account_deleted(
    user_id: int,
    member_ids: list[int]
):
    logger.info(
        "Account deletion notification: user_id=%s member_count=%s",
        user_id,
        len(member_ids),
    )
    payload = {
        "type": "account_deleted",
        "user_id": user_id
    }

    for member_id in member_ids:

        if member_id == user_id:
            continue

        await notification_manager.send_to_user(
            member_id,
            payload
        )