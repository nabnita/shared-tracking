"""
Normalization layer: transforms raw CSV strings into clean, typed values.
Every transformation is recorded in a TransformationLog for full traceability.
"""
import re
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from dateutil import parser as dateutil_parser

from app.services.ingestion.parser import ParsedRow

logger = logging.getLogger(__name__)

# Canonical mapping for known name variants → normalized form
NAME_ALIASES: dict[str, str] = {
    "priya s": "priya",
    "rohan ": "rohan",  # trailing space variant (stripped before lookup anyway)
    "dev's friend kabir": "kabir",
}


@dataclass
class Transformation:
    field: str
    original: str
    normalized: str
    reason: str


@dataclass
class NormalizedRow:
    row_number: int
    paid_by: str | None
    description: str
    amount: Decimal | None
    currency: str | None
    split_type: str | None
    split_with: list[str]           # Normalized participant name list
    split_details: str
    notes: str
    expense_date: date | None
    transformations: list[Transformation] = field(default_factory=list)
    # Preserved raw dict for audit
    raw: dict[str, str] = field(default_factory=dict)


def normalize_row(row: ParsedRow, import_currency_default: str = "INR") -> NormalizedRow:
    """
    Normalize a single ParsedRow into typed, clean values.
    All changes are logged in NormalizedRow.transformations.
    """
    t: list[Transformation] = []
    raw = row.raw

    paid_by = _normalize_name(raw.get("paid_by", ""), "paid_by", t) or None
    description = _normalize_description(raw.get("description", ""), t)
    amount = _normalize_amount(raw.get("amount", ""), t)
    currency = _normalize_currency(raw.get("currency", ""), import_currency_default, t)
    split_type = _normalize_split_type(raw.get("split_type", ""), t)
    split_with = _normalize_split_with(raw.get("split_with", ""), t)
    expense_date = _normalize_date(raw.get("date", ""), t)
    split_details = raw.get("split_details", "").strip()
    notes = raw.get("notes", "").strip()

    return NormalizedRow(
        row_number=row.row_number,
        paid_by=paid_by,
        description=description,
        amount=amount,
        currency=currency,
        split_type=split_type,
        split_with=split_with,
        split_details=split_details,
        notes=notes,
        expense_date=expense_date,
        transformations=t,
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Field-level normalizers
# ---------------------------------------------------------------------------

def _normalize_name(raw: str, field_name: str, log: list[Transformation]) -> str:
    if not raw:
        return ""
    stripped = raw.strip()
    lowered = stripped.lower()

    # Check alias table first (handles "Priya S", "Dev's friend Kabir", etc.)
    if lowered in NAME_ALIASES:
        canonical = NAME_ALIASES[lowered].title()
        if canonical.lower() != lowered:
            log.append(Transformation(
                field=field_name,
                original=raw,
                normalized=canonical,
                reason=f"Name alias resolved: '{stripped}' → '{canonical}'",
            ))
        return canonical

    # Title-case and whitespace normalization
    normalized = " ".join(stripped.title().split())
    if normalized != stripped:
        log.append(Transformation(
            field=field_name,
            original=raw,
            normalized=normalized,
            reason=f"Whitespace/case normalized: '{stripped}' → '{normalized}'",
        ))
    return normalized


def _normalize_description(raw: str, log: list[Transformation]) -> str:
    normalized = " ".join(raw.strip().split())
    if not normalized:
        normalized = "(no description)"
        log.append(Transformation(
            field="description",
            original=raw,
            normalized=normalized,
            reason="Description was empty — set to placeholder.",
        ))
    return normalized


def _normalize_amount(raw: str, log: list[Transformation]) -> Decimal | None:
    if not raw.strip():
        return None

    cleaned = raw.replace(",", "").strip()

    # Record comma removal
    if "," in raw:
        log.append(Transformation(
            field="amount",
            original=raw,
            normalized=cleaned,
            reason="Removed thousands separator comma from amount.",
        ))

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None

    # Round to 2dp
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded != amount:
        log.append(Transformation(
            field="amount",
            original=str(amount),
            normalized=str(rounded),
            reason=f"Rounded to 2 decimal places ({amount} → {rounded}).",
        ))
    return rounded


def _normalize_currency(raw: str, default: str, log: list[Transformation]) -> str | None:
    stripped = raw.strip().upper()
    if not stripped:
        log.append(Transformation(
            field="currency",
            original=raw,
            normalized=default,
            reason=f"Currency missing — inferred '{default}' from import context.",
        ))
        return default
    if stripped != raw.strip():
        log.append(Transformation(
            field="currency",
            original=raw,
            normalized=stripped,
            reason="Currency uppercased.",
        ))
    return stripped


def _normalize_split_type(raw: str, log: list[Transformation]) -> str | None:
    stripped = raw.strip().lower()
    if not stripped:
        return None
    if stripped != raw.strip():
        log.append(Transformation(
            field="split_type",
            original=raw,
            normalized=stripped,
            reason="split_type lowercased.",
        ))
    return stripped


def _normalize_split_with(raw: str, log: list[Transformation]) -> list[str]:
    """Parse semicolon-separated participant list and normalize each name."""
    if not raw.strip():
        return []
    participants = [p.strip() for p in raw.split(";") if p.strip()]
    normalized = []
    dummy_log: list[Transformation] = []
    for p in participants:
        normalized.append(_normalize_name(p, "split_with", dummy_log))
    # Surface only meaningful transformations
    for t in dummy_log:
        if t.original != t.normalized:
            log.append(Transformation(
                field="split_with",
                original=t.original,
                normalized=t.normalized,
                reason=t.reason,
            ))
    return normalized


def _normalize_date(raw: str, log: list[Transformation]) -> date | None:
    """
    Parse dates with dateutil fallback for non-standard formats.
    The dominant format in this dataset is DD-MM-YYYY (dayfirst=True).
    """
    stripped = raw.strip()
    if not stripped:
        return None

    # Try strict DD-MM-YYYY first
    try:
        parsed = dateutil_parser.parse(stripped, dayfirst=True)
        normalized = parsed.date()
        return normalized
    except Exception:
        pass

    # Fallback: try without dayfirst (handles "Mar-14" month-day style)
    try:
        parsed = dateutil_parser.parse(stripped, dayfirst=False)
        normalized = parsed.date()
        log.append(Transformation(
            field="date",
            original=raw,
            normalized=str(normalized),
            reason=f"Non-standard date format '{stripped}' parsed with fallback strategy.",
        ))
        return normalized
    except Exception:
        log.append(Transformation(
            field="date",
            original=raw,
            normalized="NULL",
            reason=f"Date '{stripped}' could not be parsed — stored as NULL.",
        ))
        return None
