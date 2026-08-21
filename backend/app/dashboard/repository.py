from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.models import UserModel
from app.customers.models import CustomerModel
from app.service_requests.models import (
    ServiceRequestModel,
    ServiceRequestPriority,
    ServiceRequestStatus,
)

from .schemas import AgentWorkSummary, AssigneeRequestCount, DashboardOverview


class DashboardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def overview(self) -> DashboardOverview:
        status_counts = self._status_counts()
        priority_counts = self._priority_counts()
        assignees, unassigned_count = self._assignee_counts()
        customer_count = self.session.scalar(select(func.count(CustomerModel.id))) or 0

        return DashboardOverview(
            total_service_requests=sum(status_counts.values()),
            service_requests_by_status=status_counts,
            service_requests_by_priority=priority_counts,
            service_requests_by_assignee=assignees,
            unassigned_service_requests=unassigned_count,
            total_customers=customer_count,
        )

    def my_work(self, agent_id: int) -> AgentWorkSummary:
        status_counts = self._status_counts(agent_id=agent_id)
        return AgentWorkSummary(
            total_assigned_service_requests=sum(status_counts.values()),
            service_requests_by_status=status_counts,
            service_requests_by_priority=self._priority_counts(agent_id=agent_id),
        )

    def _status_counts(
        self, agent_id: int | None = None
    ) -> dict[ServiceRequestStatus, int]:
        statement = select(
            ServiceRequestModel.status, func.count(ServiceRequestModel.id)
        ).group_by(ServiceRequestModel.status)
        if agent_id is not None:
            statement = statement.where(
                ServiceRequestModel.assigned_agent_id == agent_id
            )

        counts = {status: 0 for status in ServiceRequestStatus}
        for request_status, count in self.session.execute(statement):
            counts[request_status] = count
        return counts

    def _priority_counts(
        self, agent_id: int | None = None
    ) -> dict[ServiceRequestPriority, int]:
        statement = select(
            ServiceRequestModel.priority, func.count(ServiceRequestModel.id)
        ).group_by(ServiceRequestModel.priority)
        if agent_id is not None:
            statement = statement.where(
                ServiceRequestModel.assigned_agent_id == agent_id
            )

        counts = {priority: 0 for priority in ServiceRequestPriority}
        for priority, count in self.session.execute(statement):
            counts[priority] = count
        return counts

    def _assignee_counts(self) -> tuple[list[AssigneeRequestCount], int]:
        count = func.count(ServiceRequestModel.id).label("request_count")
        statement = (
            select(
                ServiceRequestModel.assigned_agent_id,
                UserModel.email,
                UserModel.is_active,
                count,
            )
            .outerjoin(UserModel, UserModel.id == ServiceRequestModel.assigned_agent_id)
            .group_by(
                ServiceRequestModel.assigned_agent_id,
                UserModel.email,
                UserModel.is_active,
            )
            .order_by(count.desc(), ServiceRequestModel.assigned_agent_id.asc())
        )

        assignees: list[AssigneeRequestCount] = []
        unassigned_count = 0
        rows = self.session.execute(statement)
        for agent_id, email, is_active, request_count in rows:
            if agent_id is None:
                unassigned_count = request_count
                continue
            assignees.append(
                AssigneeRequestCount(
                    agent_id=agent_id,
                    email=email,
                    is_active=is_active,
                    count=request_count,
                )
            )
        return assignees, unassigned_count
