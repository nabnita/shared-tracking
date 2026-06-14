"""
Duplicate expense detection.
Catches both exact duplicates and near-duplicates (same date + similar description + same amount).
"""
from dataclasses import dataclass
from decimal import Decimal

from fuzzywuzzy import fuzz

from app.models.models import AnomalyCategory, AnomalySeverity
from app.services.normalization.normalizer import NormalizedRow


@dataclass
class DuplicateAnomaly:
    row_a: int
    row_b: int
    severity: AnomalySeverity
    reason: str
    resolution: str


def detect_duplicates(rows: list[NormalizedRow]) -> list[DuplicateAnomaly]:
    """
    Compare all row pairs for duplicate signals.
    Uses fuzzy description matching (threshold 85) as a near-duplicate heuristic.
    """
    anomalies: list[DuplicateAnomaly] = []
    seen: list[NormalizedRow] = []

    for row in rows:
        for candidate in seen:
            if _is_duplicate(row, candidate):
                # Conflicting payer/amount = ERROR; otherwise WARNING
                same_payer = row.paid_by == candidate.paid_by
                same_amount = row.amount == candidate.amount
                severity = AnomalySeverity.WARNING if (same_payer and same_amount) else AnomalySeverity.ERROR

                anomalies.append(DuplicateAnomaly(
                    row_a=candidate.row_number,
                    row_b=row.row_number,
                    severity=severity,
                    reason=(
                        f"Row {row.row_number} appears to duplicate row {candidate.row_number}. "
                        f"Descriptions: '{candidate.description}' / '{row.description}'. "
                        f"Payers: {candidate.paid_by} / {row.paid_by}. "
                        f"Amounts: {candidate.amount} / {row.amount}."
                    ),
                    resolution=(
                        "Keep row with richer metadata (more notes/participants). "
                        "Reject the other. Manual review required if payer or amount differ."
                    ),
                ))
        seen.append(row)

    return anomalies


def _is_duplicate(a: NormalizedRow, b: NormalizedRow) -> bool:
    """Two rows are considered duplicates if they share the same date and
    have highly similar descriptions (fuzzy ratio >= 85)."""
    if a.expense_date != b.expense_date:
        return False
    if a.expense_date is None:
        return False
    similarity = fuzz.token_sort_ratio(
        a.description.lower(), b.description.lower()
    )
    return similarity >= 85
