import logging

from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.user import User
from app.models.chat_deletion import ChatDeletion
from app.models.message import Message
from app.models.message_deletion import MessageDeletion
from app.models.reaction import MessageReaction
from app.models.pinned_message import PinnedMessage


logger = logging.getLogger(__name__)


def _delete_chat_messages(
    db: Session,
    chat_id: int
) -> None:
    message_ids = [
        message_id
        for (message_id,) in (
            db.query(Message.id)
            .filter(Message.chat_id == chat_id)
            .all()
        )
    ]

    if not message_ids:
        logger.info(
            "Deleting chat messages: chat_id=%s message_count=%s",
            chat_id,
            len(message_ids),
        )
        return

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

    db.query(Message).filter(
        Message.id.in_(message_ids)
    ).delete(
        synchronize_session=False
    )

def _get_user_chat(
    db: Session,
    chat_id: int,
    user_id: int
):
    return (
        db.query(Chat)
        .filter(
            Chat.id == chat_id,
            Chat.members.any(User.id == user_id)
        )
        .first()
    )


def get_or_create_private_chat(
    db: Session,
    user1_id: int,
    user2_id: int
):
    """
    Получить или создать приватный чат.

    Если пользователь ранее удалил чат у себя,
    при повторном открытии:
    - чат снова становится видимым в сайдбаре;
    - старые сообщения скрываются через MessageDeletion;
    - новые сообщения будут отображаться;
    - сам Chat не создаётся заново.
    """

    # Избранное
    if user1_id == user2_id:
        logger.info(
            "Opening favorite chat: user_id=%s",
            user1_id,
        )
        return get_or_create_favorite_chat(
            db,
            user1_id
        )
    
    # Ищем существующий приватный чат
    chat = (
        db.query(Chat)
        .filter(
            Chat.is_private.is_(True),
            Chat.is_favorite.is_(False),
            Chat.members.any(User.id == user1_id),
            Chat.members.any(User.id == user2_id)
        )
        .first()
    )

    # Если чата вообще нет — создаём
    if not chat:

        users = (
            db.query(User)
            .filter(User.id.in_([user1_id, user2_id]))
            .all()
        )

        users_by_id = {
            user.id: user
            for user in users
        }

        user1 = users_by_id.get(user1_id)
        user2 = users_by_id.get(user2_id)

        if not user1 or not user2:
            logger.warning(
                "Private chat creation failed: user not found user1_id=%s user2_id=%s",
                user1_id,
                user2_id,
            )
            return None

        new_chat = Chat(
            is_private=True,
            is_favorite=False
        )

        new_chat.members.append(user1)
        new_chat.members.append(user2)

        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        logger.info(
            "Private chat created: chat_id=%s user1_id=%s user2_id=%s",
            new_chat.id,
            user1_id,
            user2_id,
        )
        return new_chat

    # Проверяем, удалял ли пользователь этот чат у себя
    deletion = (
        db.query(ChatDeletion)
        .filter(
            ChatDeletion.chat_id == chat.id,
            ChatDeletion.user_id == user1_id
        )
        .first()
    )

    # --------------------------------------------------
    # Чат был ранее удалён пользователем
    # --------------------------------------------------

    if deletion:
        logger.info(
            "Restoring deleted private chat: chat_id=%s user_id=%s",
            chat.id,
            user1_id,
        )
        # Получаем ВСЕ старые сообщения этого чата
        old_messages = (
            db.query(Message)
            .filter(
                Message.chat_id == chat.id,
                Message.created_at <= deletion.created_at
            )
            .all()
        )

        logger.info(
            "Found old messages to hide: chat_id=%s user_id=%s message_count=%s",
            chat.id,
            user1_id,
            len(old_messages),
        )

        if old_messages:

            old_message_ids = [
                message.id
                for message in old_messages
            ]

            # Какие сообщения уже скрыты этим пользователем
            existing_deletions = (
                db.query(
                    MessageDeletion.message_id
                )
                .filter(
                    MessageDeletion.user_id == user1_id,
                    MessageDeletion.message_id.in_(
                        old_message_ids
                    )
                )
                .all()
            )

            existing_ids = {
                message_id
                for (message_id,) in existing_deletions
            }
            logger.info(
                "Existing hidden messages checked: chat_id=%s user_id=%s existing_count=%s",
                chat.id,
                user1_id,
                len(existing_ids),
            )
            # Помечаем старые сообщения как удалённые
            # только если они ещё не были скрыты
            for message_id in old_message_ids:

                if message_id in existing_ids:
                    continue

                db.add(
                    MessageDeletion(
                        message_id=message_id,
                        user_id=user1_id
                    )
                )


        db.delete(deletion)
        logger.info(
            "Private chat deletion marker removed: chat_id=%s user_id=%s",
            chat.id,
            user1_id,
        )
        db.commit()
        db.refresh(chat)
        logger.info(
            "Private chat restored: chat_id=%s user_id=%s",
            chat.id,
            user1_id,
        )
    return chat



