import uuid
from fastapi import Depends, Header, HTTPException
from jose import JWTError
from sqlalchemy.orm import Session
from .database import get_db
from .models import RevokedToken, User
from .security import decode_token

def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token)
        jti = uuid.UUID(str(payload["jti"]))
        user_id = uuid.UUID(str(payload["sub"]))
    except (JWTError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Not authenticated")
    if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
