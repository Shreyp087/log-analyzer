import csv
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


def _meaningful_lines(lines: Iterable[str]) -> List[Tuple[int, str]]:
    cleaned: List[Tuple[int, str]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = (raw_line or "").lstrip("\ufeff").rstrip("\n")
        if not line.strip():
            continue
        if line.strip().startswith("#"):
            continue
        cleaned.append((line_number, line))
    return cleaned


def _normalize_csv_action(method: Optional[str], status: Optional[int]) -> Optional[str]:
    if status is not None:
        if status >= 400:
            return "BLOCK"
        return "ALLOW"
    if method:
        return "ALLOW"
    return None


def _normalize_csv_category(status: Optional[int]) -> str:
    if status is None:
        return "Business"
    if status in {401, 403}:
        return "Security"
    if status >= 500:
        return "Server_Error"
    if status >= 400:
        return "Client_Error"
    return "Business"


def _normalize_csv_destination(row: Dict[str, str]) -> Optional[str]:
    destination = clean_text(row.get("destination")) or clean_text(row.get("url"))
    if destination:
        return destination

    destination_ip = clean_text(row.get("destination_ip"))
    path = clean_text(row.get("path"))
    if destination_ip and path:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"https://{destination_ip}{path}"
    if path:
        return path
    return destination_ip


def _parse_csv_lines(lines: Iterable[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    rows = _meaningful_lines(lines)
    if not rows:
        return events, errors

    header_line_number, header_line = rows[0]
    header = next(csv.reader([header_line]))
    header = [h.strip().lower() for h in header]
    if not header:
        errors.append(
            {
                "line_number": header_line_number,
                "error": "invalid csv header",
                "raw_line": header_line,
            }
        )
        return events, errors

    for line_number, raw_line in rows[1:]:
        try:
            values = next(csv.reader([raw_line]))
            row = {header[i]: values[i].strip() if i < len(values) else "" for i in range(len(header))}

            event_time = parse_timestamp(row.get("timestamp"))
            if event_time is None:
                raise ValueError("invalid timestamp")

            status = parse_int(row.get("status"))
            method = clean_text(row.get("method"))
            action = normalize_action(row.get("action")) or _normalize_csv_action(method, status)
            category = clean_text(row.get("category")) or _normalize_csv_category(status)
            bytes_value = (
                parse_int(row.get("bytes_transferred"))
                or parse_int(row.get("bytes"))
                or parse_int(row.get("response_bytes"))
                or 0
            )

            events.append(
                {
                    "event_time": event_time,
                    "username": clean_text(row.get("username")) or clean_text(row.get("user")),
                    "source_ip": clean_text(row.get("source_ip")) or clean_text(row.get("src_ip")),
                    "destination": _normalize_csv_destination(row),
                    "action": action,
                    "category": category,
                    "bytes_transferred": bytes_value,
                    "raw_line": raw_line,
                }
            )
        except ValueError as exc:
            errors.append(
                {
                    "line_number": line_number,
                    "error": str(exc),
                    "raw_line": raw_line,
                }
            )

    return events, errors


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
    row_list = list(lines)
    meaningful = _meaningful_lines(row_list)
    if not meaningful:
        return [], []

    first_data_line = meaningful[0][1]
    looks_like_csv = "," in first_data_line and not _ZSCALER_LINE_RE.match(first_data_line.strip())
    if looks_like_csv:
        return _parse_csv_lines(row_list)

    events: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for line_number, raw_line in enumerate(row_list, start=1):
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
