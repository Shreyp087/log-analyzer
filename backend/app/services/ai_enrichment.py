import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "You are a SOC analyst. Given a single security anomaly, identify the likely attack pattern, "
    "the relevant MITRE ATT&CK technique ID and name, and one specific containment action. "
    "Be concise. Respond only in JSON."
)


def _sanitize_enrichment(payload: Any) -> Optional[Dict[str, str]]:
    if not isinstance(payload, dict):
        return None

    attack_pattern = str(payload.get("attackPattern") or "").strip()
    mitre_id = str(payload.get("mitreId") or "").strip()
    mitre_name = str(payload.get("mitreName") or "").strip()
    containment_step = str(payload.get("containmentStep") or "").strip()

    if not attack_pattern or not mitre_id or not mitre_name or not containment_step:
        return None

    return {
        "attackPattern": attack_pattern,
        "mitreId": mitre_id,
        "mitreName": mitre_name,
        "containmentStep": containment_step,
    }


def _enrich_one(
    *,
    api_key: str,
    model: str,
    input_payload: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    if OpenAI is None:
        return None

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
        return _sanitize_enrichment(result)
    except Exception as err:
        logger.error("Per-anomaly AI enrichment failed for payload=%s reason=%s", input_payload, err)
        return None


def enrich_high_priority_anomalies(
    anomaly_inputs: List[Dict[str, Any]],
) -> Dict[int, Dict[str, str]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return {}

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    targets = [
        item
        for item in anomaly_inputs
        if str(item.get("severity") or "").upper() in {"HIGH", "CRITICAL"}
    ]
    if not targets:
        return {}

    enriched_by_index: Dict[int, Dict[str, str]] = {}
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
            enrichment = future.result()
            if enrichment is not None:
                enriched_by_index[anomaly_index] = enrichment

    return enriched_by_index
