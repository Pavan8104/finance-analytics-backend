"""
Admin-only system management endpoints.

Provides:
  - GET /admin/stats   — System-wide usage statistics
"""
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_admin
from app.models.user import User as UserModel, RoleEnum
from app.models.transaction import Transaction, TransactionType
from app.schemas.admin import SystemStats

router = APIRouter()


@router.get(
    "/stats",
    response_model=SystemStats,
    summary="System-wide statistics (admin only)",
    description="Returns aggregate platform metrics across all users. **Requires Admin role.**",
)
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_admin),
) -> Any:
    # User counts
    total_users = db.query(UserModel).count()
    active_users = db.query(UserModel).filter(UserModel.is_active == True).count()

    # Role distribution
    role_counts = (
        db.query(UserModel.role, func.count(UserModel.id))
        .group_by(UserModel.role)
        .all()
    )
    users_by_role = {role.value: count for role, count in role_counts}

    # Transaction totals
    total_transactions = db.query(Transaction).count()

    income_total = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(Transaction.type == TransactionType.income).scalar()

    expense_total = db.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(Transaction.type == TransactionType.expense).scalar()

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=total_users - active_users,
        total_transactions=total_transactions,
        total_income_all_users=Decimal(str(income_total)),
        total_expenses_all_users=Decimal(str(expense_total)),
        users_by_role=users_by_role,
    )
