"""
Field-level validation pipeline.
Each validator returns a list of ValidationIssue objects — it never raises.
"""
import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from app.models.models import AnomalyCategory, AnomalySeverity
from app.services.ingestion.parser import ParsedRow

logger = logging.getLogger(__name__)

VALID_CURRENCIES = {"INR", "USD", "EUR", "GBP", "AED", "SGD"}
VALID_SPLIT_TYPES = {"equal", "unequal", "percentage", "share"}
MAX_REASONABLE_AMOUNT = Decimal("10_000_000")  # 1 crore — flag anything above


@dataclass
class ValidationIssue:
    category: AnomalyCategory
    severity: AnomalySeverity
    reason: str
    resolution: str | None = None


@dataclass
class ValidationResult:
    row: ParsedRow
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == AnomalySeverity.ERROR for i in self.issues)


def validate_row(row: ParsedRow) -> ValidationResult:
    """Run all field-level validators against a single parsed row."""
    result = ValidationResult(row=row)

    _validate_paid_by(row, result)
    _validate_amount(row, result)
    _validate_currency(row, result)
    _validate_split_type(row, result)
    _validate_description(row, result)

    return result


# ---------------------------------------------------------------------------
# Individual field validators
# ---------------------------------------------------------------------------

def _validate_paid_by(row: ParsedRow, result: ValidationResult) -> None:
    if not row.raw.get("paid_by", "").strip():
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.MISSING_PAYER,
            severity=AnomalySeverity.ERROR,
            reason="Field 'paid_by' is empty — cannot determine who paid.",
            resolution="Imported with payer=NULL. Requires manual correction.",
        ))


def _validate_amount(row: ParsedRow, result: ValidationResult) -> None:
    raw_amount = row.raw.get("amount", "")

    # Strip thousands separators before parsing
    cleaned = raw_amount.replace(",", "").strip()

    if not cleaned:
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.INVALID_AMOUNT,
            severity=AnomalySeverity.ERROR,
            reason="Amount field is empty.",
            resolution="Row rejected.",
        ))
        return

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.INVALID_AMOUNT,
            severity=AnomalySeverity.ERROR,
            reason=f"Amount '{raw_amount}' cannot be parsed as a number.",
            resolution="Row rejected.",
        ))
        return

    # Comma-formatted amount (informational normalization)
    if "," in raw_amount:
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.AMOUNT_FORMAT_NORMALIZED,
            severity=AnomalySeverity.INFO,
            reason=f"Amount '{raw_amount}' contained comma thousands separator.",
            resolution=f"Normalized to {amount}.",
        ))

    # Zero amount
    if amount == Decimal("0"):
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.ZERO_AMOUNT,
            severity=AnomalySeverity.WARNING,
            reason="Amount is zero. This may be a placeholder or erroneous entry.",
            resolution="Row imported with status=WARNING. Review and correct manually.",
        ))

    # Negative amount (refund)
    if amount < Decimal("0"):
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.REFUND_TRANSACTION,
            severity=AnomalySeverity.INFO,
            reason=f"Negative amount {amount} indicates a refund.",
            resolution="Imported as expense_type=REFUND.",
        ))

    # Excessive decimal precision
    if amount == amount.quantize(Decimal("0.001")) and amount != amount.quantize(Decimal("0.01")):
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.AMOUNT_PRECISION_NORMALIZED,
            severity=AnomalySeverity.INFO,
            reason=f"Amount {amount} has more than 2 decimal places.",
            resolution=f"Rounded to {round(amount, 2)}.",
        ))

    # Unreasonably large amount
    if amount > MAX_REASONABLE_AMOUNT:
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.INVALID_AMOUNT,
            severity=AnomalySeverity.WARNING,
            reason=f"Amount {amount} exceeds reasonable threshold of {MAX_REASONABLE_AMOUNT}.",
            resolution="Imported with status=WARNING. Verify before processing.",
        ))


def _validate_currency(row: ParsedRow, result: ValidationResult) -> None:
    currency = row.raw.get("currency", "").strip().upper()
    if not currency:
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.MISSING_CURRENCY,
            severity=AnomalySeverity.ERROR,
            reason="Currency field is empty.",
            resolution="Inferred as INR based on majority currency in this import. Flagged for review.",
        ))


def _validate_split_type(row: ParsedRow, result: ValidationResult) -> None:
    split_type = row.raw.get("split_type", "").strip().lower()
    if not split_type:
        # Settlements have no split type — this is expected
        description = row.raw.get("description", "").lower()
        notes = row.raw.get("notes", "").lower()
        if "settlement" in notes or "paid" in description and "back" in description:
            return  # Will be caught by anomaly detector as SETTLEMENT
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.MISSING_SPLIT_TYPE,
            severity=AnomalySeverity.WARNING,
            reason="split_type is empty and row does not appear to be a settlement.",
            resolution="Imported with split_type=NULL.",
        ))


def _validate_description(row: ParsedRow, result: ValidationResult) -> None:
    if not row.raw.get("description", "").strip():
        result.issues.append(ValidationIssue(
            category=AnomalyCategory.INVALID_AMOUNT,  # Reuse closest category
            severity=AnomalySeverity.WARNING,
            reason="Description is empty.",
            resolution="Imported with description='(no description)'.",
        ))
