from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminUser
from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import User, UserCreate, UserUpdate
from app.database import get_db


router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository(db: Annotated[Session, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    _: AdminUser,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        return repository.create(data)
    except IntegrityError:
        repository.session.rollback()
        raise HTTPException(status_code=409, detail="Email already exists") from None


@router.get("", response_model=list[User])
def list_users(
    _: AdminUser,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> list[User]:
    return repository.list()


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    _: AdminUser,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    user = repository.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: AdminUser,
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if user_id == current_user.id and data.role == UserRole.AGENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote their own account",
        )
    if user_id == current_user.id and data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account",
        )
    user = repository.update(user_id, data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
