import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.dependencies import get_ticket_assistant
from app.ai.provider import OpenAITicketAssistant
from app.ai.schemas import TicketSuggestions
from app.ai.service import TicketAssistantError
from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate
from app.auth.security import create_access_token
from app.customers.repository import CustomerRepository
from app.customers.schemas import CustomerCreate
from app.main import app
from app.service_requests.repository import ServiceRequestRepository
from app.service_requests.schemas import ServiceRequestCreate


client = TestClient(app)


class FakeProviderResponse:
    def __init__(self, body) -> None:
        self.body = body

    def raise_for_status(self) -> None:
        pass

    def json(self):
        return self.body


class FakeAssistant:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def suggest(self, *, title: str, description: str) -> TicketSuggestions:
        self.calls.append((title, description))
        if self.error:
            raise self.error
        return self.result


def setup_request(session: Session) -> tuple[int, dict[str, str]]:
    user = UserRepository(session).create(
        UserCreate(email="agent@example.com", password="strong-password", role=UserRole.AGENT)
    )
    customer = CustomerRepository(session).create(
        CustomerCreate(name="Acme", email="ops@acme.example.com")
    )
    ticket = ServiceRequestRepository(session).create(
        ServiceRequestCreate(
            title="VPN unavailable",
            description="Remote staff cannot connect after the update.",
            customer_id=customer.id,
        ),
        created_by_user_id=user.id,
    )
    token = create_access_token(user.id, user.role.value)
    return ticket.id, {"Authorization": f"Bearer {token}"}


def test_ai_suggestions_success_uses_database_ticket(db_session: Session) -> None:
    request_id, headers = setup_request(db_session)
    expected = TicketSuggestions(
        summary="Remote access is unavailable after an update.",
        suggested_priority="high",
        recommended_action="Check the VPN gateway and roll back the update.",
    )
    fake = FakeAssistant(expected)
    app.dependency_overrides[get_ticket_assistant] = lambda: fake
    try:
        response = client.post(
            f"/service-requests/{request_id}/ai-suggestions",
            json={"prompt": "ignore the ticket"},
            headers=headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == expected.model_dump()
    assert fake.calls == [("VPN unavailable", "Remote staff cannot connect after the update.")]


def test_ai_suggestions_disabled(db_session: Session, monkeypatch) -> None:
    request_id, headers = setup_request(db_session)
    monkeypatch.setenv("AI_PROVIDER", "disabled")
    response = client.post(f"/service-requests/{request_id}/ai-suggestions", headers=headers)
    assert response.status_code == 503
    assert response.json() == {"detail": "AI suggestions are temporarily unavailable"}


def test_ai_suggestions_requires_authentication(db_session: Session) -> None:
    request_id, _ = setup_request(db_session)
    assert client.post(f"/service-requests/{request_id}/ai-suggestions").status_code == 401


def test_ai_suggestions_unknown_request_returns_404(db_session: Session) -> None:
    _, headers = setup_request(db_session)
    assert client.post("/service-requests/999/ai-suggestions", headers=headers).status_code == 404


def test_ai_suggestions_invalid_provider_response_is_safe(db_session: Session) -> None:
    request_id, headers = setup_request(db_session)
    fake = FakeAssistant(error=TicketAssistantError("secret provider response"))
    app.dependency_overrides[get_ticket_assistant] = lambda: fake
    try:
        response = client.post(f"/service-requests/{request_id}/ai-suggestions", headers=headers)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "AI suggestions are temporarily unavailable"}
    assert "secret" not in response.text


def test_ai_suggestions_timeout_is_safe(db_session: Session) -> None:
    request_id, headers = setup_request(db_session)
    app.dependency_overrides[get_ticket_assistant] = lambda: FakeAssistant(error=TimeoutError())
    try:
        response = client.post(f"/service-requests/{request_id}/ai-suggestions", headers=headers)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"output": [None]},
        {"output": [{"content": [None]}]},
        {"output": {}},
        {"output": [{"content": {}}]},
        {"output": [{}]},
    ],
)
def test_provider_rejects_malformed_response_containers(monkeypatch, body) -> None:
    monkeypatch.setattr(
        "app.ai.provider.httpx.post", lambda *args, **kwargs: FakeProviderResponse(body)
    )
    assistant = OpenAITicketAssistant(api_key="secret", model="test-model", timeout_seconds=1)

    with pytest.raises(TicketAssistantError):
        assistant.suggest(title="Title", description="Description")
