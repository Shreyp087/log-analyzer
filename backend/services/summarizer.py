from typing import Dict, List


def summarize_logs(rows: List[Dict[str, str]]) -> Dict[str, int]:
    """Return basic aggregate counts for quick diagnostics."""
    return {
        "total_rows": len(rows),
        "error_rows": sum(1 for row in rows if row.get("status", "").startswith("5")),
    }
