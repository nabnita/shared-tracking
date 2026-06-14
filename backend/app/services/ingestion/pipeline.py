"""
Main import pipeline orchestrator.
Ties together: parse → validate → normalize → detect anomalies → persist → generate report.
"""
import json
import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Anomaly,
    AnomalyCategory,
    AnomalySeverity,
    Expense,
    ExpenseParticipant,
    ExpenseStatus,
    ExpenseType,
    ImportReport,
    SplitType,
    User,
)
from app.services.anomaly.detector import RowDecision, run_detection
from app.services.ingestion.parser import ParseResult, parse_csv
from app.services.normalization.normalizer import NormalizedRow, normalize_row
from app.services.reports.report_builder import build_report

logger = logging.getLogger(__name__)


async def run_import_pipeline(
    file_contents: bytes,
    filename: str,
    db: AsyncSession,
) -> ImportReport:
    """
    Full CSV import pipeline:
    1. Parse CSV
    2. Normalize each row
    3. Detect anomalies
    4. Persist users, expenses, participants, anomalies
    5. Generate and store the import report
    """
    # Step 1: Parse
    parse_result: ParseResult = parse_csv(file_contents, filename)

    # Step 2: Normalize
    normalized_rows: list[NormalizedRow] = [
        normalize_row(pr) for pr in parse_result.rows if pr.parse_error is None
    ]

    # Step 3: Detect anomalies
    decisions: list[RowDecision] = run_detection(normalized_rows)

    # Step 4: Persist — create ImportReport shell first (needed as FK)
    report_record = ImportReport(
        id=uuid.uuid4(),
        filename=filename,
        total_rows=parse_result.total_rows,
    )
    db.add(report_record)
    await db.flush()  # Get the ID without committing

    # Build user registry: normalized_name → User ORM object
    user_registry: dict[str, User] = await _get_or_create_users(
        normalized_rows, db
    )

    # Persist expenses + participants + anomalies
    imported = rejected = warnings = 0
    for decision in decisions:
        row = decision.row

        status = _compute_status(decision)
        if status == ExpenseStatus.REJECTED:
            rejected += 1
        elif status == ExpenseStatus.WARNING:
            warnings += 1
        else:
            imported += 1

        payer: User | None = user_registry.get(row.paid_by) if row.paid_by else None

        expense = Expense(
            id=uuid.uuid4(),
            import_id=report_record.id,
            payer_id=payer.id if payer else None,
            row_number=row.row_number,
            expense_date=row.expense_date,
            description=row.description,
            amount=row.amount or Decimal("0"),
            currency=row.currency,
            split_type=_parse_split_type(row.split_type),
            expense_type=decision.expense_type,
            status=status,
            raw_row=json.dumps(row.raw),
        )
        db.add(expense)
        await db.flush()

        # Participants (skip for settlements)
        if decision.expense_type != ExpenseType.SETTLEMENT and row.split_with:
            await _create_participants(expense, row, user_registry, db)

        # Anomalies
        for anomaly in decision.anomalies:
            db.add(Anomaly(
                id=uuid.uuid4(),
                import_id=report_record.id,
                expense_id=expense.id,
                row_number=anomaly.row_number,
                category=anomaly.category,
                severity=anomaly.severity,
                reason=anomaly.reason,
                resolution=anomaly.resolution,
                raw_row=json.dumps(row.raw),
            ))

    # Step 5: Finalize report
    report_dict = build_report(filename, decisions, str(report_record.id))
    report_record.imported_count = imported
    report_record.rejected_count = rejected
    report_record.warning_count = warnings
    report_record.report_json = json.dumps(report_dict)

    return report_record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_create_users(
    rows: list[NormalizedRow], db: AsyncSession
) -> dict[str, User]:
    """
    Collect all unique names (payers + participants) and upsert User records.
    Returns a mapping of normalized_name → User.
    """
    from sqlalchemy import select

    all_names: set[str] = set()
    for row in rows:
        if row.paid_by:
            all_names.add(row.paid_by)
        all_names.update(row.split_with)

    registry: dict[str, User] = {}

    for name in all_names:
        norm = name.lower().strip()
        result = await db.execute(
            select(User).where(User.normalized_name == norm)
        )
        existing = result.scalar_one_or_none()
        if existing:
            registry[name] = existing
        else:
            is_guest = _is_guest_name(name)
            user = User(
                id=uuid.uuid4(),
                name=name,
                normalized_name=norm,
                is_guest=is_guest,
            )
            db.add(user)
            await db.flush()
            registry[name] = user

    return registry


def _is_guest_name(name: str) -> bool:
    guest_signals = ("kabir", "friend", "guest", "visitor")
    return any(s in name.lower() for s in guest_signals)


async def _create_participants(
    expense: Expense,
    row: NormalizedRow,
    user_registry: dict[str, User],
    db: AsyncSession,
) -> None:
    import re
    from decimal import Decimal, InvalidOperation

    participants = row.split_with
    n = len(participants)
    if n == 0:
        return

    for name in participants:
        user = user_registry.get(name)
        if not user:
            continue

        share_amount: Decimal | None = None
        share_pct: Decimal | None = None
        share_weight: int | None = None
        amount = expense.amount or Decimal("0")

        if row.split_type == "equal":
            share_amount = (amount / n).quantize(Decimal("0.01"))

        elif row.split_type == "percentage" and row.split_details:
            pct_match = re.search(
                rf"{re.escape(name)}\s+(\d+(?:\.\d+)?)\s*%",
                row.split_details,
                re.IGNORECASE,
            )
            if pct_match:
                pct = Decimal(pct_match.group(1))
                share_pct = pct
                share_amount = (amount * pct / 100).quantize(Decimal("0.01"))

        elif row.split_type == "share" and row.split_details:
            weight_match = re.search(
                rf"{re.escape(name)}\s+(\d+)",
                row.split_details,
                re.IGNORECASE,
            )
            if weight_match:
                share_weight = int(weight_match.group(1))

        elif row.split_type == "unequal" and row.split_details:
            amount_match = re.search(
                rf"{re.escape(name)}\s+(\d+(?:\.\d+)?)",
                row.split_details,
                re.IGNORECASE,
            )
            if amount_match:
                share_amount = Decimal(amount_match.group(1)).quantize(Decimal("0.01"))

        db.add(ExpenseParticipant(
            id=uuid.uuid4(),
            expense_id=expense.id,
            user_id=user.id,
            share_amount=share_amount,
            share_percentage=share_pct,
            share_weight=share_weight,
        ))


def _compute_status(decision: RowDecision) -> ExpenseStatus:
    if decision.should_reject:
        return ExpenseStatus.REJECTED
    if decision.has_warnings:
        return ExpenseStatus.WARNING
    return ExpenseStatus.IMPORTED


def _parse_split_type(raw: str | None) -> SplitType | None:
    if not raw:
        return None
    try:
        return SplitType(raw.lower())
    except ValueError:
        return None
