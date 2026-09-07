import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.utils.file_validation import (
    validate_extension,
    validate_size,
    validate_magic_bytes,
    validate_safe_filename,
    FileValidationError,
)
from app.utils.hashing import compute_sha256, generate_stored_filename
from app.services.audit_service import log_audit_event, log_security_event

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploads"


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        validate_safe_filename(file.filename)
        extension = validate_extension(file.filename)

        file_bytes = await file.read()

        validate_size(file_bytes)
        detected_mime = validate_magic_bytes(file_bytes)

    except FileValidationError as e:
        log_security_event(
            db,
            event_type=e.event_type,
            severity="MEDIUM",
            user_id=current_user.id,
            description=e.reason,
            ip_address=request.client.host,
            event_metadata={"attempted_filename": file.filename},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.reason)

    sha256_hash = compute_sha256(file_bytes)
    stored_filename = generate_stored_filename(extension)
    stored_path = os.path.join(UPLOAD_DIR, stored_filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    new_document = Document(
        owner_id=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        mime_type=detected_mime,
        file_size=len(file_bytes),
        sha256_hash=sha256_hash,
        status="pending",
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    log_audit_event(
        db,
        action="DOCUMENT_UPLOADED",
        user_id=current_user.id,
        resource_type="document",
        resource_id=str(new_document.id),
        ip_address=request.client.host,
        details={"filename": file.filename, "sha256": sha256_hash},
    )

    return new_document