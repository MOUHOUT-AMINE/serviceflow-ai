from pydantic import BaseModel

from app.service_requests.models import ServiceRequestPriority, ServiceRequestStatus


class AssigneeRequestCount(BaseModel):
    agent_id: int
    email: str
    is_active: bool
    count: int


class DashboardOverview(BaseModel):
    total_service_requests: int
    service_requests_by_status: dict[ServiceRequestStatus, int]
    service_requests_by_priority: dict[ServiceRequestPriority, int]
    service_requests_by_assignee: list[AssigneeRequestCount]
    unassigned_service_requests: int
    total_customers: int


class AgentWorkSummary(BaseModel):
    total_assigned_service_requests: int
    service_requests_by_status: dict[ServiceRequestStatus, int]
    service_requests_by_priority: dict[ServiceRequestPriority, int]
