import math
from collections import Counter
from typing import Any, Dict, List, Tuple

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
HIGH_RISK_CATEGORIES = {"malware", "security", "phishing"}
MIN_AI_DATASET_SIZE = 30
MAX_AI_FINDINGS = 25


def _normalize_category(value: str) -> str:
    return (value or "").strip().lower()


def _contains_keyword(destination: str, keywords: Tuple[str, ...]) -> bool:
    destination_lower = (destination or "").lower()
    return any(keyword in destination_lower for keyword in keywords)


def _build_feature_matrix(events: List[Dict[str, Any]]) -> List[List[float]]:
    source_counts = Counter((event.get("source_ip") or "unknown") for event in events)
    user_counts = Counter((event.get("username") or "unknown") for event in events)
    destination_counts = Counter((event.get("destination") or "unknown") for event in events)
    total = max(len(events), 1)

    features: List[List[float]] = []
    for event in events:
        action = (event.get("action") or "").upper()
        category = _normalize_category(event.get("category") or "")
        destination = event.get("destination") or ""
        source_ip = event.get("source_ip") or "unknown"
        username = event.get("username") or "unknown"
        event_time = event.get("event_time")
        bytes_transferred = max(0, int(event.get("bytes_transferred") or 0))

        allow_action = 1.0 if action == "ALLOW" else 0.0
        block_action = 1.0 if action == "BLOCK" else 0.0
        suspicious_destination = 1.0 if _contains_keyword(destination, SUSPICIOUS_DOMAIN_KEYWORDS) else 0.0
        high_value_destination = 1.0 if _contains_keyword(destination, HIGH_VALUE_DESTINATION_KEYWORDS) else 0.0
        high_risk_category = 1.0 if category in HIGH_RISK_CATEGORIES else 0.0
        zero_byte_allow = 1.0 if allow_action and bytes_transferred == 0 else 0.0
        hour_of_day = float(event_time.hour) if hasattr(event_time, "hour") else 0.0

        features.append(
            [
                math.log1p(bytes_transferred),
                allow_action,
                block_action,
                suspicious_destination,
                high_value_destination,
                high_risk_category,
                zero_byte_allow,
                hour_of_day / 23.0 if hour_of_day > 0 else 0.0,
                source_counts[source_ip] / total,
                user_counts[username] / total,
                destination_counts[destination] / total,
            ]
        )

    return features


def _explanation_for_event(event: Dict[str, Any]) -> str:
    action = (event.get("action") or "UNKNOWN").upper()
    destination = event.get("destination") or "unknown_destination"
    source_ip = event.get("source_ip") or "unknown_ip"
    category = event.get("category") or "unknown"
    bytes_transferred = int(event.get("bytes_transferred") or 0)

    signals: List[str] = []
    if _contains_keyword(destination, HIGH_VALUE_DESTINATION_KEYWORDS):
        signals.append("high-risk destination pattern")
    elif _contains_keyword(destination, SUSPICIOUS_DOMAIN_KEYWORDS):
        signals.append("suspicious destination keyword")

    if bytes_transferred >= 50_000_000:
        signals.append("large transfer volume")
    elif bytes_transferred == 0 and action == "ALLOW":
        signals.append("zero-byte allowed request")

    if _normalize_category(category) in HIGH_RISK_CATEGORIES:
        signals.append(f"high-risk category ({category})")

    if not signals:
        signals.append("behavioral outlier pattern")

    return (
        f"Isolation Forest flagged a behavioral outlier for {source_ip} -> {destination} "
        f"(action={action}, bytes={bytes_transferred}, category={category}). Signals: {', '.join(signals)}."
    )


def detect_ai_anomalies(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    notes: List[str] = []
    anomalies: List[Dict[str, Any]] = []

    if len(events) < MIN_AI_DATASET_SIZE:
        notes.append(
            "Skipped AI anomaly model (Isolation Forest): "
            f"dataset size ({len(events)}) below minimum ({MIN_AI_DATASET_SIZE})."
        )
        return {"anomalies": anomalies, "notes": notes}

    try:
        from sklearn.ensemble import IsolationForest
    except Exception as exc:  # pragma: no cover - dependency/runtime environment variance
        notes.append(f"Skipped AI anomaly model: scikit-learn unavailable ({exc}).")
        return {"anomalies": anomalies, "notes": notes}

    contamination = min(0.15, max(0.03, 8 / len(events)))
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
    )

    features = _build_feature_matrix(events)
    predictions = model.fit_predict(features)
    decision_scores = model.decision_function(features)

    findings_with_score: List[Tuple[int, float]] = []
    for idx, prediction in enumerate(predictions):
        if prediction == -1:
            anomaly_strength = max(0.0, -float(decision_scores[idx]))
            findings_with_score.append((idx, anomaly_strength))

    findings_with_score.sort(key=lambda item: item[1], reverse=True)
    findings_with_score = findings_with_score[:MAX_AI_FINDINGS]

    for event_index, anomaly_strength in findings_with_score:
        event = events[event_index]
        destination = event.get("destination") or ""
        category = _normalize_category(event.get("category") or "")
        bytes_transferred = int(event.get("bytes_transferred") or 0)
        allow_action = (event.get("action") or "").upper() == "ALLOW"
        explanation = _explanation_for_event(event)

        confidence = confidence_from_signals(
            base=0.58,
            boosts=[
                min(0.2, anomaly_strength * 4.0),
                0.05 if _contains_keyword(destination, SUSPICIOUS_DOMAIN_KEYWORDS) else 0.0,
                0.05 if category in HIGH_RISK_CATEGORIES else 0.0,
                0.05 if bytes_transferred >= 50_000_000 else 0.0,
                0.03 if allow_action and bytes_transferred == 0 else 0.0,
            ],
        )

        anomalies.append(
            {
                "event_index": event_index,
                "affectedLines": [event_index + 1],
                "detectionMethod": "ai_isolation_forest",
                "type": "ai_behavioral_outlier",
                "anomaly_type": "ai_behavioral_outlier",
                "severity": severity_from_confidence(confidence),
                "confidence": confidence,
                "explanation": explanation,
                "description": explanation,
                "aiModel": "IsolationForest",
            }
        )

    notes.append(
        f"AI anomaly model executed (Isolation Forest, contamination={round(contamination, 3)}), "
        f"produced {len(anomalies)} finding(s)."
    )
    return {"anomalies": anomalies, "notes": notes}
