from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db

from .repository import CustomerRepository
from .schemas import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_repository(db: Session = Depends(get_db)) -> CustomerRepository:
    return CustomerRepository(db)


def _get_customer_or_404(
    customer_id: int, repository: CustomerRepository
) -> Customer:
    customer = repository.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    repository: CustomerRepository = Depends(get_customer_repository),
) -> Customer:
    return repository.create(data)


@router.get("", response_model=list[Customer])
def list_customers(
    repository: CustomerRepository = Depends(get_customer_repository),
) -> list[Customer]:
    return repository.list()


@router.get("/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: int,
    repository: CustomerRepository = Depends(get_customer_repository),
) -> Customer:
    return _get_customer_or_404(customer_id, repository)


@router.patch("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    repository: CustomerRepository = Depends(get_customer_repository),
) -> Customer:
    customer = repository.update(customer_id, data)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: int,
    repository: CustomerRepository = Depends(get_customer_repository),
) -> Response:
    if not repository.delete(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
