from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import UserModel
from .schemas import UserCreate, UserUpdate
from .security import hash_password


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: UserCreate) -> UserModel:
        user = UserModel(
            email=str(data.email).lower(),
            password_hash=hash_password(data.password),
            role=data.role,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def list(self) -> list[UserModel]:
        return list(self.session.scalars(select(UserModel).order_by(UserModel.id)))

    def get(self, user_id: int) -> UserModel | None:
        return self.session.get(UserModel, user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        statement = select(UserModel).where(func.lower(UserModel.email) == email.lower())
        return self.session.scalar(statement)

    def update(self, user_id: int, data: UserUpdate) -> UserModel | None:
        user = self.get(user_id)
        if user is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        self.session.commit()
        self.session.refresh(user)
        return user
