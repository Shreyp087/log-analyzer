from typing import Any, Dict, List

from app.services.scoring import confidence_from_signals, severity_from_confidence

SUSPICIOUS_DOMAIN_KEYWORDS = (
    "malicious",
    "phish",
    "command-and-control",
    "cnc",
    "tor",
    "darkweb",
)

HIGH_RISK_CATEGORIES = {"security", "malware", "phishing"}
EXCESSIVE_TRANSFER_BYTES = 50_000_000


def _contains_suspicious_keyword(destination: str) -> bool:
    dest_lower = destination.lower()
    return any(keyword in dest_lower for keyword in SUSPICIOUS_DOMAIN_KEYWORDS)


def detect_anomalies(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    anomalies: List[Dict[str, Any]] = []

    for event_index, event in enumerate(events):
        action = (event.get("action") or "").upper()
        destination = event.get("destination") or ""
        category = (event.get("category") or "").lower()
        bytes_transferred = event.get("bytes_transferred") or 0
        source_ip = event.get("source_ip") or "unknown"

        suspicious_destination = _contains_suspicious_keyword(destination)
        high_risk_category = category in HIGH_RISK_CATEGORIES

        if action == "BLOCK":
            confidence = confidence_from_signals(
                base=0.62,
                boosts=[
                    0.12 if suspicious_destination else 0.0,
                    0.1 if high_risk_category else 0.0,
                ],
            )
            anomalies.append(
                {
                    "event_index": event_index,
                    "anomaly_type": "blocked_request",
                    "severity": severity_from_confidence(confidence),
                    "confidence": confidence,
                    "description": (
                        f"Blocked request from {source_ip} to {destination} "
                        f"(category={category or 'unknown'})."
                    ),
                }
            )

        if suspicious_destination:
            confidence = confidence_from_signals(
                base=0.7,
                boosts=[0.12 if action == "BLOCK" else 0.0],
            )
            anomalies.append(
                {
                    "event_index": event_index,
                    "anomaly_type": "suspicious_destination",
                    "severity": severity_from_confidence(confidence),
                    "confidence": confidence,
                    "description": (
                        f"Destination appears suspicious based on threat-keyword match: "
                        f"{destination}."
                    ),
                }
            )

        if action in {"ALLOW", "PERMIT"} and bytes_transferred == 0:
            confidence = confidence_from_signals(base=0.55, boosts=[0.08])
            anomalies.append(
                {
                    "event_index": event_index,
                    "anomaly_type": "zero_byte_allowed_request",
                    "severity": severity_from_confidence(confidence),
                    "confidence": confidence,
                    "description": (
                        f"Allowed request from {source_ip} produced zero bytes, "
                        f"possible probing or failed transfer."
                    ),
                }
            )

        if bytes_transferred >= EXCESSIVE_TRANSFER_BYTES:
            confidence = confidence_from_signals(
                base=0.68,
                boosts=[0.1 if high_risk_category else 0.0, 0.08 if suspicious_destination else 0.0],
            )
            anomalies.append(
                {
                    "event_index": event_index,
                    "anomaly_type": "excessive_data_transfer",
                    "severity": severity_from_confidence(confidence),
                    "confidence": confidence,
                    "description": (
                        f"High transfer volume detected ({bytes_transferred} bytes) "
                        f"from {source_ip}."
                    ),
                }
            )

    return anomalies
