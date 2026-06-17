import os
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import Session as DBSession, UploadedFile, User

router = APIRouter(prefix="/api/sessions/{session_id}/files", tags=["files"])

class UploadedFileResponse(BaseModel):
    id: UUID
    session_id: UUID
    filename: str
    file_size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

def get_current_user(db: Session = Depends(get_db)) -> User:
    # Placeholder for actual authentication logic.
    user = db.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found"
        )
    return user

def validate_session(session_id: UUID, current_user: User, db: Session) -> DBSession:
    db_session = db.query(DBSession).filter(
        DBSession.id == session_id,
        DBSession.user_id == current_user.id
    ).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return db_session

@router.post("/", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    session_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file to a specific session."""
    # Validate session exists and belongs to user
    db_session = validate_session(session_id, current_user, db)

    # Read file content to calculate size
    content = await file.read()
    file_size = len(content)

    # Save file info to database
    uploaded_file = UploadedFile(
        session_id=session_id,
        filename=file.filename,
        file_size_bytes=file_size,
        uploaded_at=datetime.utcnow()
    )
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    # In a real app, you would also save the file to disk or cloud storage here.
    # For now, we just log it.
    print(f"File {file.filename} uploaded for session {session_id}, size {file_size} bytes")

    return uploaded_file