"""
GET /reports       — List all import reports
GET /reports/{id}  — Get full report JSON for a specific import
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import ImportReport
from app.schemas import ImportReportDetail, ImportReportSummary, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List all import reports, newest first."""
    count_result = await db.execute(select(func.count()).select_from(ImportReport))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(ImportReport)
        .order_by(ImportReport.imported_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    reports = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ImportReportSummary.model_validate(r) for r in reports],
    )


@router.get("/{report_id}", response_model=ImportReportDetail)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ImportReportDetail:
    """Get the full import report including the machine-readable JSON payload."""
    result = await db.execute(
        select(ImportReport).where(ImportReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return ImportReportDetail.model_validate(report)
