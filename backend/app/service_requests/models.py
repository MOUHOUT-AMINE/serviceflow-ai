from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ServiceRequestStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ServiceRequestPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ServiceRequestModel(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ServiceRequestStatus] = mapped_column(
        SqlEnum(
            ServiceRequestStatus,
            name="service_request_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=ServiceRequestStatus.OPEN,
        server_default=ServiceRequestStatus.OPEN.value,
        index=True,
    )
    priority: Mapped[ServiceRequestPriority] = mapped_column(
        SqlEnum(
            ServiceRequestPriority,
            name="service_request_priority",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda priorities: [priority.value for priority in priorities],
        ),
        nullable=False,
        default=ServiceRequestPriority.MEDIUM,
        server_default=ServiceRequestPriority.MEDIUM.value,
        index=True,
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    customer: Mapped["CustomerModel"] = relationship(back_populates="service_requests")
    assigned_agent: Mapped["UserModel | None"] = relationship(
        back_populates="assigned_service_requests", foreign_keys=[assigned_agent_id]
    )
    created_by: Mapped["UserModel"] = relationship(
        back_populates="created_service_requests", foreign_keys=[created_by_user_id]
    )

    @property
    def assigned_agent_email(self) -> str | None:
        return self.assigned_agent.email if self.assigned_agent is not None else None


from app.auth.models import UserModel  # noqa: E402
from app.customers.models import CustomerModel  # noqa: E402
