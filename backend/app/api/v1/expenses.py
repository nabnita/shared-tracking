"""
GET /expenses       — List expenses with filtering and pagination
GET /expenses/{id}  — Get expense detail with participants
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import Expense, ExpenseStatus, ExpenseType
from app.schemas import ExpenseDetail, ExpenseSummary, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    import_id: uuid.UUID | None = Query(None),
    currency: str | None = Query(None),
    status: ExpenseStatus | None = Query(None),
    expense_type: ExpenseType | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List expenses with optional filters for import, currency, status, type, and date range."""
    query = select(Expense).options(selectinload(Expense.payer))

    if import_id:
        query = query.where(Expense.import_id == import_id)
    if currency:
        query = query.where(Expense.currency == currency.upper())
    if status:
        query = query.where(Expense.status == status)
    if expense_type:
        query = query.where(Expense.expense_type == expense_type)
    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Expense.expense_date.asc().nulls_last(), Expense.row_number.asc())
        .offset(offset)
        .limit(page_size)
    )
    expenses = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ExpenseSummary.model_validate(e) for e in expenses],
    )


@router.get("/{expense_id}", response_model=ExpenseDetail)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExpenseDetail:
    """Get full expense detail including participants and their share amounts."""
    result = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id)
        .options(
            selectinload(Expense.payer),
            selectinload(Expense.participants).selectinload(
                # Import here to avoid circular at module level
                __import__("app.models.models", fromlist=["ExpenseParticipant"]).ExpenseParticipant.user
            ),
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    return ExpenseDetail.model_validate(expense)
