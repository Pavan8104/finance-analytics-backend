from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.analytics import AnalyticsReport
from app.services.analytics_service import AnalyticsService
from app.core.dependencies import get_current_active_analyst_or_admin
from app.models.user import User as UserModel

router = APIRouter()

@router.get("/report", response_model=AnalyticsReport)
def get_analytics_report(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_analyst_or_admin),
) -> Any:
    """
    Get financial analytics report.
    Access restricted to Admin or Analyst.
    """
    report = AnalyticsService.generate_report(db, owner_id=current_user.id)
    return report
