from sqlalchemy.orm import Session
from app.models.user import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def search_users(db: Session, query: str):
    query = query.strip()

    if not query:
        return []
    if query.startswith("@"):
        query = query[1:]

    usernameid = f"@{query}"

    # 1. Сначала проверяем точное совпадение
    exact_user = (
        db.query(User)
        .filter(
            User.usernameid.ilike(usernameid)
        )
        .first()
    )

    if exact_user:
        logger.info(
            "User search exact match: query=%s user_id=%s",
            query,
            exact_user.id,
        )
        return [exact_user]

    # 2. Если точного совпадения нет —
    # показываем максимум 5 похожих
    users = (
        db.query(User)
        .filter(
            User.usernameid.ilike(f"{usernameid}%")
        )
        .limit(5)
        .all()
    )

    logger.info(
        "User search completed: query=%s result_count=%s",
        query,
        len(users),
    )

    return users



def delete_account(db, user: User):
    """
    Анонимизация аккаунта.
    Сообщения и чаты сохраняются.
    """
    logger.info(
        "Account deletion started: user_id=%s",
        user.id,
    )

    user.login = None
    user.username = "Аккаунт удалён"
    user.usernameid = None

    user.bio = ""
    user.birthday = ""

  
    user.avatar = "/storage/ghost.png"

    user.status = "offline"
    user.last_seen = datetime(2000, 1, 1)

    user.is_deleted = True

    db.commit()
    db.refresh(user)
    logger.info(
        "Account anonymized: user_id=%s",
        user.id,
    )
    return user