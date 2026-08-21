from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import AdminUser, AgentUser
from app.database import get_db

from .repository import DashboardRepository
from .schemas import AgentWorkSummary, DashboardOverview


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_repository(
    db: Annotated[Session, Depends(get_db)],
) -> DashboardRepository:
    return DashboardRepository(db)


@router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    _: AdminUser,
    repository: Annotated[DashboardRepository, Depends(get_dashboard_repository)],
) -> DashboardOverview:
    return repository.overview()


@router.get("/my-work", response_model=AgentWorkSummary)
def dashboard_my_work(
    agent: AgentUser,
    repository: Annotated[DashboardRepository, Depends(get_dashboard_repository)],
) -> AgentWorkSummary:
    return repository.my_work(agent.id)
