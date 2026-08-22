from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import NO_VALUE

from app.auth.models import UserModel, UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate
from app.auth.security import create_access_token
from app.customers.models import CustomerModel
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreate
from app.main import app
from app.service_requests.models import ServiceRequestModel
from app.service_requests.repository import ServiceRequestRepository


client = TestClient(app)


def create_user(
    session: Session,
    email: str,
    role: UserRole = UserRole.AGENT,
    active: bool = True,
) -> UserModel:
    user = UserRepository(session).create(
        UserCreate(email=email, password="strong-password", role=role)
    )
    if not active:
        user.is_active = False
        session.commit()
        session.refresh(user)
    return user


def headers_for(user: UserModel) -> dict[str, str]:
    token = create_access_token(user.id, user.role.value)
    return {"Authorization": f"Bearer {token}"}


def create_customer(session: Session, number: int = 1) -> CustomerModel:
    return CustomerRepository(session).create(
        CustomerCreate(name=f"Customer {number}", email=f"customer{number}@example.com")
    )


def request_payload(customer_id: int, **overrides) -> dict:
    payload = {
        "title": "Printer unavailable",
        "description": "The office printer cannot be reached.",
        "customer_id": customer_id,
    }
    payload.update(overrides)
    return payload


def test_crud_defaults_creator_and_updated_at(db_session: Session) -> None:
    agent = create_user(db_session, "agent@example.com")
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    customer = create_customer(db_session)

    created_response = client.post(
        "/service-requests",
        json=request_payload(customer.id, created_by_user_id=admin.id),
        headers=headers_for(agent),
    )
    assert created_response.status_code == 422

    created_response = client.post(
        "/service-requests", json=request_payload(customer.id), headers=headers_for(agent)
    )
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["status"] == "open"
    assert created["priority"] == "medium"
    assert created["created_by_user_id"] == agent.id
    assert created["assigned_agent_id"] is None
    assert client.get(
        f"/service-requests/{created['id']}", headers=headers_for(agent)
    ).json() == created
    assert client.get("/service-requests", headers=headers_for(agent)).json() == [created]

    old_updated_at = datetime.fromisoformat(created["updated_at"])
    updated_response = client.patch(
        f"/service-requests/{created['id']}",
        json={"title": "Printer restored", "status": "resolved", "priority": "low"},
        headers=headers_for(agent),
    )
    assert updated_response.status_code == 200
    updated = updated_response.json()
    assert updated["title"] == "Printer restored"
    assert updated["status"] == "resolved"
    assert updated["priority"] == "low"
    assert datetime.fromisoformat(updated["updated_at"]) > old_updated_at

    assert client.delete(
        f"/service-requests/{created['id']}", headers=headers_for(admin)
    ).status_code == 204
    assert client.get(
        f"/service-requests/{created['id']}", headers=headers_for(agent)
    ).status_code == 404


@pytest.mark.parametrize("status_value", ["open", "in_progress", "resolved", "closed"])
def test_all_status_values(status_value: str, db_session: Session) -> None:
    user = create_user(db_session, f"{status_value}@example.com")
    customer = create_customer(db_session)
    response = client.post(
        "/service-requests",
        json=request_payload(customer.id, status=status_value),
        headers=headers_for(user),
    )
    assert response.status_code == 201
    assert response.json()["status"] == status_value


@pytest.mark.parametrize("priority", ["low", "medium", "high"])
def test_all_priority_values(priority: str, db_session: Session) -> None:
    user = create_user(db_session, f"{priority}@example.com")
    customer = create_customer(db_session)
    response = client.post(
        "/service-requests",
        json=request_payload(customer.id, priority=priority),
        headers=headers_for(user),
    )
    assert response.status_code == 201
    assert response.json()["priority"] == priority


@pytest.mark.parametrize(
    "changes",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"description": ""},
        {"description": "   "},
        {"status": "waiting"},
        {"priority": "urgent"},
    ],
)
def test_invalid_create_values(changes: dict, db_session: Session) -> None:
    user = create_user(db_session, "agent@example.com")
    customer = create_customer(db_session)
    assert client.post(
        "/service-requests",
        json=request_payload(customer.id, **changes),
        headers=headers_for(user),
    ).status_code == 422


