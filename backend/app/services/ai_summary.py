import json
import logging
import os
from typing import Any, Dict, List

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a SOC analyst writing an operator-friendly executive briefing. "
    "Use clear, human-readable language with short sentences. "
    "Be specific: reference real users, IPs, destinations, and anomaly types from the input. "
    "Avoid generic filler and avoid repeating dashboard card numbers verbatim. "
    "Respond ONLY with valid JSON, no markdown, no explanation. "
    "Return this JSON shape exactly: "
    "{"
    '"riskLevel":"CRITICAL | HIGH | MEDIUM | LOW",'
    '"executiveSummary":"One specific paragraph, max 2 sentences, naming real entities from the data",'
    '"keyFindings":["specific finding with real IP/user/destination - no generic text","specific finding 2","specific finding 3"],'
    '"recommendations":["specific action referencing a real entity from the data","specific action 2"],'
    '"immediateActions":["specific urgent action if riskLevel is HIGH or CRITICAL, naming the specific threat actor/destination"]'
    "}"
)

DETECTION_NOTES_PROMPT = (
    "You are a SOC analyst assistant. Convert detection engine notes into concise WHAT and WHY items. "
    "Respond ONLY with valid JSON and this exact shape: "
    "{"
    '"overview":"1-2 sentence summary of detector behavior for this upload",'
    '"entries":[{"what":"What happened","why":"Why it happened"}]'
    "}"
)


def _normalize_risk_level(value: Any) -> str:
    normalized = str(value or "").upper()
    if normalized in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
        return normalized
    return "LOW"


def _normalize_list(value: Any, limit: int) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()][:limit]


def _trim_text(value: Any, max_length: int = 150) -> str:
    text = str(value or "").strip()
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."


def _contains_keyword(value: str, keywords: List[str]) -> bool:
    text = (value or "").lower()
    return any(keyword in text for keyword in keywords)


def _count_threats(anomalies: List[Dict[str, Any]]) -> int:
    threat_types = {
        "suspicious_destination",
        "threat_signature",
        "policy_violation",
        "data_exfiltration",
    }
    count = 0
    for anomaly in anomalies:
        anomaly_type = str(anomaly.get("type") or "").lower()
        if anomaly_type in threat_types:
            count += 1
    return count


