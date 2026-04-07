from typing import Any, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User as UserModel
from app.models.transaction import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    PaginatedResponse,
)
from app.services.transaction_service import TransactionService
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
)
def create_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_in: TransactionCreate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Create a new income or expense transaction for the current user."""
    transaction = TransactionService.create(
        db=db, obj_in=transaction_in, owner_id=current_user.id
    )
    # Invalidate analytics cache for this user so the next report is fresh
    AnalyticsService.invalidate_cache(current_user.id)
    return transaction


@router.get(
    "/",
    response_model=PaginatedResponse[TransactionResponse],
    summary="List transactions with filters and pagination",
)
def read_transactions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=200, description="Page size (max 200)"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    start_date: Optional[datetime] = Query(None, description="Filter from date (ISO-8601)"),
    end_date: Optional[datetime] = Query(None, description="Filter to date (ISO-8601)"),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve the authenticated user's transactions.
    Supports filtering by category, type, and date range with pagination.
    """
    transactions, total = TransactionService.get_multi(
        db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        category=category,
        type=type,
        start_date=start_date,
        end_date=end_date,
    )
    current_page = (skip // limit) + 1
    pages = max(1, (total + limit - 1) // limit)
    has_next = current_page < pages
    has_prev = current_page > 1

    return PaginatedResponse(
        items=transactions,
        total=total,
        page=current_page,
        size=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev,
        next_skip=(skip + limit) if has_next else None,
    )


# NOTE: /export must be declared BEFORE /{transaction_id} — FastAPI matches
# routes top-to-bottom, and "export" would otherwise be parsed as a
# transaction_id string (and fail the int cast with a 422 error).
@router.get(
    "/export",
    summary="Export transactions as CSV",
    description=(
        "Download all your transactions as a CSV file. "
        "Accepts the same filters as the list endpoint (type, category, date range). "
        "Opens directly in Excel and Google Sheets."
    ),
    response_class=StreamingResponse,
)
def export_transactions_csv(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    type: Optional[TransactionType] = Query(None, description="Filter by income or expense"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    start_date: Optional[datetime] = Query(None, description="Include transactions from this date"),
    end_date: Optional[datetime] = Query(None, description="Include transactions up to this date"),
) -> StreamingResponse:
    """
    Exports the authenticated user's transactions to a CSV file.

    The filename includes today's date so repeated exports don't
    overwrite each other in the user's Downloads folder.
    """
    buffer = TransactionService.export_to_csv(
        db,
        owner_id=current_user.id,
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )

    # e.g. "transactions_2024-07-15.csv" — makes sense when user has multiple exports
    filename = f"transactions_{date.today().isoformat()}.csv"

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a specific transaction",
)
def read_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: int,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Retrieve a specific transaction by ID (must belong to the current user)."""
    transaction = TransactionService.get(
        db=db, id=transaction_id, owner_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )
    return transaction


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
)
def update_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: int,
    transaction_in: TransactionUpdate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Update a transaction. Only the owner can update their own transactions."""
    transaction = TransactionService.get(
        db=db, id=transaction_id, owner_id=current_user.id
    )
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )
    updated = TransactionService.update(db=db, db_obj=transaction, obj_in=transaction_in)
    AnalyticsService.invalidate_cache(current_user.id)
    return updated


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
)
def delete_transaction(
    *,
    db: Session = Depends(get_db),
    transaction_id: int,
    current_user: UserModel = Depends(get_current_active_user),
) -> None:
    """Delete a transaction. Only the owner can delete their own transactions."""
    transaction = TransactionService.remove(
        db=db, id=transaction_id, owner_id=current_user.id
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction {transaction_id} not found.")

    AnalyticsService.invalidate_cache(owner_id=current_user.id)
    return None

