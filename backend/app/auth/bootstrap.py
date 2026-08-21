import os

from app.database import SessionLocal

from .models import UserRole
from .repository import UserRepository
from .schemas import UserCreate, UserUpdate


def main() -> None:
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are required"
        )
    data = UserCreate(email=email, password=password, role=UserRole.ADMIN)
    with SessionLocal() as session:
        repository = UserRepository(session)
        user = repository.get_by_email(email)
        if user is None:
            repository.create(data)
            print(f"Created admin user {email}")
            return

        needs_promotion = user.role != UserRole.ADMIN
        needs_reactivation = not user.is_active
        if not needs_promotion and not needs_reactivation:
            print(f"Admin user {email} is already valid (active with admin role)")
            return

        repository.update(
            user.id,
            UserUpdate(
                role=UserRole.ADMIN if needs_promotion else user.role,
                is_active=True if needs_reactivation else user.is_active,
            ),
        )
        if needs_promotion:
            print(f"Promoted user {email} to admin")
        if needs_reactivation:
            print(f"Reactivated user {email}")


if __name__ == "__main__":
    main()
