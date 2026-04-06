from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from sqlalchemy import func

class TransactionService:
    @staticmethod
    def get(db: Session, id: int, owner_id: int) -> Optional[Transaction]:
        return db.query(Transaction).filter(Transaction.id == id, Transaction.owner_id == owner_id).first()

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
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Transaction], int]:
        query = db.query(Transaction).filter(Transaction.owner_id == owner_id)
        
        # Advanced Filtering
        if category:
            query = query.filter(func.lower(Transaction.category) == category.lower())
        if type:
            query = query.filter(Transaction.type == type)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
            
        total = query.count()
        
        # Pagination
        transactions = query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()
        return transactions, total

    @staticmethod
    def create(db: Session, *, obj_in: TransactionCreate, owner_id: int) -> Transaction:
        # Default the date if it's none
        date_val = obj_in.date if obj_in.date else datetime.now()
        
        db_obj = Transaction(
            **obj_in.model_dump(exclude={'date'}),
            date=date_val,
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update(db: Session, *, db_obj: Transaction, obj_in: TransactionUpdate) -> Transaction:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def remove(db: Session, *, id: int, owner_id: int) -> Transaction:
        obj = db.query(Transaction).filter(Transaction.id == id, Transaction.owner_id == owner_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj
