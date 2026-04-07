from datetime import datetime, timezone
from typing import List, Optional, Tuple
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:

    @staticmethod
    def get(db: Session, id: int, owner_id: int) -> Optional[Transaction]:
        """Fetch a single transaction belonging to the given owner."""
        return (
            db.query(Transaction)
            .filter(Transaction.id == id, Transaction.owner_id == owner_id)
            .first()
        )

    @staticmethod
    def get_multi(
        db: Session,
        *,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[Transaction], int]:
        """Return a paginated, filtered list of transactions and total count."""
        query = db.query(Transaction).filter(Transaction.owner_id == owner_id)

        if category:
            query = query.filter(func.lower(Transaction.category) == category.lower())
        if type:
            query = query.filter(Transaction.type == type)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        # Count before pagination to avoid sub-query inefficiency
        total = query.count()
        transactions = (
            query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
        )
        return transactions, total

    @staticmethod
    def create(db: Session, *, obj_in: TransactionCreate, owner_id: int) -> Transaction:
        date_val = obj_in.date or datetime.now(timezone.utc)
        db_obj = Transaction(
            amount=obj_in.amount,
            type=obj_in.type,
            category=obj_in.category,
            notes=obj_in.notes,
            date=date_val,
            owner_id=owner_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(
        db: Session, *, db_obj: Transaction, obj_in: TransactionUpdate
    ) -> Transaction:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def remove(db: Session, *, id: int, owner_id: int) -> Optional[Transaction]:
        obj = (
            db.query(Transaction)
            .filter(Transaction.id == id, Transaction.owner_id == owner_id)
            .first()
        )
        if obj:
            db.delete(obj)
            db.commit()
        return obj
