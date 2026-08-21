from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.customers.router import router as customers_router
from app.users.router import router as users_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(customers_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
