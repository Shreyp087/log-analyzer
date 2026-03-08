import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a SOC analyst. Given a single security anomaly, identify the likely attack pattern, "
    "the relevant MITRE ATT&CK technique ID and name, and one specific containment action. "
    "Be concise. Respond only in JSON. "
    "Return this exact JSON shape: "
    '{"attackPattern":"...","mitreId":"...","mitreName":"...","containmentStep":"..."}'
)


def _pick(payload: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _sanitize_enrichment(payload: Any) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    if not isinstance(payload, dict):
        return None, "eligible_invalid_response"

    attack_pattern = _pick(
        payload,
        [
            "attackPattern",
            "attack_pattern",
            "pattern",
            "likelyAttackPattern",
        ],
    )
    mitre_id = _pick(payload, ["mitreId", "mitreID", "mitre_id", "techniqueId", "technique_id"])
    mitre_name = _pick(payload, ["mitreName", "mitre_name", "techniqueName", "technique_name"])
    containment_step = _pick(payload, ["containmentStep", "containment_step", "containment", "action"])

    if not attack_pattern or not mitre_id or not mitre_name or not containment_step:
        return None, "eligible_invalid_response"

    return (
        {
            "attackPattern": attack_pattern,
            "mitreId": mitre_id,
            "mitreName": mitre_name,
            "containmentStep": containment_step,
        },
        "enriched",
    )


def _enrich_one(
    *,
    api_key: str,
    model: str,
    input_payload: Dict[str, Any],
) -> Tuple[Optional[Dict[str, str]], str]:
    if OpenAI is None:
        return None, "eligible_openai_unavailable"

    try:
        openai = OpenAI(api_key=api_key)
        completion = openai.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(input_payload)},
            ],
            max_tokens=220,
            temperature=0.2,
        )
        content = completion.choices[0].message.content if completion.choices else None
        result = json.loads(content) if content else {}
        enrichment, status = _sanitize_enrichment(result)
        return enrichment, status or "eligible_invalid_response"
    except Exception as err:
        logger.error("Per-anomaly AI enrichment failed for payload=%s reason=%s", input_payload, err)
        return None, "eligible_model_error"


def enrich_high_priority_anomalies(
    anomaly_inputs: List[Dict[str, Any]],
) -> Dict[str, Dict[int, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    targets = [
        item
        for item in anomaly_inputs
        if str(item.get("severity") or "").upper() in {"HIGH", "CRITICAL"}
    ]
    if not targets:
        return {"enriched_by_index": {}, "status_by_index": {}}

    enriched_by_index: Dict[int, Dict[str, str]] = {}
    status_by_index: Dict[int, str] = {}

    if not api_key:
        for target in targets:
            anomaly_index = int(target.get("anomaly_index", -1))
            if anomaly_index >= 0:
                status_by_index[anomaly_index] = "eligible_no_api_key"
        return {"enriched_by_index": enriched_by_index, "status_by_index": status_by_index}

    if OpenAI is None:
        for target in targets:
            anomaly_index = int(target.get("anomaly_index", -1))
            if anomaly_index >= 0:
                status_by_index[anomaly_index] = "eligible_openai_unavailable"
        return {"enriched_by_index": enriched_by_index, "status_by_index": status_by_index}

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    max_workers = min(6, len(targets))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for target in targets:
            anomaly_index = int(target.get("anomaly_index", -1))
            input_payload = {
                "anomalyType": target.get("anomalyType"),
                "entity": target.get("entity"),
                "destination": target.get("destination"),
                "bytesTransferred": target.get("bytesTransferred"),
                "action": target.get("action"),
                "category": target.get("category"),
                "timestamp": target.get("timestamp"),
            }
            future = executor.submit(
                _enrich_one,
                api_key=api_key,
                model=model,
                input_payload=input_payload,
            )
            future_map[future] = anomaly_index

        for future in as_completed(future_map):
            anomaly_index = future_map[future]
            if anomaly_index < 0:
                continue
            enrichment, status = future.result()
            status_by_index[anomaly_index] = status
            if enrichment is not None:
                enriched_by_index[anomaly_index] = enrichment

    return {"enriched_by_index": enriched_by_index, "status_by_index": status_by_index}
