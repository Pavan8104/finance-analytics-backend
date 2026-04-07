import enum

from sqlalchemy import (
    Column, DateTime, Enum, ForeignKey, Index,
    Integer, Numeric, String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Use Numeric(precision, scale) instead of Float to prevent IEEE 754
    # rounding errors in financial calculations (e.g., 0.1 + 0.2 != 0.3)
    amount = Column(Numeric(precision=12, scale=2), nullable=False)

    type = Column(Enum(TransactionType), nullable=False, index=True)
    category = Column(String(100), index=True, nullable=False)
    notes = Column(String(500), nullable=True)
    date = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("User", back_populates="transactions")

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        # Composite index: most analytics/transaction queries filter by owner + date
        Index("ix_transactions_owner_date", "owner_id", "date"),
        # Composite index for the common owner + type aggregate pattern
        Index("ix_transactions_owner_type", "owner_id", "type"),
    )
