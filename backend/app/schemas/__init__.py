"""
Pydantic schemas for request/response serialization.
All schemas are defined here grouped by domain.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import (
    AnomalyCategory,
    AnomalySeverity,
    ExpenseStatus,
    ExpenseType,
    SplitType,
)


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    normalized_name: str
    is_guest: bool
    email: str | None = None


# ---------------------------------------------------------------------------
# Import Report
# ---------------------------------------------------------------------------

class ImportReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    imported_at: datetime
    total_rows: int
    imported_count: int
    rejected_count: int
    warning_count: int


class ImportReportDetail(ImportReportSummary):
    report_json: str | None = None


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------

class ExpenseParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user: UserOut
    share_amount: Decimal | None = None
    share_percentage: Decimal | None = None
    share_weight: int | None = None


class ExpenseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    import_id: UUID
    row_number: int
    expense_date: date | None = None
    description: str
    amount: Decimal
    currency: str | None = None
    split_type: SplitType | None = None
    expense_type: ExpenseType
    status: ExpenseStatus
    payer: UserOut | None = None


class ExpenseDetail(ExpenseSummary):
    participants: list[ExpenseParticipantOut] = Field(default_factory=list)
    raw_row: str | None = None


# ---------------------------------------------------------------------------
# Anomaly
# ---------------------------------------------------------------------------

class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    import_id: UUID
    expense_id: UUID | None = None
    row_number: int
    category: AnomalyCategory
    severity: AnomalySeverity
    reason: str
    resolution: str | None = None
    created_at: datetime
