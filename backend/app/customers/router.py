from fastapi import APIRouter, HTTPException, Response, status

from .repository import customer_repository
from .schemas import Customer, CustomerCreate, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_customer_or_404(customer_id: int) -> Customer:
    customer = customer_repository.get(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=Customer, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate) -> Customer:
    return customer_repository.create(data)


@router.get("", response_model=list[Customer])
def list_customers() -> list[Customer]:
    return customer_repository.list()


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int) -> Customer:
    return _get_customer_or_404(customer_id)


@router.patch("/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, data: CustomerUpdate) -> Customer:
    customer = customer_repository.update(customer_id, data)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int) -> Response:
    if not customer_repository.delete(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
