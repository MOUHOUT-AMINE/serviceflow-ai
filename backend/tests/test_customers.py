from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate
from app.auth.security import create_access_token
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreate, CustomerUpdate
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticate_as_admin(db_session: Session) -> None:
    user = UserRepository(db_session).create(
        UserCreate(email="admin@example.com", password="strong-password", role=UserRole.ADMIN)
    )
    client.headers["Authorization"] = f"Bearer {create_access_token(user.id, user.role.value)}"


def test_customer_crud_flow() -> None:
    create_response = client.post(
        "/customers", json={"name": "Ada Lovelace", "email": "ada@example.com"}
    )
    assert create_response.status_code == 201
    assert create_response.json() == {
        "id": 1,
        "name": "Ada Lovelace",
        "email": "ada@example.com",
    }

    assert client.get("/customers").json() == [create_response.json()]
    assert client.get("/customers/1").json() == create_response.json()

    update_response = client.patch("/customers/1", json={"name": "Ada Byron"})
    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": 1,
        "name": "Ada Byron",
        "email": "ada@example.com",
    }

    assert client.delete("/customers/1").status_code == 204
    assert client.get("/customers/1").status_code == 404
    assert client.get("/customers").json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "email": "ada@example.com"},
        {"name": "   ", "email": "ada@example.com"},
        {"name": "Ada", "email": "not-an-email"},
        {"email": "ada@example.com"},
    ],
)
def test_create_customer_rejects_invalid_data(payload: dict[str, str]) -> None:
    assert client.post("/customers", json=payload).status_code == 422


def test_missing_customer_operations_return_404() -> None:
    assert client.get("/customers/999").status_code == 404
    assert client.patch("/customers/999", json={"name": "Nobody"}).status_code == 404
    assert client.delete("/customers/999").status_code == 404


def test_update_rejects_null_fields() -> None:
    client.post("/customers", json={"name": "Ada", "email": "ada@example.com"})

    assert client.patch("/customers/1", json={"name": None}).status_code == 422
    assert client.patch("/customers/1", json={"email": None}).status_code == 422


def test_concurrent_creates_keep_unique_ids_and_all_customers(
    session_factory: sessionmaker[Session], db_session: Session
) -> None:
    def create_customer(number: int) -> int:
        with session_factory() as session:
            repository = CustomerRepository(session)
            customer = repository.create(
                CustomerCreate(
                    name=f"Customer {number}", email=f"user{number}@example.com"
                )
            )
            return customer.id

    with ThreadPoolExecutor(max_workers=10) as executor:
        ids = list(executor.map(create_customer, range(100)))

    assert len(ids) == len(set(ids)) == 100
    assert len(CustomerRepository(db_session).list()) == 100


def test_update_returns_404_when_customer_is_deleted_before_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client.post("/customers", json={"name": "Ada", "email": "ada@example.com"})

    def delete_before_update(
        repository: CustomerRepository, customer_id: int, data: CustomerUpdate
    ) -> None:
        repository.delete(customer_id)
        return None

    monkeypatch.setattr(CustomerRepository, "update", delete_before_update)

    response = client.patch("/customers/1", json={"name": "Ada Byron"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}
