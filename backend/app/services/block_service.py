import logging

from sqlalchemy.orm import Session

from app.models.user_block import UserBlock


logger = logging.getLogger(__name__)


def block_user(
    db: Session,
    blocker_id: int,
    blocked_id: int
):
    if blocker_id == blocked_id:
        logger.warning(
            "Block user failed: user tried to block themselves user_id=%s",
            blocker_id,
        )
        raise Exception("You can't block yourself")

    existing = (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        )
        .first()
    )

    if existing:
        logger.debug(
            "User already blocked: blocker_id=%s blocked_id=%s",
            blocker_id,
            blocked_id,
        )
        return existing

    block = UserBlock(
        blocker_id=blocker_id,
        blocked_id=blocked_id
    )

    db.add(block)
    db.commit()
    db.refresh(block)

    logger.info(
        "User blocked: blocker_id=%s blocked_id=%s",
        blocker_id,
        blocked_id,
    )

    return block


def unblock_user(
    db: Session,
    blocker_id: int,
    blocked_id: int
):
    block = (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        )
        .first()
    )

    if block:
        db.delete(block)
        db.commit()

        logger.info(
            "User unblocked: blocker_id=%s blocked_id=%s",
            blocker_id,
            blocked_id,
        )
    else:
        logger.debug(
            "Unblock skipped: block does not exist "
            "blocker_id=%s blocked_id=%s",
            blocker_id,
            blocked_id,
        )

    return True


def is_blocked(
    db: Session,
    blocker_id: int,
    blocked_id: int
) -> bool:

    return (
        db.query(UserBlock)
        .filter(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        )
        .first()
        is not None
    )


def are_users_blocked(
    db: Session,
    user1: int,
    user2: int
) -> bool:

    return (
        db.query(UserBlock)
        .filter(
            (
                (UserBlock.blocker_id == user1)
                &
                (UserBlock.blocked_id == user2)
            )
            |
            (
                (UserBlock.blocker_id == user2)
                &
                (UserBlock.blocked_id == user1)
            )
        )
        .first()
        is not None
    )