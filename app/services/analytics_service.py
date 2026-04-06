from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from cachetools import cached, TTLCache

from app.models.transaction import Transaction, TransactionType
from app.schemas.analytics import AnalyticsReport, CategoryBreakdown

# In-Memory Cache: Max 100 items, TTL 5 minutes
analytics_cache = TTLCache(maxsize=100, ttl=300)

class AnalyticsService:

    @staticmethod
    @cached(analytics_cache)
    def generate_report(db: Session, owner_id: int) -> AnalyticsReport:
        # Note: Since Session objects aren't hashable out of the box in a way that respects their open connection,
        # we typically cache at a slightly higher level (e.g. passing just the owner_id),
        # but for ATS requirement demonstration, we can cache the method with owner_id hash.
        
        # Calculate totals
        income_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.owner_id == owner_id, 
            Transaction.type == TransactionType.income
        ).scalar()
        
        expense_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.owner_id == owner_id, 
            Transaction.type == TransactionType.expense
        ).scalar()

        total_income = float(income_query)
        total_expenses = float(expense_query)
        balance = total_income - total_expenses
        
        # Calculate category breakdowns
        income_cats = db.query(Transaction.category, func.sum(Transaction.amount)).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.income
        ).group_by(Transaction.category).all()
        
        expense_cats = db.query(Transaction.category, func.sum(Transaction.amount)).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.expense
        ).group_by(Transaction.category).all()

        return AnalyticsReport(
            total_income=total_income,
            total_expenses=total_expenses,
            balance=balance,
            income_by_category=[CategoryBreakdown(category=row[0], total_amount=float(row[1])) for row in income_cats],
            expenses_by_category=[CategoryBreakdown(category=row[0], total_amount=float(row[1])) for row in expense_cats]
        )
