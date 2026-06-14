"""
Settlement and refund transaction classifiers.
A row is a settlement when description/notes signal a peer debt repayment.
A row is a refund when the amount is negative.
"""
import re

from app.models.models import AnomalyCategory, AnomalySeverity
from app.services.ingestion.validator import ValidationIssue
from app.services.normalization.normalizer import NormalizedRow

SETTLEMENT_SIGNALS = re.compile(
    r"\b(paid back|paid .* back|settlement|settling|repaid|reimbursed|owes|owed|deposit)\b",
    re.IGNORECASE,
)


def classify_settlement(row: NormalizedRow) -> ValidationIssue | None:
    text = f"{row.description} {row.notes}".lower()
    if SETTLEMENT_SIGNALS.search(text) or (not row.split_type and row.paid_by and len(row.split_with) == 1):
        return ValidationIssue(
            category=AnomalyCategory.SETTLEMENT_TRANSACTION,
            severity=AnomalySeverity.WARNING,
            reason=f"Row appears to be a peer settlement, not a shared expense. Description: '{row.description}'.",
            resolution="Imported as expense_type=SETTLEMENT. Share computation skipped.",
        )
    return None


def classify_refund(row: NormalizedRow) -> ValidationIssue | None:
    from decimal import Decimal
    if row.amount is not None and row.amount < Decimal("0"):
        return ValidationIssue(
            category=AnomalyCategory.REFUND_TRANSACTION,
            severity=AnomalySeverity.INFO,
            reason=f"Negative amount {row.amount} indicates a refund/credit.",
            resolution="Imported as expense_type=REFUND. Negative amount applied to participant shares.",
        )
    return None
