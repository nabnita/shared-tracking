"""
Unknown participant detector.
Checks participants against a known-user registry and flags unrecognized names.
"""
from app.models.models import AnomalyCategory, AnomalySeverity
from app.services.ingestion.validator import ValidationIssue
from app.services.normalization.normalizer import NormalizedRow

# Known guests or informal name patterns that signal an unknown participant
GUEST_SIGNALS = ("friend", "cousin", "colleague", "guest", "visitor", "colleague")


def check_unknown_participants(
    row: NormalizedRow,
    known_names: set[str],
) -> list[ValidationIssue]:
    """
    Flag participants whose normalized name is not in known_names.
    known_names is built from all paid_by values across the import batch —
    anyone who has paid is assumed to be a known participant.
    """
    issues: list[ValidationIssue] = []

    for participant in row.split_with:
        lowered = participant.lower()
        if participant not in known_names:
            is_guest = any(signal in lowered for signal in GUEST_SIGNALS)
            issues.append(ValidationIssue(
                category=AnomalyCategory.UNKNOWN_PARTICIPANT,
                severity=AnomalySeverity.WARNING,
                reason=f"Participant '{participant}' is not a recognized user in this import.",
                resolution=(
                    f"Created as a guest user (is_guest=True)."
                    if is_guest
                    else f"Created as a new user. Verify this is intentional."
                ),
            ))

    return issues


def check_stale_participant(
    row: NormalizedRow,
    departed_users: dict[str, str],  # normalized_name → departure note
) -> list[ValidationIssue]:
    """
    Flag participants who have been recorded as having left the group.
    departed_users is populated externally (e.g., from notes analysis).
    """
    issues: list[ValidationIssue] = []
    for participant in row.split_with:
        if participant in departed_users:
            issues.append(ValidationIssue(
                category=AnomalyCategory.STALE_PARTICIPANT,
                severity=AnomalySeverity.WARNING,
                reason=f"Participant '{participant}' appears to have left the group ({departed_users[participant]}) but is still listed in split_with.",
                resolution="Imported as-is. Verify whether this participant should be included.",
            ))
    return issues
