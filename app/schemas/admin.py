from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class SystemStats(BaseModel):
    """System-wide statistics — admin only."""
    total_users: int
    active_users: int
    inactive_users: int

    total_transactions: int
    total_income_all_users: Decimal
    total_expenses_all_users: Decimal

    users_by_role: dict
