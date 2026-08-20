from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints


CustomerName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class CustomerCreate(BaseModel):
    name: CustomerName
    email: EmailStr


class CustomerUpdate(BaseModel):
    name: CustomerName = Field(default=None)  # type: ignore[assignment]
    email: EmailStr = Field(default=None)  # type: ignore[assignment]


class Customer(CustomerCreate):
    id: int
