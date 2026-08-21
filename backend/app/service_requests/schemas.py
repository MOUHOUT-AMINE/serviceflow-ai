from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .models import ServiceRequestPriority, ServiceRequestStatus


Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ServiceRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title
    description: Description
    customer_id: int = Field(gt=0)
    status: ServiceRequestStatus = ServiceRequestStatus.OPEN
    priority: ServiceRequestPriority = ServiceRequestPriority.MEDIUM


class ServiceRequestUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title = Field(default=None)  # type: ignore[assignment]
    description: Description = Field(default=None)  # type: ignore[assignment]
    status: ServiceRequestStatus = Field(default=None)  # type: ignore[assignment]
    priority: ServiceRequestPriority = Field(default=None)  # type: ignore[assignment]


class ServiceRequestAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assigned_agent_id: int | None


class ServiceRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: ServiceRequestStatus
    priority: ServiceRequestPriority
    customer_id: int
    assigned_agent_id: int | None
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
