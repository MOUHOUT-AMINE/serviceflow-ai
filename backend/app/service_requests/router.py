from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminUser, AuthenticatedUser
from app.auth.models import UserRole
from app.auth.repository import UserRepository
from app.ai.dependencies import TicketAssistantDependency
from app.ai.schemas import TicketSuggestions
from app.ai.service import TicketAssistantError
from app.customers.repository import CustomerRepository
from app.database import get_db

from .models import ServiceRequestPriority, ServiceRequestStatus
from .repository import ServiceRequestRepository
from .schemas import (
    ServiceRequest,
    ServiceRequestAssignment,
    ServiceRequestCreate,
    ServiceRequestUpdate,
)


router = APIRouter(prefix="/service-requests", tags=["service-requests"])
AI_UNAVAILABLE_DETAIL = "AI suggestions are temporarily unavailable"


def get_service_request_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ServiceRequestRepository:
    return ServiceRequestRepository(db)


@router.post("", response_model=ServiceRequest, status_code=status.HTTP_201_CREATED)
def create_service_request(
    data: ServiceRequestCreate,
    user: AuthenticatedUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
) -> ServiceRequest:
    if CustomerRepository(repository.session).get(data.customer_id) is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return repository.create(data, created_by_user_id=user.id)


@router.get("", response_model=list[ServiceRequest])
def list_service_requests(
    _: AuthenticatedUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
    customer_id: int | None = None,
    assigned_agent_id: int | None = None,
    status_filter: Annotated[ServiceRequestStatus | None, Query(alias="status")] = None,
    priority: ServiceRequestPriority | None = None,
) -> list[ServiceRequest]:
    return repository.list(
        customer_id=customer_id,
        assigned_agent_id=assigned_agent_id,
        status=status_filter,
        priority=priority,
    )


@router.get("/{request_id}", response_model=ServiceRequest)
def get_service_request(
    request_id: int,
    _: AuthenticatedUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
) -> ServiceRequest:
    request = repository.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Service request not found")
    return request


@router.post("/{request_id}/ai-suggestions", response_model=TicketSuggestions)
def generate_ai_suggestions(
    request_id: int,
    _: AuthenticatedUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
    assistant: TicketAssistantDependency,
) -> TicketSuggestions:
    request = repository.get(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Service request not found")
    try:
        return assistant.suggest(title=request.title, description=request.description)
    except (TicketAssistantError, TimeoutError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AI_UNAVAILABLE_DETAIL,
        ) from None


@router.patch("/{request_id}", response_model=ServiceRequest)
def update_service_request(
    request_id: int,
    data: ServiceRequestUpdate,
    _: AuthenticatedUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
) -> ServiceRequest:
    request = repository.update(request_id, data)
    if request is None:
        raise HTTPException(status_code=404, detail="Service request not found")
    return request


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_request(
    request_id: int,
    _: AdminUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
) -> Response:
    if not repository.delete(request_id):
        raise HTTPException(status_code=404, detail="Service request not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{request_id}/assignment", response_model=ServiceRequest)
def assign_service_request(
    request_id: int,
    data: ServiceRequestAssignment,
    _: AdminUser,
    repository: Annotated[
        ServiceRequestRepository, Depends(get_service_request_repository)
    ],
) -> ServiceRequest:
    if repository.get(request_id) is None:
        raise HTTPException(status_code=404, detail="Service request not found")
    if data.assigned_agent_id is not None:
        user = UserRepository(repository.session).get(data.assigned_agent_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active or user.role != UserRole.AGENT:
            raise HTTPException(
                status_code=422, detail="Assignment target must be an active agent"
            )
    request = repository.assign(request_id, data.assigned_agent_id)
    assert request is not None
    return request
