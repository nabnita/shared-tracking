"""
Main anomaly detection engine.
Runs all rule modules against the normalized row set and returns a consolidated
list of AnomalyRecord objects ready to be persisted.
"""
import logging
from dataclasses import dataclass, field
from datetime import date

from app.models.models import AnomalyCategory, AnomalySeverity, ExpenseType
from app.services.ingestion.validator import ValidationIssue, validate_row
from app.services.normalization.normalizer import NormalizedRow
from app.services.anomaly.rules.duplicate import detect_duplicates
from app.services.anomaly.rules.settlement import classify_settlement, classify_refund
from app.services.anomaly.rules.split_conflict import check_percentage_split, check_conflicting_split
from app.services.anomaly.rules.unknown_participant import check_unknown_participants, check_stale_participant

logger = logging.getLogger(__name__)

# Meera departed after 2026-03-28 based on CSV analysis
DEPARTED_USERS: dict[str, str] = {
    "Meera": "moved out ~2026-03-28 (farewell dinner row 32)",
}


@dataclass
class AnomalyRecord:
    row_number: int
    category: AnomalyCategory
    severity: AnomalySeverity
    reason: str
    resolution: str | None
    # Which duplicate pair this belongs to (if any)
    duplicate_peer_row: int | None = None


@dataclass
class RowDecision:
    row: NormalizedRow
    anomalies: list[AnomalyRecord] = field(default_factory=list)
    expense_type: ExpenseType = ExpenseType.EXPENSE
    # Rows marked as duplicate of another row
    is_duplicate_of: int | None = None

    @property
    def should_reject(self) -> bool:
        """Reject if any ERROR anomaly exists (except MISSING_PAYER which imports with WARNING)."""
        for a in self.anomalies:
            if a.severity == AnomalySeverity.ERROR and a.category not in {
                AnomalyCategory.MISSING_PAYER,
                AnomalyCategory.MISSING_CURRENCY,
            }:
                return True
        # Explicit duplicate rejection (second row of a pair)
        return self.is_duplicate_of is not None

    @property
    def has_warnings(self) -> bool:
        return any(a.severity != AnomalySeverity.INFO for a in self.anomalies)


def run_detection(normalized_rows: list[NormalizedRow]) -> list[RowDecision]:
    """
    Full anomaly detection pass over all normalized rows.

    Order of operations:
    1. Build known-user registry from all paid_by values.
    2. Run per-row validators (from ingestion pipeline).
    3. Classify settlement and refund transactions.
    4. Check split integrity.
    5. Check participant validity.
    6. Run batch-level duplicate detection.
    7. Mark duplicate rows.
    """
    decisions: dict[int, RowDecision] = {
        row.row_number: RowDecision(row=row) for row in normalized_rows
    }

    # 1. Build known-user registry
    known_names: set[str] = {
        row.paid_by for row in normalized_rows if row.paid_by
    }

    # 2–5. Per-row checks
    for row in normalized_rows:
        decision = decisions[row.row_number]

        # Re-run field validation to surface any issues not caught by normalizer
        from app.services.ingestion.parser import ParsedRow
        parsed = ParsedRow(row_number=row.row_number, raw=row.raw)
        validation = validate_row(parsed)
        for issue in validation.issues:
            decision.anomalies.append(_to_record(row.row_number, issue))

        # Settlement / refund classification
        settlement = classify_settlement(row)
        if settlement:
            decision.expense_type = ExpenseType.SETTLEMENT
            decision.anomalies.append(_to_record(row.row_number, settlement))

        refund = classify_refund(row)
        if refund:
            decision.expense_type = ExpenseType.REFUND
            decision.anomalies.append(_to_record(row.row_number, refund))

        # Percentage split validation
        for issue in check_percentage_split(row):
            decision.anomalies.append(_to_record(row.row_number, issue))

        # Conflicting split type
        conflict = check_conflicting_split(row)
        if conflict:
            decision.anomalies.append(_to_record(row.row_number, conflict))

        # Unknown / stale participants
        for issue in check_unknown_participants(row, known_names):
            decision.anomalies.append(_to_record(row.row_number, issue))

        for issue in check_stale_participant(row, DEPARTED_USERS):
            decision.anomalies.append(_to_record(row.row_number, issue))

    # 6. Batch-level duplicate detection
    duplicate_pairs = detect_duplicates(normalized_rows)
    duplicate_rejected: set[int] = set()

    for dup in duplicate_pairs:
        row_a = decisions[dup.row_a]
        row_b = decisions[dup.row_b]

        # Attach anomaly to both rows
        record_a = AnomalyRecord(
            row_number=dup.row_a,
            category=AnomalyCategory.DUPLICATE_EXPENSE,
            severity=dup.severity,
            reason=dup.reason,
            resolution=dup.resolution,
            duplicate_peer_row=dup.row_b,
        )
        record_b = AnomalyRecord(
            row_number=dup.row_b,
            category=AnomalyCategory.DUPLICATE_EXPENSE,
            severity=dup.severity,
            reason=dup.reason,
            resolution=dup.resolution,
            duplicate_peer_row=dup.row_a,
        )
        row_a.anomalies.append(record_a)
        row_b.anomalies.append(record_b)

        # 7. Reject the later row (higher row_number) as the duplicate
        later_row = max(dup.row_a, dup.row_b)
        if later_row not in duplicate_rejected:
            decisions[later_row].is_duplicate_of = min(dup.row_a, dup.row_b)
            duplicate_rejected.add(later_row)

    return list(decisions.values())


def _to_record(row_number: int, issue: ValidationIssue) -> AnomalyRecord:
    return AnomalyRecord(
        row_number=row_number,
        category=issue.category,
        severity=issue.severity,
        reason=issue.reason,
        resolution=issue.resolution,
    )
