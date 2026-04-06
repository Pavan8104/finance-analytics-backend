from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from app.models.transaction import TransactionType

T = TypeVar('T')

class TransactionBase(BaseModel):
    amount: float
    type: TransactionType
    category: str
    notes: Optional[str] = None
    date: Optional[datetime] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[datetime] = None

class TransactionInDBBase(TransactionBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

class Transaction(TransactionInDBBase):
    pass

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
