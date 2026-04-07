from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class CategoryBreakdown(BaseModel):
    category: str
    total_amount: Decimal
    transaction_count: int
    percentage: float  # As a percentage of the total for that type


class MonthlyBreakdown(BaseModel):
    month: str          # Format: YYYY-MM
    income: Decimal
    expense: Decimal
    net: Decimal        # income - expense


class AnalyticsReport(BaseModel):
    # Totals
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal            # total_income - total_expenses
    transaction_count: int
    avg_transaction_amount: Decimal

    # Breakdowns
    income_by_category: List[CategoryBreakdown]
    expenses_by_category: List[CategoryBreakdown]
    monthly_breakdown: List[MonthlyBreakdown]

    # Meta
    currency: str = "USD"
