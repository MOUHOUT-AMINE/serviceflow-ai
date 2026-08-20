from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CustomerModel
from .schemas import CustomerCreate, CustomerUpdate


class CustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: CustomerCreate) -> CustomerModel:
        customer = CustomerModel(**data.model_dump())
        self.session.add(customer)
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def list(self) -> list[CustomerModel]:
        statement = select(CustomerModel).order_by(CustomerModel.id)
        return list(self.session.scalars(statement))

    def get(self, customer_id: int) -> CustomerModel | None:
        return self.session.get(CustomerModel, customer_id)

    def update(
        self, customer_id: int, data: CustomerUpdate
    ) -> CustomerModel | None:
        customer = self.get(customer_id)
        if customer is None:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(customer, field, value)

        self.session.commit()
        self.session.refresh(customer)
        return customer

    def delete(self, customer_id: int) -> bool:
        customer = self.get(customer_id)
        if customer is None:
            return False

        self.session.delete(customer)
        self.session.commit()
        return True
