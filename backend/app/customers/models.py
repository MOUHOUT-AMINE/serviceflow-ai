from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CustomerModel(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    service_requests: Mapped[list["ServiceRequestModel"]] = relationship(
        back_populates="customer"
    )


from app.service_requests.models import ServiceRequestModel  # noqa: E402
