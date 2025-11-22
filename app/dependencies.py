import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .authorization import AccessLevel, ensure_subject_meets_level
from .database import SessionLocal
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(get_password_hash(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return hmac.new(SECRET_KEY.encode(), msg=password.encode(), digestmod=hashlib.sha256).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.isoformat()})
    message = json.dumps(to_encode, separators=(",", ":"), sort_keys=True).encode()
    message_b64 = _b64encode(message)
    signature = hmac.new(SECRET_KEY.encode(), msg=message_b64.encode(), digestmod=hashlib.sha256)
    token = f"{message_b64}.{_b64encode(signature.digest())}"
    return token


def _decode_access_token(token: str) -> dict:
    try:
        message_b64, signature_b64 = token.split(".", maxsplit=1)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    expected_signature = hmac.new(
        SECRET_KEY.encode(), msg=message_b64.encode(), digestmod=hashlib.sha256
    )
    if not hmac.compare_digest(_b64encode(expected_signature.digest()), signature_b64):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = json.loads(_b64decode(message_b64))
        exp_raw = payload.get("exp")
        if not exp_raw:
            raise ValueError
        expires_at = datetime.fromisoformat(exp_raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    return payload


def get_current_user(
    db: Session = Depends(get_db),
    session: str | None = Cookie(default=None)
) -> User:
    print(f"get_current_user called, session cookie: {session}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not session:
        print("No session cookie found")
        raise credentials_exception
    
    try:
        payload = _decode_access_token(session)
        user_id = payload.get("sub")
        print(f"Token decoded, user_id: {user_id}")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except HTTPException as e:
        print(f"Token decode failed: {e}")
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print("User not found in database")
        raise credentials_exception
    print(f"User authenticated: {user.email}")
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def ensure_access_level(db: Session, user_id: int, required_level: AccessLevel) -> User:
    user = get_user_by_id(db, user_id)
    ensure_subject_meets_level(user, required_level)
    return user
