from typing import Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transaction import Transaction, TransactionCreate, TransactionUpdate, PaginatedResponse
from app.models.transaction import TransactionType
from app.services.transaction_service import TransactionService
from app.core.dependencies import get_current_user
from app.models.user import User as UserModel

router = APIRouter()

@router.post("/", response_model=Transaction)
def create_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_in: TransactionCreate,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Create a new transaction.
    """
    transaction = TransactionService.create(db=db, obj_in=transaction_in, owner_id=current_user.id)
    return transaction

@router.get("/", response_model=PaginatedResponse[Transaction])
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    type: Optional[TransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Retrieve transactions with advanced filtering and pagination.
    """
    transactions, total = TransactionService.get_multi(
        db, 
        owner_id=current_user.id, 
        skip=skip, 
        limit=limit,
        category=category,
        type=type,
        start_date=start_date,
        end_date=end_date
    )
    
    pages = (total + limit - 1) // limit

    return PaginatedResponse(
        items=transactions,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages
    )

@router.get("/{id}", response_model=Transaction)
def read_transaction(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Get transaction by ID.
    """
    transaction = TransactionService.get(db=db, id=id, owner_id=current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{id}", response_model=Transaction)
def update_transaction(
    *,
    db: Session = Depends(get_db),
    id: int,
    transaction_in: TransactionUpdate,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Update a transaction.
    """
    transaction = TransactionService.get(db=db, id=id, owner_id=current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    transaction = TransactionService.update(db=db, db_obj=transaction, obj_in=transaction_in)
    return transaction

@router.delete("/{id}", response_model=Transaction)
def delete_transaction(
    *,
    db: Session = Depends(get_db),
    id: int,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Delete a transaction.
    """
    transaction = TransactionService.remove(db=db, id=id, owner_id=current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
