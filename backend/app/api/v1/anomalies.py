"""
GET /anomalies — List anomalies with filtering and pagination
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Anomaly, AnomalyCategory, AnomalySeverity
from app.schemas import AnomalyOut, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_anomalies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    import_id: uuid.UUID | None = Query(None),
    severity: AnomalySeverity | None = Query(None),
    category: AnomalyCategory | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List anomalies filterable by import, severity, and category."""
    query = select(Anomaly)

    if import_id:
        query = query.where(Anomaly.import_id == import_id)
    if severity:
        query = query.where(Anomaly.severity == severity)
    if category:
        query = query.where(Anomaly.category == category)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Anomaly.severity.asc(), Anomaly.row_number.asc())
        .offset(offset)
        .limit(page_size)
    )
    anomalies = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AnomalyOut.model_validate(a) for a in anomalies],
    )
