from threading import RLock

from .schemas import Customer, CustomerCreate, CustomerUpdate


class CustomerRepository:
    """Small in-memory repository; replaceable with persistence later."""

    def __init__(self) -> None:
        self._customers: dict[int, Customer] = {}
        self._next_id = 1
        self._lock = RLock()

    def create(self, data: CustomerCreate) -> Customer:
        with self._lock:
            customer = Customer(id=self._next_id, **data.model_dump())
            self._customers[customer.id] = customer
            self._next_id += 1
            return customer

    def list(self) -> list[Customer]:
        with self._lock:
            return list(self._customers.values())

    def get(self, customer_id: int) -> Customer | None:
        with self._lock:
            return self._customers.get(customer_id)

    def update(self, customer_id: int, data: CustomerUpdate) -> Customer | None:
        with self._lock:
            customer = self._customers.get(customer_id)
            if customer is None:
                return None

            updated = customer.model_copy(update=data.model_dump(exclude_unset=True))
            self._customers[customer_id] = updated
            return updated

    def delete(self, customer_id: int) -> bool:
        with self._lock:
            return self._customers.pop(customer_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._customers.clear()
            self._next_id = 1


customer_repository = CustomerRepository()
