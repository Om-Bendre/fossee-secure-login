from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import File, User
from ..authorization import FileOwnershipPolicy, FileResource, UserSubject
from ..authorization.adapters import EmptyEnvironment, FileDownloadAction, FileReadAction
from ..authorization.core import AuthorizationContext, PolicyEngine

router = APIRouter()
FILE_POLICY_ENGINE = PolicyEngine([FileOwnershipPolicy()])


def authorize_file_access(current_user: User, file: File, action) -> bool:
    context = AuthorizationContext(
        subject=UserSubject(current_user),
        resource=FileResource(file),
        action=action,
        environment=EmptyEnvironment(),
    )
    return FILE_POLICY_ENGINE.authorize(context)

def serialize_file(file: File) -> dict:
    return {
        "id": str(file.id),
        "ownerId": str(file.owner_id),
        "fileName": file.file_name,
        "mimeType": file.mime_type,
        "sizeBytes": file.size_bytes or 0,
        "uploadedAt": file.uploaded_at.isoformat() if file.uploaded_at else None,
    }

def get_owned_file(file_id: UUID, current_user: User, db: Session) -> File:
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not authorize_file_access(current_user, file, FileReadAction()):
        raise HTTPException(status_code=403, detail="You do not have access to this file")
    return file

@router.get("/files")
def get_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    files = db.query(File).filter(File.owner_id == current_user.id).all()
    return [serialize_file(file) for file in files]

@router.get("/files/{file_id}")
def get_file(file_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return serialize_file(get_owned_file(file_id, current_user, db))

@router.get("/files/{file_id}/download")
def download_file(file_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not authorize_file_access(current_user, file, FileDownloadAction()):
        raise HTTPException(status_code=403, detail="You do not have access to this file")
    path = Path(file.storage_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File content not found")
    return FileResponse(path, media_type=file.mime_type, filename=file.file_name)
