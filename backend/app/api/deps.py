import uuid
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_token, generate_guest_id
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=False
)


def _get_user_from_token(token: str, db: Session) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_error

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    user = db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise credentials_error
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _get_user_from_token(token, db)


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        return _get_user_from_token(token, db)
    except HTTPException:
        return None


def resolve_owner_identity(
    current_user: Optional[User] = Depends(get_optional_current_user),
    x_guest_id: Optional[str] = Header(default=None, alias=settings.GUEST_ID_HEADER_NAME),
) -> Tuple[Optional[User], Optional[str]]:
    if current_user:
        return current_user, None

    guest_id = x_guest_id or generate_guest_id()
    return None, guest_id
