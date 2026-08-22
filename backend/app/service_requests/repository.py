from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import ServiceRequestModel, ServiceRequestPriority, ServiceRequestStatus
from .schemas import ServiceRequestCreate, ServiceRequestUpdate


class ServiceRequestRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, data: ServiceRequestCreate, created_by_user_id: int
    ) -> ServiceRequestModel:
        request = ServiceRequestModel(
            **data.model_dump(), created_by_user_id=created_by_user_id
        )
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request

    def list(
        self,
        customer_id: int | None = None,
        assigned_agent_id: int | None = None,
        status: ServiceRequestStatus | None = None,
        priority: ServiceRequestPriority | None = None,
    ) -> list[ServiceRequestModel]:
        statement = select(ServiceRequestModel).options(
            selectinload(ServiceRequestModel.assigned_agent)
        )
        if customer_id is not None:
            statement = statement.where(ServiceRequestModel.customer_id == customer_id)
        if assigned_agent_id is not None:
            statement = statement.where(
                ServiceRequestModel.assigned_agent_id == assigned_agent_id
            )
        if status is not None:
            statement = statement.where(ServiceRequestModel.status == status)
        if priority is not None:
            statement = statement.where(ServiceRequestModel.priority == priority)
        return list(self.session.scalars(statement.order_by(ServiceRequestModel.id)))

    def get(self, request_id: int) -> ServiceRequestModel | None:
        return self.session.get(ServiceRequestModel, request_id)

    def update(
        self, request_id: int, data: ServiceRequestUpdate
    ) -> ServiceRequestModel | None:
        request = self.get(request_id)
        if request is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(request, field, value)
        self.session.commit()
        self.session.refresh(request)
        return request

    def assign(
        self, request_id: int, assigned_agent_id: int | None
    ) -> ServiceRequestModel | None:
        request = self.get(request_id)
        if request is None:
            return None
        request.assigned_agent_id = assigned_agent_id
        self.session.commit()
        self.session.refresh(request)
        return request

    def delete(self, request_id: int) -> bool:
        request = self.get(request_id)
        if request is None:
            return False
        self.session.delete(request)
        self.session.commit()
        return True
