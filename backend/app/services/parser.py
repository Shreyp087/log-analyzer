import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.services.normalizer import (
    clean_text,
    normalize_action,
    parse_int,
    parse_timestamp,
)

_ZSCALER_LINE_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+"
    r"(?P<username>\S+)\s+"
    r"(?P<source_ip>\S+)\s+"
    r"(?P<destination>\S+)\s+"
    r"(?P<action>\S+)\s+"
    r"(?P<category>.+)\s+"
    r"(?P<bytes_transferred>\S+)$"
)


def parse_zscaler_line(raw_line: str) -> Optional[Dict[str, Any]]:
    if raw_line is None:
        return None

    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    match = _ZSCALER_LINE_RE.match(line)
    if not match:
        raise ValueError("invalid zscaler row format")

    row = match.groupdict()
    normalized = {
        "event_time": parse_timestamp(row.get("timestamp")),
        "username": clean_text(row.get("username")),
        "source_ip": clean_text(row.get("source_ip")),
        "destination": clean_text(row.get("destination")),
        "action": normalize_action(row.get("action")),
        "category": clean_text(row.get("category")),
        "bytes_transferred": parse_int(row.get("bytes_transferred")),
        "raw_line": line,
    }

    if normalized["event_time"] is None:
        raise ValueError("invalid timestamp")
    if normalized["bytes_transferred"] is None:
        raise ValueError("invalid bytes_transferred")

    return normalized


def parse_zscaler_lines(lines: Iterable[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for line_number, raw_line in enumerate(lines, start=1):
        try:
            parsed = parse_zscaler_line(raw_line)
            if parsed is not None:
                events.append(parsed)
        except ValueError as exc:
            errors.append(
                {
                    "line_number": line_number,
                    "error": str(exc),
                    "raw_line": (raw_line or "").rstrip("\n"),
                }
            )

    return events, errors
