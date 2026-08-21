from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.auth.router as auth_router
from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate
from app.auth.security import DUMMY_PASSWORD_HASH, create_access_token, verify_password
from app.config import get_jwt_algorithm, get_jwt_secret_key
from app.main import app


client = TestClient(app)


def create_user(
    session: Session,
    email: str = "admin@example.com",
    role: UserRole = UserRole.ADMIN,
    is_active: bool = True,
):
    user = UserRepository(session).create(
        UserCreate(email=email, password="strong-password", role=role)
    )
    if not is_active:
        user.is_active = False
        session.commit()
        session.refresh(user)
    return user


def headers_for(user) -> dict[str, str]:
    token = create_access_token(user.id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me(db_session: Session) -> None:
    user = create_user(db_session, email="Admin@Example.com")
    assert user.email == "admin@example.com"
    assert user.password_hash != "strong-password"
    assert verify_password("strong-password", user.password_hash)

    response = client.post(
        "/auth/login",
        data={"username": "ADMIN@example.com", "password": "strong-password"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"
    assert "password_hash" not in me.json()


def test_invalid_email_and_password_use_same_response_and_verification_path(
    db_session: Session, monkeypatch
) -> None:
    user = create_user(db_session)
    verified_hashes: list[str] = []
    real_verify_password = auth_router.verify_password

    def recording_verify_password(password: str, encoded_hash: str) -> bool:
        verified_hashes.append(encoded_hash)
        return real_verify_password(password, encoded_hash)

    monkeypatch.setattr(auth_router, "verify_password", recording_verify_password)

    invalid_email = client.post(
        "/auth/login",
        data={"username": "missing@example.com", "password": "strong-password"},
    )
    invalid_password = client.post(
        "/auth/login",
        data={"username": user.email, "password": "wrong-password"},
    )

    assert invalid_email.status_code == invalid_password.status_code == 401
    assert invalid_email.json() == invalid_password.json() == {
        "detail": "Incorrect email or password"
    }
    assert invalid_email.headers["www-authenticate"] == "Bearer"
    assert invalid_password.headers["www-authenticate"] == "Bearer"
    assert verified_hashes == [DUMMY_PASSWORD_HASH, user.password_hash]


def test_inactive_user_cannot_login_or_use_existing_token(db_session: Session) -> None:
    user = create_user(db_session)
    token = create_access_token(user.id, user.role.value)
    user.is_active = False
    db_session.commit()

    assert client.post(
        "/auth/login",
        data={"username": user.email, "password": "strong-password"},
    ).status_code == 401
    assert client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401


def test_missing_tampered_and_expired_tokens_are_rejected(db_session: Session) -> None:
    create_user(db_session)
    assert client.get("/auth/me").status_code == 401
    assert client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid"}
    ).status_code == 401

    expired = jwt.encode(
        {
            "sub": "1",
            "role": "admin",
            "iat": datetime.now(timezone.utc) - timedelta(minutes=2),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        get_jwt_secret_key(),
        algorithm=get_jwt_algorithm(),
    )
    assert client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    ).status_code == 401


def test_health_remains_public() -> None:
    assert client.get("/health").status_code == 200
