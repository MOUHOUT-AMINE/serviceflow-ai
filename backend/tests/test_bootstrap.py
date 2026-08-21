import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.auth import bootstrap
from app.auth.models import UserModel, UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate


BOOTSTRAP_EMAIL = "bootstrap@example.com"
BOOTSTRAP_PASSWORD = "strong-password"


@pytest.fixture
def run_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: sessionmaker[Session],
):
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", f"  {BOOTSTRAP_EMAIL.upper()}  ")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", BOOTSTRAP_PASSWORD)
    monkeypatch.setattr(bootstrap, "SessionLocal", session_factory)
    return bootstrap.main


def create_existing_user(
    db_session: Session, *, role: UserRole, is_active: bool
) -> UserModel:
    user = UserRepository(db_session).create(
        UserCreate(
            email=BOOTSTRAP_EMAIL,
            password="existing-password",
            role=role,
        )
    )
    if not is_active:
        user.is_active = False
        db_session.commit()
        db_session.refresh(user)
    return user


def test_bootstrap_creates_active_admin(
    db_session: Session, run_bootstrap, capsys: pytest.CaptureFixture[str]
) -> None:
    run_bootstrap()

    user = UserRepository(db_session).get_by_email(BOOTSTRAP_EMAIL)
    assert user is not None
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert capsys.readouterr().out == f"Created admin user {BOOTSTRAP_EMAIL}\n"


def test_bootstrap_promotes_existing_active_user(
    db_session: Session, run_bootstrap, capsys: pytest.CaptureFixture[str]
) -> None:
    user = create_existing_user(db_session, role=UserRole.AGENT, is_active=True)
    original_password_hash = user.password_hash

    run_bootstrap()

    db_session.refresh(user)
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert user.password_hash == original_password_hash
    assert capsys.readouterr().out == f"Promoted user {BOOTSTRAP_EMAIL} to admin\n"


def test_bootstrap_reactivates_existing_admin(
    db_session: Session, run_bootstrap, capsys: pytest.CaptureFixture[str]
) -> None:
    user = create_existing_user(db_session, role=UserRole.ADMIN, is_active=False)

    run_bootstrap()

    db_session.refresh(user)
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert capsys.readouterr().out == f"Reactivated user {BOOTSTRAP_EMAIL}\n"


def test_bootstrap_promotes_and_reactivates_existing_user(
    db_session: Session, run_bootstrap, capsys: pytest.CaptureFixture[str]
) -> None:
    user = create_existing_user(db_session, role=UserRole.AGENT, is_active=False)

    run_bootstrap()

    db_session.refresh(user)
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert capsys.readouterr().out == (
        f"Promoted user {BOOTSTRAP_EMAIL} to admin\n"
        f"Reactivated user {BOOTSTRAP_EMAIL}\n"
    )


def test_bootstrap_reports_valid_admin_and_remains_idempotent(
    db_session: Session, run_bootstrap, capsys: pytest.CaptureFixture[str]
) -> None:
    user = create_existing_user(db_session, role=UserRole.ADMIN, is_active=True)

    run_bootstrap()
    run_bootstrap()

    db_session.refresh(user)
    assert user.role == UserRole.ADMIN
    assert user.is_active is True
    assert len(UserRepository(db_session).list()) == 1
    assert capsys.readouterr().out == (
        f"Admin user {BOOTSTRAP_EMAIL} is already valid (active with admin role)\n" * 2
    )
