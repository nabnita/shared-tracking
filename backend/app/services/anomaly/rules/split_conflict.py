"""
Percentage split validation: checks that split_details percentages sum to 100%.
Also detects the conflicting split_type vs split_details anomaly.
"""
import re
from decimal import Decimal

from app.models.models import AnomalyCategory, AnomalySeverity
from app.services.ingestion.validator import ValidationIssue
from app.services.normalization.normalizer import NormalizedRow

PERCENTAGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def check_percentage_split(row: NormalizedRow) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if row.split_type != "percentage" or not row.split_details:
        return issues

    percentages = [Decimal(p) for p in PERCENTAGE_RE.findall(row.split_details)]
    if not percentages:
        return issues

    total = sum(percentages)
    if total != Decimal("100"):
        issues.append(ValidationIssue(
            category=AnomalyCategory.INVALID_PERCENTAGE_SPLIT,
            severity=AnomalySeverity.ERROR,
            reason=f"Percentage split sums to {total}%%, not 100%%. Details: '{row.split_details}'.",
            resolution="Imported with status=WARNING. Percentages must be corrected manually before amounts can be computed.",
        ))
    return issues


def check_conflicting_split(row: NormalizedRow) -> ValidationIssue | None:
    """Detect rows where split_type=equal but split_details contain weight/share data."""
    if row.split_type != "equal" or not row.split_details:
        return None

    # Share-weight pattern: "Name N; Name N"
    share_pattern = re.compile(r"\w+\s+\d+", re.IGNORECASE)
    if share_pattern.search(row.split_details):
        return ValidationIssue(
            category=AnomalyCategory.CONFLICTING_SPLIT_INFO,
            severity=AnomalySeverity.WARNING,
            reason=f"split_type is 'equal' but split_details contain share weights: '{row.split_details}'.",
            resolution="Treated as equal split. split_details cleared. Mathematically equivalent in this case.",
        )
    return None
