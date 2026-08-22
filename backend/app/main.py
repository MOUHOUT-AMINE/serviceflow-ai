from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.config import get_cors_origins
from app.customers.router import router as customers_router
from app.dashboard.router import router as dashboard_router
from app.service_requests.router import router as service_requests_router
from app.users.router import router as users_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(customers_router)
app.include_router(service_requests_router)
app.include_router(dashboard_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
