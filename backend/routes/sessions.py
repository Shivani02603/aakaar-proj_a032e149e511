from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import Session as DBSession, User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionBase(BaseModel):
    name: str

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

def get_current_user(db: Session = Depends(get_db)) -> User:
    # This is a placeholder for actual authentication logic.
    # In a real app, you would extract user from JWT token.
    # For now, we'll return the first user as a mock.
    user = db.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found"
        )
    return user

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new session for the current user."""
    db_session = DBSession(
        user_id=current_user.id,
        name=session_data.name,
        created_at=datetime.utcnow()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/", response_model=List[SessionResponse])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all sessions for the current user."""
    sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).all()
    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific session by ID, ensuring it belongs to the current user."""
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