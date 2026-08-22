import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import RevokedToken, User
from ..rate_limit import clear_failures, is_locked, record_failure
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..security import create_access_token, decode_token, hash_password, verify_password

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email}

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email = data.email.lower()
    if is_locked(email):
        raise HTTPException(status_code=429, detail="Too many failed login attempts. Try again later.")
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(data.password, user.password_hash):
        record_failure(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    clear_failures(email)
    token, _, _ = create_access_token(str(user.id))
    return {"token": token, "user": {"id": str(user.id), "email": user.email}}

@router.post("/logout")
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
        jti = uuid.UUID(str(payload["jti"]))
        expires_at = datetime.fromtimestamp(float(payload["exp"]), tz=timezone.utc)
    except (JWTError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
        db.commit()
    return {"message": "Logout successful"}
