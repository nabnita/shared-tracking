"""
POST /imports  — Upload and process a CSV file
GET  /imports  — List all import reports (paginated)
GET  /imports/{id} — Get import report detail
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import ImportReport
from app.schemas import ImportReportDetail, ImportReportSummary, PaginatedResponse
from app.services.ingestion.pipeline import run_import_pipeline

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"text/csv", "application/csv", "application/octet-stream", "text/plain"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=ImportReportDetail)
async def upload_csv(
    file: Annotated[UploadFile, File(description="Expense CSV file")],
    db: AsyncSession = Depends(get_db),
) -> ImportReportDetail:
    """
    Upload an expense CSV for import processing.

    The pipeline will:
    - Parse the CSV
    - Normalize all fields
    - Detect anomalies
    - Persist cleaned data to the database
    - Return the full import report
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES and not (
        file.filename or ""
    ).endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are supported.",
        )

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit.",
        )

    if not contents.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    report = await run_import_pipeline(
        file_contents=contents,
        filename=file.filename or "upload.csv",
        db=db,
    )

    return ImportReportDetail.model_validate(report)


@router.get("", response_model=PaginatedResponse)
async def list_imports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List all import reports, newest first."""
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count()).select_from(ImportReport))
    total = count_result.scalar_one()

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


@router.get("/{import_id}", response_model=ImportReportDetail)
async def get_import(
    import_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ImportReportDetail:
    """Get the full detail and report JSON for a specific import."""
    result = await db.execute(
        select(ImportReport).where(ImportReport.id == import_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found.")
    return ImportReportDetail.model_validate(report)
