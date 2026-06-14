"""
CSV parser: safely reads an uploaded CSV and returns raw row dicts.
All errors are captured per-row rather than aborting the entire import.
"""
import csv
import io
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {
    "date", "description", "paid_by", "amount",
    "currency", "split_type", "split_with", "split_details", "notes",
}


@dataclass
class ParsedRow:
    row_number: int          # 1-indexed, excluding header
    raw: dict[str, str]      # Original values from CSV
    parse_error: str | None = None  # Set if the row itself is malformed


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)
    total_rows: int = 0


def parse_csv(file_contents: bytes, filename: str) -> ParseResult:
    """
    Parse raw CSV bytes into ParsedRow objects.

    Strategy:
    - Decode as UTF-8 with replacement for malformed bytes.
    - Detect and report missing/extra columns vs. expected schema.
    - Each row is captured individually; a malformed row does not abort parsing.
    """
    result = ParseResult()

    try:
        text = file_contents.decode("utf-8-sig", errors="replace")
    except Exception as exc:
        logger.error("Failed to decode CSV file %s: %s", filename, exc)
        result.rows.append(ParsedRow(
            row_number=0,
            raw={},
            parse_error=f"File decode error: {exc}",
        ))
        return result

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        result.rows.append(ParsedRow(row_number=0, raw={}, parse_error="Empty or unreadable CSV"))
        return result

    actual_columns = {col.strip().lower() for col in reader.fieldnames if col}
    result.missing_columns = list(EXPECTED_COLUMNS - actual_columns)
    result.extra_columns = list(actual_columns - EXPECTED_COLUMNS)

    for row_number, raw_row in enumerate(reader, start=1):
        # Strip keys — DictReader uses the exact header string
        cleaned = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items() if k}

        result.rows.append(ParsedRow(
            row_number=row_number,
            raw=cleaned,
        ))

    result.total_rows = len(result.rows)
    return result