def _build_input_data(
    summary_metrics: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    blocked_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_events = int(summary_metrics.get("total_events", 0) or 0)
    blocked_count = int(summary_metrics.get("blocked_events", 0) or 0)
    block_rate = f"{round((blocked_count / total_events) * 100) if total_events > 0 else 0}%"
    threat_signals = _count_threats(anomalies)

    structured_anomalies = []
    for anomaly in anomalies[:25]:
        severity = str(anomaly.get("severity") or "medium").upper()
        raw_confidence = anomaly.get("confidence")
        if isinstance(raw_confidence, (int, float)):
            confidence = f"{round(float(raw_confidence) * 100)}%"
        else:
            confidence = str(raw_confidence or "")

        structured_anomalies.append(
            {
                "row": int(anomaly.get("row") or anomaly.get("event_row") or 0),
                "type": anomaly.get("type") or anomaly.get("anomaly_type") or "unknown",
                "severity": severity,
                "confidence": confidence,
                "entity": anomaly.get("entity") or "unknown/unknown",
                "detail": anomaly.get("detail")
                or anomaly.get("explanation")
                or anomaly.get("description")
                or "No detail provided.",
            }
        )

    structured_blocked = []
    for event in blocked_events[:25]:
        structured_blocked.append(
            {
                "user": event.get("user") or "unknown",
                "destination": event.get("destination") or "unknown",
                "category": event.get("category") or "Unknown",
            }
        )

    return {
        "summary": {
            "totalEvents": total_events,
            "blocked": blocked_count,
            "blockRate": block_rate,
            "anomalyCount": len(structured_anomalies),
            "threatSignals": threat_signals,
        },
        "anomalies": structured_anomalies,
        "blockedEvents": structured_blocked,
    }


def fallback_summary(
    anomalies: List[Dict[str, Any]],
    blocked_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    critical_anomalies = [
        anomaly for anomaly in anomalies if str(anomaly.get("severity") or "").lower() == "critical"
    ]
    high_anomalies = [
        anomaly for anomaly in anomalies if str(anomaly.get("severity") or "").lower() == "high"
    ]

    risk_level = (
        "CRITICAL"
        if critical_anomalies
        else "HIGH"
        if len(high_anomalies) > 2
        else "MEDIUM"
        if anomalies
        else "LOW"
    )

    primary = critical_anomalies[0] if critical_anomalies else (high_anomalies[0] if high_anomalies else None)
    if primary is None and anomalies:
        primary = anomalies[0]

    suspicious_blocked = [
        event
        for event in blocked_events
        if _contains_keyword(
            str(event.get("destination") or ""),
            ["c2", "cnc", "botnet", "darkweb", "ransomware", "malicious", "phish", "tor"],
        )
        or str(event.get("category") or "").lower() in {"malware", "security", "phishing"}
    ]

    if primary:
        primary_detail = _trim_text(primary.get("detail"), max_length=160)
        primary_text = (
            f"Primary signal: row {primary.get('row')} {primary.get('type')} on "
            f"{primary.get('entity')} ({primary.get('confidence')}) - {primary_detail}."
        )
    else:
        primary_text = "No parser-level anomalies were produced for this upload."

    if suspicious_blocked:
        blocked = suspicious_blocked[0]
        secondary_text = (
            f"Blocked high-risk destination observed for {blocked.get('user')} -> "
            f"{blocked.get('destination')} (category={blocked.get('category')})."
        )
    elif blocked_events:
        blocked = blocked_events[0]
        secondary_text = (
            f"Blocked activity includes {blocked.get('user')} contacting {blocked.get('destination')}."
        )
    else:
        secondary_text = "No blocked destination attempts were captured in this upload."

    key_findings: List[str] = []
    if primary:
        key_findings.append(
            f"Row {primary.get('row')} {primary.get('type')} involved {primary.get('entity')} -> {primary.get('detail')}."
        )
    if suspicious_blocked:
        blocked = suspicious_blocked[0]
        key_findings.append(
            f"Blocked high-risk contact: {blocked.get('user')} -> {blocked.get('destination')} ({blocked.get('category')})."
        )
    if not key_findings:
        key_findings.append("No concrete anomaly rows were generated from this upload.")

    recommendations: List[str] = []
    if critical_anomalies:
        critical = critical_anomalies[0]
        recommendations.append(
            f"Isolate and triage endpoint tied to {critical.get('entity')} for CRITICAL {critical.get('type')}."
        )
    elif high_anomalies:
        high = high_anomalies[0]
        recommendations.append(
            f"Prioritize investigation of {high.get('entity')} for HIGH {high.get('type')} on row {high.get('row')}."
        )

    if suspicious_blocked:
        blocked = suspicious_blocked[0]
        recommendations.append(
            f"Correlate DNS, proxy, and endpoint telemetry for {blocked.get('user')} around {blocked.get('destination')}."
        )

    if not recommendations:
        recommendations.append("Continue monitoring with the current rule set and baseline thresholds.")

    immediate_actions: List[str] = []
    if risk_level == "CRITICAL":
        if critical_anomalies:
            critical = critical_anomalies[0]
            immediate_actions.append(
                f"Trigger IR escalation for {critical.get('entity')} tied to {critical.get('type')}."
            )
        else:
            immediate_actions.append("Trigger IR escalation for this upload due to CRITICAL risk.")

    return {
        "riskLevel": risk_level,
        "executiveSummary": f"{primary_text} {secondary_text}",
        "keyFindings": key_findings[:2],
        "recommendations": recommendations[:2],
        "immediateActions": immediate_actions,
    }


def _sanitize_summary(payload: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return fallback

    risk_level = _normalize_risk_level(payload.get("riskLevel", fallback["riskLevel"]))
    executive_summary = str(payload.get("executiveSummary") or fallback["executiveSummary"]).strip()
    key_findings = _normalize_list(payload.get("keyFindings"), limit=3) or fallback["keyFindings"]
    recommendations = (
        _normalize_list(payload.get("recommendations"), limit=2) or fallback["recommendations"]
    )
    immediate_actions = _normalize_list(payload.get("immediateActions"), limit=2)
    if risk_level != "CRITICAL":
        immediate_actions = []

    return {
        "riskLevel": risk_level,
        "executiveSummary": executive_summary,
        "keyFindings": key_findings[:3],
        "recommendations": recommendations[:2],
        "immediateActions": immediate_actions[:2],
    }


def _fallback_detection_notes_summary(detection_notes: List[str]) -> Dict[str, Any]:
    if not detection_notes:
        return {
            "overview": "No detection notes were generated for this upload.",
            "entries": [],
            "source": "fallback",
        }

    entries = []
    for note in detection_notes[:5]:
        note_clean = str(note).strip()
        note_lower = note_clean.lower()
        if note_lower.startswith("skipped"):
            what = note_clean.split(":", 1)[0].strip()
            why = note_clean.split(":", 1)[1].strip() if ":" in note_clean else "Detector guard conditions were not met."
        elif "executed" in note_lower and "produced" in note_lower:
            what = "AI anomaly detector executed for this upload."
            why = note_clean
        else:
            what = note_clean
            why = "Runtime detector note emitted by the analysis pipeline."

        entries.append({"what": what, "why": why})

    return {
        "overview": f"Detection pipeline emitted {len(detection_notes)} note(s) for this upload.",
        "entries": entries,
        "source": "fallback",
    }


def _sanitize_detection_notes_summary(payload: Any, fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return fallback

    overview = str(payload.get("overview") or fallback.get("overview") or "").strip()
    raw_entries = payload.get("entries")
    entries = []
    if isinstance(raw_entries, list):
        for item in raw_entries[:5]:
            if not isinstance(item, dict):
                continue
            what = str(item.get("what") or "").strip()
            why = str(item.get("why") or "").strip()
            if what and why:
                entries.append({"what": what, "why": why})

    if not entries:
        entries = fallback.get("entries", [])

    return {
        "overview": overview or fallback.get("overview", ""),
        "entries": entries,
        "source": "openai" if entries != fallback.get("entries", []) else fallback.get("source", "fallback"),
    }


def generate_detection_notes_summary(
    detection_notes: List[str],
    anomalies: List[Dict[str, Any]],
) -> Dict[str, Any]:
    fallback = _fallback_detection_notes_summary(detection_notes)
    if not detection_notes:
        return fallback

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return fallback

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    anomaly_context = [
        {
            "type": anomaly.get("type"),
            "severity": anomaly.get("severity"),
            "confidence": anomaly.get("confidence"),
            "row": anomaly.get("row"),
        }
        for anomaly in anomalies[:10]
    ]
    input_data = {
        "detectionNotes": detection_notes[:10],
        "anomalyContext": anomaly_context,
    }

    try:
        openai = OpenAI(api_key=api_key)
        completion = openai.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": DETECTION_NOTES_PROMPT},
                {"role": "user", "content": json.dumps(input_data)},
            ],
            max_tokens=350,
            temperature=0.2,
        )
        content = completion.choices[0].message.content if completion.choices else None
        result = json.loads(content) if content else {}
        return _sanitize_detection_notes_summary(result, fallback)
    except Exception as err:
        logger.error("Detection notes summary AI failed; using fallback. Reason: %s", err)
        return fallback


def generate_executive_summary(
    summary_metrics: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    blocked_events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    input_data = _build_input_data(summary_metrics, anomalies, blocked_events)
    fallback = fallback_summary(
        input_data.get("anomalies", []),
        input_data.get("blockedEvents", []),
    )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return fallback
    if OpenAI is None:
        return fallback

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    try:
        openai = OpenAI(api_key=api_key)
        completion = openai.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(input_data)},
            ],
            max_tokens=600,
            temperature=0.2,
        )
        content = completion.choices[0].message.content if completion.choices else None
        result = json.loads(content) if content else {}
        return _sanitize_summary(result, fallback)
    except Exception as err:
        logger.error("AI summary failed; using fallback. Reason: %s", err)
        return fallback
