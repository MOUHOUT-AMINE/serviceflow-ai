from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.customers.repository import CustomerRepository, customer_repository
from app.customers.schemas import CustomerCreate, CustomerUpdate
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_customer_repository() -> None:
    customer_repository.clear()


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


def test_concurrent_creates_keep_unique_ids_and_all_customers() -> None:
    repository = CustomerRepository()

    def create_customer(number: int) -> int:
        customer = repository.create(
            CustomerCreate(name=f"Customer {number}", email=f"user{number}@example.com")
        )
        return customer.id

    with ThreadPoolExecutor(max_workers=10) as executor:
        ids = list(executor.map(create_customer, range(100)))

    assert len(ids) == len(set(ids)) == 100
    assert len(repository.list()) == 100


def test_update_returns_404_when_customer_is_deleted_before_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client.post("/customers", json={"name": "Ada", "email": "ada@example.com"})

    def delete_before_update(
        customer_id: int, data: CustomerUpdate
    ) -> None:
        customer_repository.delete(customer_id)
        return None

    monkeypatch.setattr(customer_repository, "update", delete_before_update)

    response = client.patch("/customers/1", json={"name": "Ada Byron"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}
