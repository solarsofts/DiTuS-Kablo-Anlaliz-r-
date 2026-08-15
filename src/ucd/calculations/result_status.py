from __future__ import annotations

STATUS_SUITABLE = "UYGUN"
STATUS_UNSUITABLE = "UYGUN DEĞİL"
STATUS_INCOMPLETE = "HESAP EKSİK"
STATUS_FAILED = "BAŞARISIZ"


def is_suitable(status: str) -> bool:
    return str(status).strip().upper() == STATUS_SUITABLE


def is_unsuitable(status: str) -> bool:
    return str(status).strip().upper() in {
        STATUS_UNSUITABLE,
        "HESAP EKSİK — UYGUN DEĞİL",
        "BAŞARISIZ — UYGUN DEĞİL",
    }


def aggregate_binary_status(statuses: list[str] | tuple[str, ...]) -> str:
    """Aggregate legacy complete-result statuses without vacuous all(True)."""
    values = tuple(statuses)
    if not values:
        return STATUS_FAILED
    return STATUS_SUITABLE if all(is_suitable(value) for value in values) else STATUS_UNSUITABLE


def display_background(status: str) -> str:
    normalized = str(status).strip().upper()
    if normalized == STATUS_SUITABLE:
        return "#e5f4ea"
    if normalized.startswith(STATUS_INCOMPLETE):
        return "#fff4d6"
    if normalized.startswith(STATUS_FAILED):
        return "#e0e0e0"
    return "#fdecec"


def display_foreground(status: str) -> str:
    normalized = str(status).strip().upper()
    if normalized == STATUS_SUITABLE:
        return "#1d5f4a"
    if normalized.startswith(STATUS_INCOMPLETE):
        return "#9a6700"
    if normalized.startswith(STATUS_FAILED):
        return "#555555"
    return "#a43b3b"