def get_user_chats(
    db: Session,
    user_id: int
):
    user_exists = (
        db.query(User.id)
        .filter(User.id == user_id)
        .first()
    )

    if not user_exists:
        return []

    chats = (
        db.query(Chat)
        .filter(
            Chat.members.any(User.id == user_id)
        )
        .all()
    )

    if not chats:
        return []

    chat_ids = [chat.id for chat in chats]

    # Получаем удаления пользователя одним запросом
    deletions = (
        db.query(ChatDeletion)
        .filter(
            ChatDeletion.user_id == user_id,
            ChatDeletion.chat_id.in_(chat_ids)
        )
        .all()
    )

    deletion_by_chat_id = {
        deletion.chat_id: deletion
        for deletion in deletions
    }

    # Для чатов, у которых есть ChatDeletion,
    # одним запросом находим те, где появились новые сообщения.
    deletion_chat_ids = list(deletion_by_chat_id.keys())

    chats_with_new_messages = set()

    if deletion_chat_ids:
        rows = (
            db.query(
                Message.chat_id
            )
            .join(
                ChatDeletion,
                ChatDeletion.chat_id == Message.chat_id
            )
            .filter(
                ChatDeletion.user_id == user_id,
                ChatDeletion.chat_id.in_(deletion_chat_ids),
                Message.created_at > ChatDeletion.created_at
            )
            .distinct()
            .all()
        )

        chats_with_new_messages = {
            chat_id
            for (chat_id,) in rows
        }

    result = []

    for chat in chats:

        deletion = deletion_by_chat_id.get(chat.id)

        # Чат никогда не удалялся пользователем
        if deletion is None:
            result.append(chat)
            continue

        # Чат был удалён, но после удаления появились новые сообщения
        if chat.id in chats_with_new_messages:
            result.append(chat)

    return result


def get_chat_deletion(
    db: Session,
    chat_id: int,
    user_id: int
):
    """
    Получить отметку удаления чата
    текущим пользователем.
    """

    return (
        db.query(ChatDeletion)
        .filter(
            ChatDeletion.chat_id == chat_id,
            ChatDeletion.user_id == user_id
        )
        .first()
    )


def delete_chat_for_me(
    db: Session,
    chat_id: int,
    user_id: int
):
    chat = _get_user_chat(
        db,
        chat_id,
        user_id
    )

    if not chat:
        logger.warning(
            "Delete chat for self failed: chat not found or access denied "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return False

    existing = get_chat_deletion(
        db,
        chat_id,
        user_id
    )

    if existing:
        logger.info(
            "Chat already deleted for self: chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return True

    db.add(
        ChatDeletion(
            chat_id=chat_id,
            user_id=user_id
        )
    )
    logger.info(
        "Chat marked as deleted for self: chat_id=%s user_id=%s",
        chat_id,
        user_id,
    )
    db.commit()

    return True


def delete_chat_for_all(
    db: Session,
    chat_id: int,
    user_id: int
):
    chat = _get_user_chat(
        db,
        chat_id,
        user_id
    )

    if not chat:
        logger.warning(
            "Delete chat for all failed: chat not found or access denied "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return False

    if not chat.is_private:
        logger.warning(
            "Delete chat for all denied: chat is not private "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return False

    if chat.is_favorite:
        logger.warning(
            "Delete chat for all denied: favorite chat "
            "chat_id=%s user_id=%s",
            chat_id,
            user_id,
        )
        return False

    if len(chat.members) != 2:
        logger.warning(
            "Delete chat for all denied: invalid member count "
            "chat_id=%s user_id=%s member_count=%s",
            chat_id,
            user_id,
            len(chat.members),
        )
        return False

    _delete_chat_messages(
        db,
        chat_id
    )

    db.query(ChatDeletion).filter(
        ChatDeletion.chat_id == chat_id
    ).delete(
        synchronize_session=False
    )

    db.delete(chat)
    db.commit()
    logger.info(
        "Chat deleted for all: chat_id=%s user_id=%s",
        chat_id,
        user_id,
    )
    return True


def get_chat_name(
    chat: Chat,
    current_user_id: int
) -> str:

    if chat.is_favorite:
        return "Избранное"

    if chat.is_private:

        for member in chat.members:

            if member.id != current_user_id:
                return member.username

        return "Chat"

    return chat.name or "Group Chat"



def get_or_create_favorite_chat(
    db: Session,
    user_id: int
):
    # Ищем существующее Избранное
    chat = (
        db.query(Chat)
        .filter(Chat.is_favorite == True)
        .filter(
            Chat.members.any(
                User.id == user_id
            )
        )
        .first()
    )

    if chat:
        logger.info(
            "Favorite chat found: chat_id=%s user_id=%s",
            chat.id,
            user_id,
        )
        # Проверяем, удалял ли пользователь
        # это Избранное у себя
        deletion = (
            db.query(ChatDeletion)
            .filter(
                ChatDeletion.chat_id == chat.id,
                ChatDeletion.user_id == user_id
            )
            .first()
        )

        if deletion:
            logger.info(
                "Restoring favorite chat: chat_id=%s user_id=%s",
                chat.id,
                user_id,
            )
            _delete_chat_messages(
                db,
                chat.id
            )

            db.query(ChatDeletion).filter(
                ChatDeletion.chat_id == chat.id,
                ChatDeletion.user_id == user_id
            ).delete(
                synchronize_session=False
            )

            db.commit()
            logger.info(
                "Favorite chat restored: chat_id=%s user_id=%s",
                chat.id,
                user_id,
            )
            return chat

        # Избранное существует и не удалялось
        return chat

    # Избранного вообще нет — создаём
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        logger.warning(
            "Favorite chat creation failed: user not found user_id=%s",
            user_id,
        )
        return None

    new_chat = Chat(
        is_private=True,
        is_favorite=True,
        name="Избранное"
    )

    new_chat.members.append(user)

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    logger.info(
        "Favorite chat created: chat_id=%s user_id=%s",
        new_chat.id,
        user_id,
    )
    return new_chat