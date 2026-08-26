from sqlalchemy.orm import Session
from app.models.reaction import MessageReaction
import logging

logger = logging.getLogger(__name__)

def toggle_reaction(
    db: Session,
    message_id: int,
    user_id: int,
    emoji: str
):

    existing = (
        db.query(MessageReaction)
        .filter(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id
        )
        .first()
    )

    if existing:

        if existing.emoji == emoji:

            db.delete(existing)
            db.commit()
            logger.info(
                "Reaction removed: message_id=%s user_id=%s emoji=%s",
                message_id,
                user_id,
                emoji,
            )
            return "removed"

        existing.emoji = emoji
        db.commit()
        logger.info(
            "Reaction updated: message_id=%s user_id=%s emoji=%s",
            message_id,
            user_id,
            emoji,
        )
        return "updated"

    reaction = MessageReaction(
        message_id=message_id,
        user_id=user_id,
        emoji=emoji
    )

    db.add(reaction)
    db.commit()
    logger.info(
        "Reaction added: message_id=%s user_id=%s emoji=%s",
        message_id,
        user_id,
        emoji,
    )
    return "added"


def get_message_reactions(
    db: Session,
    message_id: int,
    current_user_id: int
):

    reactions = (
        db.query(MessageReaction)
        .filter(
            MessageReaction.message_id == message_id
        )
        .all()
    )
    logger.info(
        "Message reactions loaded: message_id=%s user_id=%s count=%s",
        message_id,
        current_user_id,
        len(reactions),
    )
    result = {}

    for reaction in reactions:

        if reaction.emoji not in result:

            result[reaction.emoji] = {
                "count": 0,
                "users": []
            }

        result[reaction.emoji]["count"] += 1
        result[reaction.emoji]["users"].append(
            reaction.user_id
        )

    return result