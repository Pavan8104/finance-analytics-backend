from pydantic import BaseModel
from typing import Dict, Any, List

class CategoryBreakdown(BaseModel):
    category: str
    total_amount: float

class AnalyticsReport(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    income_by_category: List[CategoryBreakdown]
    expenses_by_category: List[CategoryBreakdown]
    
class MonthlyBreakdown(BaseModel):
    month: str # YYYY-MM
    income: float
    expense: float
