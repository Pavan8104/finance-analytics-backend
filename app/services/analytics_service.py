"""
Analytics service with a production-safe TTLCache implementation.

Problem with the original:
  @cached(analytics_cache)
  def generate_report(db: Session, owner_id: int):
  → SQLAlchemy Session objects are NOT hashable, so cachetools uses them
    as part of the cache key, which fails with a TypeError in practice.

Fix:
  - Cache is keyed ONLY on `owner_id` (an int — hashable).
  - db session is passed into the internal method that bypasses the cache.
  - Cache invalidation is exposed so transaction mutations clear stale data.
"""
from decimal import Decimal
from threading import Lock
from typing import Dict, Optional

from cachetools import TTLCache
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.schemas.analytics import AnalyticsReport, CategoryBreakdown, MonthlyBreakdown

# ---------------------------------------------------------------------------
# Thread-safe in-memory TTL cache keyed on owner_id
# ---------------------------------------------------------------------------
_cache: TTLCache = TTLCache(maxsize=200, ttl=300)   # 5-minute TTL
_cache_lock = Lock()


class AnalyticsService:

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @staticmethod
    def generate_report(db: Session, owner_id: int) -> AnalyticsReport:
        """Return a cached analytics report, recomputing on cache miss."""
        with _cache_lock:
            cached = _cache.get(owner_id)
        if cached is not None:
            return cached

        report = AnalyticsService._compute_report(db, owner_id)

        with _cache_lock:
            _cache[owner_id] = report

        return report

    @staticmethod
    def invalidate_cache(owner_id: int) -> None:
        """Remove a user's cached report (call after any transaction mutation)."""
        with _cache_lock:
            _cache.pop(owner_id, None)

    # -----------------------------------------------------------------------
    # Internal computation — never cached directly
    # -----------------------------------------------------------------------

    @staticmethod
    def _compute_report(db: Session, owner_id: int) -> AnalyticsReport:
        # --- Aggregate totals ---
        income_agg = db.query(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.income,
        ).one()

        expense_agg = db.query(
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        ).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.expense,
        ).one()

        total_income = Decimal(str(income_agg[0]))
        income_count = income_agg[1]
        total_expenses = Decimal(str(expense_agg[0]))
        expense_count = expense_agg[1]
        transaction_count = income_count + expense_count
        balance = total_income - total_expenses

        total_all = total_income + total_expenses
        avg_amount = (
            (total_all / transaction_count).quantize(Decimal("0.01"))
            if transaction_count > 0
            else Decimal("0.00")
        )

        # --- Category breakdowns ---
        income_cats = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("cnt"),
        ).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.income,
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()

        expense_cats = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("cnt"),
        ).filter(
            Transaction.owner_id == owner_id,
            Transaction.type == TransactionType.expense,
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()

        def _to_breakdowns(rows, total_for_type: Decimal):
            result = []
            for row in rows:
                amt = Decimal(str(row.total))
                pct = float((amt / total_for_type * 100).quantize(Decimal("0.01"))) if total_for_type else 0.0
                result.append(CategoryBreakdown(
                    category=row.category,
                    total_amount=amt,
                    transaction_count=row.cnt,
                    percentage=pct,
                ))
            return result

        # --- Monthly breakdown ---
        monthly_rows = db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        ).filter(
            Transaction.owner_id == owner_id,
        ).group_by("year", "month", Transaction.type).order_by("year", "month").all()

        monthly_map: Dict[str, Dict[str, Decimal]] = {}
        for row in monthly_rows:
            key = f"{int(row.year):04d}-{int(row.month):02d}"
            if key not in monthly_map:
                monthly_map[key] = {"income": Decimal("0"), "expense": Decimal("0")}
            monthly_map[key][row.type.value] += Decimal(str(row.total))

        monthly_breakdown = [
            MonthlyBreakdown(
                month=k,
                income=v["income"],
                expense=v["expense"],
                net=v["income"] - v["expense"],
            )
            for k, v in sorted(monthly_map.items())
        ]

        return AnalyticsReport(
            total_income=total_income,
            total_expenses=total_expenses,
            balance=balance,
            transaction_count=transaction_count,
            avg_transaction_amount=avg_amount,
            income_by_category=_to_breakdowns(income_cats, total_income),
            expenses_by_category=_to_breakdowns(expense_cats, total_expenses),
            monthly_breakdown=monthly_breakdown,
        )
