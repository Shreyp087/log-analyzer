from datetime import datetime
from typing import Optional

NULL_MARKERS = {"", "null", "none", "na", "n/a", "-"}


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    cleaned = value.strip()
    if cleaned.lower() in NULL_MARKERS:
        return None
    return cleaned


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def parse_int(value: Optional[str]) -> Optional[int]:
    cleaned = clean_text(value)
    if cleaned is None:
        return None

    try:
        return int(cleaned)
    except ValueError:
        return None


def normalize_action(value: Optional[str]) -> Optional[str]:
    cleaned = clean_text(value)
    if cleaned is None:
        return None
    return cleaned.upper()
