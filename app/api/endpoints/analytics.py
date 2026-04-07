from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_analyst_or_admin
from app.models.user import User as UserModel
from app.schemas.analytics import AnalyticsReport
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get(
    "/report",
    response_model=AnalyticsReport,
    summary="Get financial analytics report",
    description=(
        "Returns a comprehensive financial analytics report including totals, "
        "category breakdowns, and monthly trends. "
        "Cached for 5 minutes per user. **Requires Analyst or Admin role.**"
    ),
)
def get_analytics_report(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_analyst_or_admin),
) -> Any:
    return AnalyticsService.generate_report(db, owner_id=current_user.id)
