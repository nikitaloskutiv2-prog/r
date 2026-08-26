import os
import uuid
import logging

import cv2

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.file import File


logger = logging.getLogger(__name__)


MAX_AVATAR_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIZE = 50 * 1024 * 1024
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024
MAX_DOCUMENT_SIZE = 250 * 1024 * 1024

MAX_VOICE_DURATION = 2 * 60 * 60

UPLOAD_CHUNK_SIZE = 1024 * 1024


def get_file_size_limit(
    mime_type: str,
    is_voice: bool = False
) -> int | None:

    if is_voice:
        return None

    if mime_type.startswith("image/"):
        return MAX_IMAGE_SIZE

    if mime_type.startswith("video/"):
        return MAX_VIDEO_SIZE

    return MAX_DOCUMENT_SIZE


def save_uploaded_file(
    uploaded_file: UploadFile,
    file_path: str,
    max_size: int | None = None
) -> int:

    total_size = 0

    try:

        with open(file_path, "wb") as buffer:

            while True:

                chunk = uploaded_file.file.read(
                    UPLOAD_CHUNK_SIZE
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if (
                    max_size is not None
                    and total_size > max_size
                ):

                    raise ValueError(
                        "File size exceeds the allowed limit"
                    )

                buffer.write(chunk)

    except Exception:

        if os.path.exists(file_path):

            try:
                os.remove(file_path)

            except OSError:

                logger.exception(
                    "Failed to remove incomplete file: path=%s",
                    file_path
                )

        raise

    return total_size


def save_file(
    db: Session,
    uploaded_file: UploadFile,
    user_id: int,
    is_voice: bool = False
):

    filename = uploaded_file.filename or "file"

    ext = os.path.splitext(filename)[1]

    stored_name = f"{uuid.uuid4()}{ext}"

    mime_type = uploaded_file.content_type or ""

    max_size = get_file_size_limit(
        mime_type,
        is_voice=is_voice
    )

    if mime_type.startswith("image/"):

        folder = "storage/images"

    elif mime_type.startswith("video/"):

        folder = "storage/videos"

    elif is_voice:

        folder = "storage/voices"

    else:

        folder = "storage/files"

    logger.info(
        "Saving file: "
        "user_id=%s filename=%s mime_type=%s "
        "folder=%s max_size=%s",
        user_id,
        filename,
        mime_type,
        folder,
        max_size,
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    os.makedirs(
        "storage/thumbnails",
        exist_ok=True
    )

    file_path = os.path.join(
        folder,
        stored_name
    )

    try:

        size = save_uploaded_file(
            uploaded_file,
            file_path,
            max_size
        )

    except ValueError:

        logger.warning(
            "File upload rejected: "
            "size limit exceeded "
            "user_id=%s filename=%s "
            "mime_type=%s size_limit=%s",
            user_id,
            filename,
            mime_type,
            max_size,
        )

        raise

    logger.info(
        "File saved to storage: "
        "user_id=%s filename=%s path=%s size=%s",
        user_id,
        filename,
        file_path.replace("\\", "/"),
        size,
    )

    thumbnail_path = None

    if mime_type.startswith("video/"):

        try:

            cap = cv2.VideoCapture(file_path)

            success, frame = cap.read()

            cap.release()

            if success:

                thumb_name = f"{uuid.uuid4()}.jpg"

                thumbnail_path = os.path.join(
                    "storage/thumbnails",
                    thumb_name
                )

                thumbnail_created = cv2.imwrite(
                    thumbnail_path,
                    frame
                )

                if not thumbnail_created:

                    thumbnail_path = None

                else:

                    thumbnail_path = (
                        thumbnail_path
                        .replace("\\", "/")
                    )

                    logger.info(
                        "Video thumbnail created: "
                        "user_id=%s filename=%s "
                        "thumbnail_path=%s",
                        user_id,
                        filename,
                        thumbnail_path,
                    )

        except Exception:

            logger.exception(
                "Failed to create video thumbnail: "
                "user_id=%s filename=%s",
                user_id,
                filename,
            )

            thumbnail_path = None

    db_file = File(
        original_name=filename,
        stored_name=stored_name,
        path=file_path.replace("\\", "/"),
        mime_type=mime_type,
        size=size,
        uploader_id=user_id,
        thumbnail_path=thumbnail_path,
    )

    try:

        db.add(db_file)

        db.commit()

        db.refresh(db_file)

    except Exception:

        db.rollback()

        if os.path.exists(file_path):

            try:
                os.remove(file_path)

            except OSError:

                logger.exception(
                    "Failed to remove file after "
                    "database error: path=%s",
                    file_path
                )

        if (
            thumbnail_path
            and os.path.exists(thumbnail_path)
        ):

            try:
                os.remove(thumbnail_path)

            except OSError:

                logger.exception(
                    "Failed to remove thumbnail "
                    "after database error: path=%s",
                    thumbnail_path
                )

        raise

    logger.info(
        "File record created: "
        "file_id=%s user_id=%s filename=%s "
        "mime_type=%s size=%s",
        db_file.id,
        user_id,
        db_file.original_name,
        db_file.mime_type,
        db_file.size,
    )

    return db_file


def upload_voice(
    db: Session,
    uploaded_file: UploadFile,
    chat_id: int,
    user_id: int,
    duration: int,
    waveform: str
):

    if duration < 0:

        raise ValueError(
            "Voice duration cannot be negative"
        )

    if duration > MAX_VOICE_DURATION:

        raise ValueError(
            "Voice duration exceeds the allowed limit"
        )

    db_file = save_file(
        db,
        uploaded_file,
        user_id,
        is_voice=True
    )

    logger.info(
        "Voice file uploaded: "
        "file_id=%s chat_id=%s "
        "user_id=%s duration=%s",
        db_file.id,
        chat_id,
        user_id,
        duration,
    )

    return {
        "file_id": db_file.id,
        "duration": duration,
        "waveform": waveform,
        "file": {
            "id": db_file.id,
            "path": db_file.path,
            "mime_type": db_file.mime_type,
            "original_name": db_file.original_name,
            "thumbnail_path": db_file.thumbnail_path,
            "size": db_file.size,
        }
    }