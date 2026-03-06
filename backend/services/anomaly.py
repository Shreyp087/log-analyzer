from typing import List, Dict


SUSPICIOUS_IPS = {"45.33.12.9", "201.54.2.99"}


def detect_anomalies(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Mark rows that should be flagged for further investigation."""
    flagged = []
    for row in rows:
        if row.get("source_ip") in SUSPICIOUS_IPS or row.get("status") == "401":
            flagged.append(row)
    return flagged
