from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate
from app.auth.security import create_access_token
from app.main import app


client = TestClient(app)


def create_user(session: Session, email: str, role: UserRole):
    return UserRepository(session).create(
        UserCreate(email=email, password="strong-password", role=role)
    )


def headers_for(user) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"
    }


def test_admin_can_manage_users(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    headers = headers_for(admin)

    response = client.post(
        "/users",
        json={"email": "Agent@Example.com", "password": "agent-password", "role": "agent"},
        headers=headers,
    )
    assert response.status_code == 201
    agent = response.json()
    assert agent["email"] == "agent@example.com"
    assert agent["role"] == "agent"
    assert "password" not in agent and "password_hash" not in agent

    assert len(client.get("/users", headers=headers).json()) == 2
    assert client.get(f"/users/{agent['id']}", headers=headers).status_code == 200
    updated = client.patch(
        f"/users/{agent['id']}", json={"role": "admin", "is_active": False}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "admin"
    assert updated.json()["is_active"] is False


def test_duplicate_email_is_rejected_case_insensitively(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    response = client.post(
        "/users",
        json={"email": "ADMIN@example.com", "password": "strong-password", "role": "agent"},
        headers=headers_for(admin),
    )
    assert response.status_code == 409


def test_agent_cannot_manage_users(db_session: Session) -> None:
    agent = create_user(db_session, "agent@example.com", UserRole.AGENT)
    headers = headers_for(agent)
    assert client.get("/users", headers=headers).status_code == 403
    assert client.post(
        "/users",
        json={"email": "new@example.com", "password": "strong-password", "role": "agent"},
        headers=headers,
    ).status_code == 403


def test_missing_users_return_404(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    headers = headers_for(admin)
    assert client.get("/users/999", headers=headers).status_code == 404
    assert client.patch("/users/999", json={"is_active": False}, headers=headers).status_code == 404


def test_agent_customer_permissions_and_admin_delete(db_session: Session) -> None:
    agent = create_user(db_session, "agent@example.com", UserRole.AGENT)
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    agent_headers = headers_for(agent)

    created = client.post(
        "/customers",
        json={"name": "Ada", "email": "ada@example.com"},
        headers=agent_headers,
    )
    assert created.status_code == 201
    assert client.get("/customers", headers=agent_headers).status_code == 200
    assert client.get("/customers/1", headers=agent_headers).status_code == 200
    assert client.patch(
        "/customers/1", json={"name": "Ada Byron"}, headers=agent_headers
    ).status_code == 200
    assert client.delete("/customers/1", headers=agent_headers).status_code == 403
    assert client.delete("/customers/1", headers=headers_for(admin)).status_code == 204


def test_customer_routes_require_authentication() -> None:
    assert client.get("/customers").status_code == 401
