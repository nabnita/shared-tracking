"""
Import report builder.
Aggregates RowDecision results into a structured machine-readable report dict.
"""
import json
from collections import Counter
from datetime import datetime, timezone

from app.models.models import AnomalyCategory, AnomalySeverity, ExpenseStatus
from app.services.anomaly.detector import RowDecision


def build_report(
    filename: str,
    decisions: list[RowDecision],
    import_id: str,
) -> dict:
    """
    Build the full import report as a plain dict (serializable to JSON).

    Structure:
    - summary: high-level counts
    - anomaly_breakdown: counts by category and severity
    - row_actions: what happened to each row
    """
    imported = [d for d in decisions if not d.should_reject and not d.has_warnings]
    warnings = [d for d in decisions if not d.should_reject and d.has_warnings]
    rejected = [d for d in decisions if d.should_reject]

    anomaly_by_severity: Counter = Counter()
    anomaly_by_category: Counter = Counter()
    for decision in decisions:
        for anomaly in decision.anomalies:
            anomaly_by_severity[anomaly.severity.value] += 1
            anomaly_by_category[anomaly.category.value] += 1

    row_actions = []
    for decision in decisions:
        if decision.should_reject:
            action = "REJECTED"
            reason = (
                f"Duplicate of row {decision.is_duplicate_of}"
                if decision.is_duplicate_of
                else "One or more ERROR anomalies"
            )
        elif decision.has_warnings:
            action = "IMPORTED_WITH_WARNINGS"
            reason = f"{len(decision.anomalies)} anomaly/anomalies detected"
        else:
            action = "IMPORTED"
            reason = "No anomalies detected"

        row_actions.append({
            "row": decision.row.row_number,
            "action": action,
            "reason": reason,
            "anomalies": [
                {
                    "category": a.category.value,
                    "severity": a.severity.value,
                    "reason": a.reason,
                    "resolution": a.resolution,
                }
                for a in decision.anomalies
            ],
        })

    return {
        "import_id": import_id,
        "filename": filename,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_rows": len(decisions),
            "imported": len(imported),
            "imported_with_warnings": len(warnings),
            "rejected": len(rejected),
            "total_anomalies": sum(len(d.anomalies) for d in decisions),
        },
        "anomaly_breakdown": {
            "by_severity": dict(anomaly_by_severity),
            "by_category": dict(anomaly_by_category),
        },
        "row_actions": row_actions,
    }
