from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.transaction import TransactionType

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Must be positive")
    type: TransactionType
    category: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None

    @field_validator("category")
    @classmethod
    def strip_category(cls, v: str) -> str:
        return v.strip().title()


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class TransactionResponse(TransactionBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Keep backward-compatible alias
Transaction = TransactionResponse


# ---------------------------------------------------------------------------
# Paginated response wrapper (generic)
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool
    next_skip: Optional[int] = None  # Convenience: pass as `skip` for the next page