def test_missing_resources(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    headers = headers_for(admin)
    assert client.post(
        "/service-requests", json=request_payload(999), headers=headers
    ).status_code == 404
    assert client.get("/service-requests/999", headers=headers).status_code == 404
    assert client.patch(
        "/service-requests/999", json={"status": "closed"}, headers=headers
    ).status_code == 404
    assert client.delete("/service-requests/999", headers=headers).status_code == 404
    assert client.patch(
        "/service-requests/999/assignment",
        json={"assigned_agent_id": None},
        headers=headers,
    ).status_code == 404


def test_assignment_reassignment_and_unassignment(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    first = create_user(db_session, "first@example.com")
    second = create_user(db_session, "second@example.com")
    customer = create_customer(db_session)
    headers = headers_for(admin)
    request_id = client.post(
        "/service-requests", json=request_payload(customer.id), headers=headers
    ).json()["id"]

    for agent_id in (first.id, second.id, None):
        response = client.patch(
            f"/service-requests/{request_id}/assignment",
            json={"assigned_agent_id": agent_id},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["assigned_agent_id"] == agent_id
        assert response.json()["assigned_agent_email"] == (
            None if agent_id is None else db_session.get(UserModel, agent_id).email
        )

    assert client.patch(
        f"/service-requests/{request_id}",
        json={"assigned_agent_id": first.id},
        headers=headers,
    ).status_code == 422


def test_agent_receives_safe_assignee_identity_without_users_access(
    db_session: Session,
) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    assignee = create_user(db_session, "assigned@example.com")
    viewer = create_user(db_session, "viewer@example.com")
    customer = create_customer(db_session)
    request_id = client.post(
        "/service-requests",
        json=request_payload(customer.id),
        headers=headers_for(admin),
    ).json()["id"]
    client.patch(
        f"/service-requests/{request_id}/assignment",
        json={"assigned_agent_id": assignee.id},
        headers=headers_for(admin),
    )

    response = client.get(
        f"/service-requests/{request_id}", headers=headers_for(viewer)
    )

    assert response.status_code == 200
    assert response.json()["assigned_agent_id"] == assignee.id
    assert response.json()["assigned_agent_email"] == "assigned@example.com"
    assert client.get("/users", headers=headers_for(viewer)).status_code == 403


def test_list_eager_loads_assigned_agents(db_session: Session) -> None:
    creator = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    assignee = create_user(db_session, "assigned@example.com")
    customer = create_customer(db_session)
    db_session.add_all(
        [
            ServiceRequestModel(
                title=f"Request {number}",
                description="Description",
                customer_id=customer.id,
                created_by_user_id=creator.id,
                assigned_agent_id=assignee.id,
            )
            for number in range(2)
        ]
    )
    db_session.commit()
    db_session.expire_all()

    requests = ServiceRequestRepository(db_session).list()

    assert len(requests) == 2
    assert all(
        inspect(request).attrs.assigned_agent.loaded_value is not NO_VALUE
        for request in requests
    )


def test_assignment_rejects_invalid_targets(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    inactive = create_user(db_session, "inactive@example.com", active=False)
    customer = create_customer(db_session)
    headers = headers_for(admin)
    request_id = client.post(
        "/service-requests", json=request_payload(customer.id), headers=headers
    ).json()["id"]

    for user_id, expected in ((999, 404), (admin.id, 422), (inactive.id, 422)):
        assert client.patch(
            f"/service-requests/{request_id}/assignment",
            json={"assigned_agent_id": user_id},
            headers=headers,
        ).status_code == expected


def test_permissions_and_authentication(db_session: Session) -> None:
    agent = create_user(db_session, "agent@example.com")
    customer = create_customer(db_session)
    headers = headers_for(agent)
    created = client.post(
        "/service-requests", json=request_payload(customer.id), headers=headers
    )
    assert created.status_code == 201
    request_id = created.json()["id"]
    assert client.get("/service-requests", headers=headers).status_code == 200
    assert client.get(f"/service-requests/{request_id}", headers=headers).status_code == 200
    assert client.patch(
        f"/service-requests/{request_id}", json={"status": "in_progress"}, headers=headers
    ).status_code == 200
    assert client.patch(
        f"/service-requests/{request_id}/assignment",
        json={"assigned_agent_id": agent.id},
        headers=headers,
    ).status_code == 403
    assert client.delete(f"/service-requests/{request_id}", headers=headers).status_code == 403

    assert client.get("/service-requests").status_code == 401
    assert client.post(
        "/service-requests", json=request_payload(customer.id)
    ).status_code == 401
    assert client.get(f"/service-requests/{request_id}").status_code == 401
    assert client.patch(
        f"/service-requests/{request_id}", json={"status": "closed"}
    ).status_code == 401
    assert client.patch(
        f"/service-requests/{request_id}/assignment", json={"assigned_agent_id": None}
    ).status_code == 401
    assert client.delete(f"/service-requests/{request_id}").status_code == 401


def test_filters(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    agent = create_user(db_session, "agent@example.com")
    first_customer = create_customer(db_session, 1)
    second_customer = create_customer(db_session, 2)
    headers = headers_for(admin)
    first = client.post(
        "/service-requests",
        json=request_payload(first_customer.id, status="open", priority="high"),
        headers=headers,
    ).json()
    second = client.post(
        "/service-requests",
        json=request_payload(second_customer.id, status="closed", priority="low"),
        headers=headers,
    ).json()
    client.patch(
        f"/service-requests/{second['id']}/assignment",
        json={"assigned_agent_id": agent.id},
        headers=headers,
    )

    cases = {
        f"customer_id={first_customer.id}": first["id"],
        f"assigned_agent_id={agent.id}": second["id"],
        "status=closed": second["id"],
        "priority=high": first["id"],
    }
    for query, expected_id in cases.items():
        result = client.get(f"/service-requests?{query}", headers=headers).json()
        assert [item["id"] for item in result] == [expected_id]


def test_database_foreign_key_deletion_behavior(db_session: Session) -> None:
    creator = create_user(db_session, "creator@example.com")
    assignee = create_user(db_session, "assignee@example.com")
    customer = create_customer(db_session)
    request = ServiceRequestModel(
        title="Request",
        description="Description",
        customer_id=customer.id,
        created_by_user_id=creator.id,
        assigned_agent_id=assignee.id,
    )
    db_session.add(request)
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(delete(CustomerModel).where(CustomerModel.id == customer.id))
        db_session.commit()
    db_session.rollback()

    with pytest.raises(IntegrityError):
        db_session.execute(delete(UserModel).where(UserModel.id == creator.id))
        db_session.commit()
    db_session.rollback()

    db_session.execute(delete(UserModel).where(UserModel.id == assignee.id))
    db_session.commit()
    db_session.expire_all()
    assert db_session.scalar(
        select(ServiceRequestModel).where(ServiceRequestModel.id == request.id)
    ).assigned_agent_id is None
