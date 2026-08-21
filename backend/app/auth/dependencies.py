from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db

from .models import UserModel, UserRole
from .repository import UserRepository
from .security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> UserModel:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise credentials_error
        user_id = int(subject)
    except (jwt.PyJWTError, ValueError):
        raise credentials_error from None

    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[CurrentUser], UserModel]:
    def dependency(user: CurrentUser) -> UserModel:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


AuthenticatedUser = Annotated[
    UserModel, Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))
]
AdminUser = Annotated[UserModel, Depends(require_roles(UserRole.ADMIN))]
AgentUser = Annotated[UserModel, Depends(require_roles(UserRole.AGENT))]
