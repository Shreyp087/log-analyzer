from collections import Counter
from typing import Any, Dict, Iterable, List


def _top_counts(values: Iterable[str], top_n: int = 5) -> List[Dict[str, Any]]:
    counter = Counter(v for v in values if v)
    return [{"value": value, "count": count} for value, count in counter.most_common(top_n)]


def generate_summary_metrics(events: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, Any]:
    actions = [(event.get("action") or "").upper() for event in events]
    source_ips = [event.get("source_ip") for event in events if event.get("source_ip")]
    categories = [event.get("category") for event in events if event.get("category")]
    destinations = [event.get("destination") for event in events if event.get("destination")]

    return {
        "total_events": len(events),
        "blocked_events": sum(1 for action in actions if action == "BLOCK"),
        "allowed_events": sum(1 for action in actions if action == "ALLOW"),
        "unique_ips": len(set(source_ips)),
        "top_categories": _top_counts(categories, top_n=top_n),
        "top_destinations": _top_counts(destinations, top_n=top_n),
        "top_source_ips": _top_counts(source_ips, top_n=top_n),
    }
