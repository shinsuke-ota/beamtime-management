from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User, UserRole


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_role(db: Session, user_id: int, role: UserRole) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role != role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User must have role {role}",
        )
    return user
