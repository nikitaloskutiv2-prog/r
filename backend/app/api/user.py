from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, selectinload
from typing import List
from app.schemas.user import UserResponse, UserSearchResponse, UserStatusUpdate, UserUpdate
from app.db.session import get_db
from app.core.deps import get_current_user
from app.services import user_service, block_service, file_service
from app.models.user import User
import os
import uuid
from datetime import datetime
from app.models.chat import Chat
from app.websocket.chat_ws import notify_block_changed, notify_account_deleted
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[UserSearchResponse])
def search_users(query: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return user_service.search_users(db, query)


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить профиль текущего пользователя"""
    
    if user_data.username is not None:
        current_user.username = user_data.username
    
    if user_data.usernameid is not None:
        # Проверяем, что usernameid не занят другим пользователем
        existing = db.query(User).filter(
            User.usernameid == user_data.usernameid,
            User.id != current_user.id
        ).first()
        if existing:
            logger.warning(
                "Profile update rejected: usernameid already taken "
                "user_id=%s usernameid=%s",
                current_user.id,
                user_data.usernameid,
            )

            raise HTTPException(
                status_code=400,
                detail="UserID already taken"
            )
        
        current_user.usernameid = user_data.usernameid
    
    if user_data.bio is not None:
        current_user.bio = user_data.bio
    
    if user_data.birthday is not None:
        current_user.birthday = user_data.birthday
    
    db.commit()
    db.refresh(current_user)
    logger.info(
        "User profile updated: user_id=%s",
        current_user.id,
    )

    return current_user


@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_deleted:
        logger.warning(
            "Account deletion rejected: already deleted user_id=%s",
            current_user.id,
        )
        raise HTTPException(
            status_code=400,
            detail="Account already deleted"
        )

    deleted_user_id = current_user.id

    # Находим все личные чаты удаляемого пользователя
    chats = (
        db.query(Chat)
        .options(
            selectinload(Chat.members)
        )
        .filter(
            Chat.is_private.is_(True),
            Chat.members.any(User.id == deleted_user_id)
        )
        .all()
    )

    # Собираем ID собеседников
    notify_user_ids = set()

    for chat in chats:
        for member in chat.members:

            if member.id != deleted_user_id:
                notify_user_ids.add(member.id)

    # Помечаем аккаунт удалённым
    user_service.delete_account(
        db=db,
        user=current_user
    )

    # Realtime уведомление собеседникам
    await notify_account_deleted(
        deleted_user_id,
        list(notify_user_ids)
    )
    logger.info(
        "User account deleted: user_id=%s notified_users=%s",
        deleted_user_id,
        len(notify_user_ids),
    )
    return {
        "success": True,
        "message": "Account deleted"
    }

@router.post("/me/avatar")
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # проверяем тип файла
    if not avatar.content_type or not avatar.content_type.startswith("image/"):
        logger.warning(
            "Avatar upload rejected: invalid content type "
            "user_id=%s content_type=%s",
            current_user.id,
            avatar.content_type,
        )

        raise HTTPException(
            status_code=400,
            detail="Only images allowed"
        )
    max_size = file_service.MAX_AVATAR_SIZE
    os.makedirs("storage/avatars", exist_ok=True)

    if not avatar.filename:
        logger.warning(
            "Avatar upload rejected: filename missing "
            "user_id=%s",
            current_user.id,
        )

        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    
    ext = os.path.splitext(avatar.filename or "")[1]

    
    filename = f"{uuid.uuid4()}{ext}"

    filepath = os.path.join(
        "storage",
        "avatars",
        filename
    )

    try:
        file_service.save_uploaded_file(
            avatar,
            filepath,
            max_size
        )

    except ValueError:

        logger.warning(
            "Avatar upload rejected: size limit exceeded "
            "user_id=%s filename=%s limit=%s",
            current_user.id,
            avatar.filename,
            max_size,
        )

        raise HTTPException(
            status_code=413,
            detail="Avatar size exceeds the allowed limit"
        )

    # удалить старую аватарку
    if current_user.avatar:
        old = current_user.avatar.lstrip("/")
        if os.path.exists(old):
            try:
                os.remove(old)
            except OSError as e:
                logger.warning(
                    "Failed to remove old avatar: user_id=%s error=%s",
                    current_user.id,
                    e,
                )

    current_user.avatar = f"/storage/avatars/{filename}"

    db.commit()
    db.refresh(current_user)

    logger.info(
        "User avatar updated: user_id=%s",
        current_user.id,
    )
    return {
        "avatar": current_user.avatar
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        logger.warning(
            "User lookup failed: user not found user_id=%s requester_id=%s",
            user_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user



@router.post("/me/status")
def update_user_status(
    status_data: UserStatusUpdate,  # 👈 используем схему
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.status = status_data.status
    current_user.last_seen = datetime.fromisoformat(status_data.last_seen.replace('Z', '+00:00'))
    db.commit()
    logger.info(
        "User status updated: user_id=%s status=%s",
        current_user.id,
        status_data.status,
    )
    return {"status": "updated"}

@router.get("/{user_id}/status")
def get_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        logger.warning(
            "User status lookup failed: user not found "
            "user_id=%s requester_id=%s",
            user_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "status": user.status,
        "last_seen": (
            user.last_seen.isoformat()
            if user.last_seen
            else None
        )
    }

@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    block_service.block_user(
        db=db,
        blocker_id=current_user.id,
        blocked_id=user_id
    )
    await notify_block_changed(
        current_user.id,
        user_id
    )
    logger.info(
        "User blocked: blocker_id=%s blocked_id=%s",
        current_user.id,
        user_id,
    )
    return {
        "success": True
    }


@router.delete("/{user_id}/block")
async def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    block_service.unblock_user(
        db=db,
        blocker_id=current_user.id,
        blocked_id=user_id
    )
    await notify_block_changed(
        current_user.id,
        user_id
    )
    logger.info(
        "User unblocked: blocker_id=%s blocked_id=%s",
        current_user.id,
        user_id,
    )
    return {
        "success": True
    }


@router.get("/{user_id}/block-status")
def get_block_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    i_blocked = block_service.is_blocked(
        db,
        current_user.id,
        user_id
    )

    blocked_me = block_service.is_blocked(
        db,
        user_id,
        current_user.id
    )

    return {

        "i_blocked": i_blocked,

        "blocked_me": blocked_me,

        "blocked": i_blocked or blocked_me
    }

