from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import UserModel, UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate, UserUpdate
from app.auth.security import create_access_token
from app.customers.models import CustomerModel
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreate
from app.main import app
from app.service_requests.models import ServiceRequestModel


client = TestClient(app)


def create_user(
    session: Session, email: str, role: UserRole = UserRole.AGENT
) -> UserModel:
    return UserRepository(session).create(
        UserCreate(email=email, password="strong-password", role=role)
    )


def create_customer(session: Session, number: int) -> CustomerModel:
    return CustomerRepository(session).create(
        CustomerCreate(
            name=f"Customer {number}", email=f"customer{number}@example.com"
        )
    )


def create_request(
    session: Session,
    *,
    creator_id: int,
    customer_id: int,
    status: str,
    priority: str,
    assignee_id: int | None = None,
) -> ServiceRequestModel:
    request = ServiceRequestModel(
        title=f"{status} {priority}",
        description="Dashboard test request",
        status=status,
        priority=priority,
        customer_id=customer_id,
        created_by_user_id=creator_id,
        assigned_agent_id=assignee_id,
    )
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


def headers_for(user: UserModel) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"
    }


def test_admin_overview_aggregates_all_dashboard_statistics(
    db_session: Session,
) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    first_agent = create_user(db_session, "first@example.com")
    second_agent = create_user(db_session, "second@example.com")
    first_customer = create_customer(db_session, 1)
    create_customer(db_session, 2)

    create_request(
        db_session,
        creator_id=admin.id,
        customer_id=first_customer.id,
        status="open",
        priority="high",
        assignee_id=first_agent.id,
    )
    create_request(
        db_session,
        creator_id=admin.id,
        customer_id=first_customer.id,
        status="in_progress",
        priority="medium",
        assignee_id=first_agent.id,
    )
    create_request(
        db_session,
        creator_id=admin.id,
        customer_id=first_customer.id,
        status="resolved",
        priority="low",
        assignee_id=second_agent.id,
    )
    create_request(
        db_session,
        creator_id=admin.id,
        customer_id=first_customer.id,
        status="closed",
        priority="medium",
    )

    response = client.get("/dashboard/overview", headers=headers_for(admin))

    assert response.status_code == 200
    assert response.json() == {
        "total_service_requests": 4,
        "service_requests_by_status": {
            "open": 1,
            "in_progress": 1,
            "resolved": 1,
            "closed": 1,
        },
        "service_requests_by_priority": {"low": 1, "medium": 2, "high": 1},
        "service_requests_by_assignee": [
            {
                "agent_id": first_agent.id,
                "email": first_agent.email,
                "is_active": True,
                "count": 2,
            },
            {
                "agent_id": second_agent.id,
                "email": second_agent.email,
                "is_active": True,
                "count": 1,
            },
        ],
        "unassigned_service_requests": 1,
        "total_customers": 2,
    }


def test_empty_overview_includes_zero_enum_values(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)

    response = client.get("/dashboard/overview", headers=headers_for(admin))

    assert response.status_code == 200
    assert response.json() == {
        "total_service_requests": 0,
        "service_requests_by_status": {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "closed": 0,
        },
        "service_requests_by_priority": {"low": 0, "medium": 0, "high": 0},
        "service_requests_by_assignee": [],
        "unassigned_service_requests": 0,
        "total_customers": 0,
    }


def test_my_work_counts_only_requests_assigned_to_authenticated_agent(
    db_session: Session,
) -> None:
    agent = create_user(db_session, "agent@example.com")
    other_agent = create_user(db_session, "other@example.com")
    customer = create_customer(db_session, 1)
    create_request(
        db_session,
        creator_id=other_agent.id,
        customer_id=customer.id,
        status="open",
        priority="high",
        assignee_id=agent.id,
    )
    create_request(
        db_session,
        creator_id=agent.id,
        customer_id=customer.id,
        status="resolved",
        priority="low",
        assignee_id=agent.id,
    )
    create_request(
        db_session,
        creator_id=agent.id,
        customer_id=customer.id,
        status="closed",
        priority="medium",
        assignee_id=other_agent.id,
    )
    create_request(
        db_session,
        creator_id=agent.id,
        customer_id=customer.id,
        status="in_progress",
        priority="medium",
    )

    response = client.get("/dashboard/my-work", headers=headers_for(agent))

    assert response.status_code == 200
    assert response.json() == {
        "total_assigned_service_requests": 2,
        "service_requests_by_status": {
            "open": 1,
            "in_progress": 0,
            "resolved": 1,
            "closed": 0,
        },
        "service_requests_by_priority": {"low": 1, "medium": 0, "high": 1},
    }


def test_overview_retains_deactivated_and_role_changed_assignees(
    db_session: Session,
) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    deactivated = create_user(db_session, "deactivated@example.com")
    role_changed = create_user(db_session, "role-changed@example.com")
    customer = create_customer(db_session, 1)
    for assignee in (deactivated, role_changed):
        create_request(
            db_session,
            creator_id=admin.id,
            customer_id=customer.id,
            status="open",
            priority="medium",
            assignee_id=assignee.id,
        )

    UserRepository(db_session).update(
        deactivated.id, UserUpdate(is_active=False)
    )
    UserRepository(db_session).update(
        role_changed.id, UserUpdate(role=UserRole.ADMIN)
    )

    response = client.get("/dashboard/overview", headers=headers_for(admin))

    assert response.status_code == 200
    assert response.json()["service_requests_by_assignee"] == [
        {
            "agent_id": deactivated.id,
            "email": deactivated.email,
            "is_active": False,
            "count": 1,
        },
        {
            "agent_id": role_changed.id,
            "email": role_changed.email,
            "is_active": True,
            "count": 1,
        },
    ]


def test_dashboard_authorization(db_session: Session) -> None:
    admin = create_user(db_session, "admin@example.com", UserRole.ADMIN)
    agent = create_user(db_session, "agent@example.com")

    assert client.get("/dashboard/overview").status_code == 401
    assert client.get("/dashboard/my-work").status_code == 401
    assert client.get(
        "/dashboard/overview", headers=headers_for(agent)
    ).status_code == 403
    assert client.get(
        "/dashboard/my-work", headers=headers_for(admin)
    ).status_code == 403
    assert client.get(
        "/dashboard/overview", headers=headers_for(admin)
    ).status_code == 200
    assert client.get(
        "/dashboard/my-work", headers=headers_for(agent)
    ).status_code == 200
