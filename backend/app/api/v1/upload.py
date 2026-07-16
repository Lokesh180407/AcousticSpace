import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.api.deps import resolve_owner_identity
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.audio import UploadedAudio
from app.schemas.audio import UploadResponse

router = APIRouter(prefix="/audio", tags=["Audio"])


def _validate_upload(file: UploadFile, size_bytes: int) -> None:
    if file.content_type not in settings.ALLOWED_AUDIO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {file.content_type}",
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )
    if size_bytes == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")


def _save_to_disk(file: UploadFile, content: bytes) -> Tuple[str, str]:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or "").suffix
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = upload_dir / stored_name

    with open(stored_path, "wb") as f:
        f.write(content)

    return stored_name, str(stored_path)


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_audio(
    response: Response,
    file: UploadFile = File(...),
    owner: Tuple[Optional[User], Optional[str]] = Depends(resolve_owner_identity),
    db: Session = Depends(get_db),
):
    current_user, guest_id = owner

    content = file.file.read()
    _validate_upload(file, len(content))

    _, storage_path = _save_to_disk(file, content)

    audio = UploadedAudio(
        user_id=current_user.id if current_user else None,
        guest_id=guest_id,  # None when authenticated, set when anonymous
        original_filename=file.filename or "unknown",
        storage_path=storage_path,
        content_type=file.content_type,
        file_size_bytes=len(content),
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)

    # Echo the guest id back so the client can persist it (e.g. localStorage)
    # and send it as X-Guest-Id on subsequent requests to keep continuity.
    if guest_id:
        response.headers[settings.GUEST_ID_HEADER_NAME] = guest_id

    return UploadResponse(audio=audio, guest_id=guest_id)
