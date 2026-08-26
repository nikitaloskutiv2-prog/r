from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    HTTPException,
    File as FastAPIFile
)

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user

from app.schemas.file import FileResponse

from app.services import file_service

from fastapi.responses import FileResponse as FastAPIFileResponse

from app.models.file import File

import logging


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/files",
    tags=["files"]
)


@router.post(
    "/upload",
    response_model=FileResponse
)
def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if not file.filename:

        logger.warning(
            "File upload rejected: filename missing "
            "user_id=%s",
            current_user.id,
        )

        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    if not file.content_type:

        logger.warning(
            "File upload rejected: MIME type missing "
            "user_id=%s filename=%s",
            current_user.id,
            file.filename,
        )

        raise HTTPException(
            status_code=400,
            detail="File type is required"
        )

    try:

        saved_file = file_service.save_file(
            db,
            file,
            current_user.id
        )

    except ValueError as error:

        logger.warning(
            "File upload rejected: "
            "user_id=%s filename=%s "
            "mime_type=%s reason=%s",
            current_user.id,
            file.filename,
            file.content_type,
            str(error),
        )

        raise HTTPException(
            status_code=413,
            detail="File size exceeds the allowed limit"
        )

    except Exception:

        logger.exception(
            "File upload failed: "
            "user_id=%s filename=%s "
            "mime_type=%s",
            current_user.id,
            file.filename,
            file.content_type,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload file"
        )

    logger.info(
        "File uploaded: "
        "user_id=%s file_id=%s "
        "filename=%s size=%s",
        current_user.id,
        saved_file.id,
        file.filename,
        saved_file.size,
    )

    return saved_file


@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    file = (
        db.query(File)
        .filter(File.id == file_id)
        .first()
    )

    if not file:

        logger.warning(
            "File download failed: "
            "file not found "
            "file_id=%s user_id=%s",
            file_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    if not file.path:

        logger.error(
            "File download failed: "
            "path missing "
            "file_id=%s user_id=%s",
            file_id,
            current_user.id,
        )

        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    logger.info(
        "File downloaded: "
        "user_id=%s file_id=%s filename=%s",
        current_user.id,
        file.id,
        file.original_name,
    )

    return FastAPIFileResponse(
        path=file.path,
        filename=file.original_name,
        media_type=file.mime_type
    )