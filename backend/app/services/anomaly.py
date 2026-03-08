from typing import Any, Dict, List

from app.services.ai_anomaly import detect_ai_anomalies
from app.services.scoring import confidence_from_signals, severity_from_confidence

SUSPICIOUS_DOMAIN_KEYWORDS = (
    "malicious",
    "c2",
    "darkweb",
    "cnc",
    "phish",
    "tor",
    "ransomware",
)
HIGH_VALUE_DESTINATION_KEYWORDS = ("cnc", "c2", "botnet", "darkweb", "ransomware")

SAFE_ZERO_BYTE_CATEGORIES = {
    "internal",
    "business",
    "collaboration",
    "network_services",
}
HIGH_RISK_CATEGORIES = {"malware", "security", "phishing"}
EXCESSIVE_TRANSFER_BYTES = 50_000_000
MIN_STAT_BASELINE_SIZE = 20


def _normalize_category(value: str) -> str:
    return (value or "").strip().lower()


def _contains_suspicious_keyword(destination: str) -> bool:
    dest_lower = (destination or "").lower()
    return any(keyword in dest_lower for keyword in SUSPICIOUS_DOMAIN_KEYWORDS)


def _contains_high_value_keyword(destination: str) -> bool:
    dest_lower = (destination or "").lower()
    return any(keyword in dest_lower for keyword in HIGH_VALUE_DESTINATION_KEYWORDS)


def _build_anomaly(
    *,
    event_index: int,
    anomaly_type: str,
    severity: str,
    confidence: float,
    explanation: str,
    detection_method: str = "rule_engine",
) -> Dict[str, Any]:
    return {
        "event_index": event_index,
        "affectedLines": [event_index + 1],
        "detectionMethod": detection_method,
        "type": anomaly_type,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "confidence": confidence,
        "explanation": explanation,
        "description": explanation,
    }


def detect_anomalies(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    anomalies: List[Dict[str, Any]] = []
    notes: List[str] = []

    if len(events) < MIN_STAT_BASELINE_SIZE:
        notes.append(
            "Skipped HIGH_FREQUENCY and DATA_EXFILTRATION z-score detectors: "
            f"dataset size ({len(events)}) is below minimum baseline ({MIN_STAT_BASELINE_SIZE})."
        )

    for event_index, event in enumerate(events):
        action = (event.get("action") or "").upper()
        destination = event.get("destination") or ""
        category_raw = event.get("category") or ""
        category = _normalize_category(category_raw)
        bytes_transferred = event.get("bytes_transferred") or 0
        source_ip = event.get("source_ip") or "unknown"

        keyword_match = _contains_suspicious_keyword(destination)
        high_value_keyword_match = _contains_high_value_keyword(destination)
        allow_action = action == "ALLOW"
        data_exchanged = bytes_transferred > 0
        high_risk_category = category in HIGH_RISK_CATEGORIES
        signal_count = sum((keyword_match, allow_action, data_exchanged, high_risk_category))
        high_value_destination = category == "malware" or high_value_keyword_match

        # High-value C2/malware signal: alert even if BLOCKED because the contact attempt itself matters.
        if high_value_destination:
            confidence = confidence_from_signals(
                base=0.82,
                boosts=[0.04 if allow_action else 0.0, 0.04 if data_exchanged else 0.0],
            )
            anomalies.append(
                _build_anomaly(
                    event_index=event_index,
                    anomaly_type="suspicious_destination",
                    severity="high",
                    confidence=confidence,
                    explanation=(
                        f"High-value suspicious destination contact attempt ({action or 'UNKNOWN'}) from {source_ip} "
                        f"to {destination} (category={category_raw or 'unknown'})."
                    ),
                )
            )

        # Precision-first suspicious destination logic for non-high-value destinations:
        # requires suspicious keyword + ALLOW action + at least one additional corroborating signal.
        elif keyword_match and allow_action and signal_count >= 2:
            confidence = confidence_from_signals(base=0.64, boosts=[0.08 * (signal_count - 2)])
            anomalies.append(
                _build_anomaly(
                    event_index=event_index,
                    anomaly_type="suspicious_destination",
                    severity="medium",
                    confidence=confidence,
                    explanation=(
                        f"Suspicious destination from {source_ip} matched {signal_count}/4 signals "
                        f"(allow={allow_action}, bytes={bytes_transferred}, category={category_raw or 'unknown'}): "
                        f"{destination}."
                    ),
                )
            )

        # Zero-byte allowed request is only suspicious when all requested constraints hold.
        safe_zero_byte_category = category in SAFE_ZERO_BYTE_CATEGORIES
        if allow_action and bytes_transferred == 0 and (not safe_zero_byte_category) and keyword_match:
            confidence = confidence_from_signals(base=0.7, boosts=[0.08 if high_risk_category else 0.0])
            anomalies.append(
                _build_anomaly(
                    event_index=event_index,
                    anomaly_type="zero_byte_allowed_request",
                    severity=severity_from_confidence(confidence),
                    confidence=confidence,
                    explanation=(
                        f"Allowed zero-byte request from {source_ip} to suspicious destination {destination} "
                        f"(category={category_raw or 'unknown'})."
                    ),
                )
            )

        if bytes_transferred >= EXCESSIVE_TRANSFER_BYTES:
            confidence = confidence_from_signals(
                base=0.68,
                boosts=[0.1 if high_risk_category else 0.0, 0.08 if keyword_match else 0.0],
            )
            anomalies.append(
                _build_anomaly(
                    event_index=event_index,
                    anomaly_type="excessive_data_transfer",
                    severity=severity_from_confidence(confidence),
                    confidence=confidence,
                    explanation=(
                        f"High transfer volume detected ({bytes_transferred} bytes) from {source_ip} "
                        f"to {destination}."
                    ),
                )
            )

    ai_detection_result = detect_ai_anomalies(events)
    ai_anomalies = ai_detection_result.get("anomalies", [])
    ai_notes = ai_detection_result.get("notes", [])

    if ai_anomalies:
        existing_keys = {(item.get("event_index"), item.get("type")) for item in anomalies}
        for ai_anomaly in ai_anomalies:
            anomaly_key = (ai_anomaly.get("event_index"), ai_anomaly.get("type"))
            if anomaly_key not in existing_keys:
                anomalies.append(ai_anomaly)

    notes.extend(ai_notes)
    return {"anomalies": anomalies, "notes": notes}
