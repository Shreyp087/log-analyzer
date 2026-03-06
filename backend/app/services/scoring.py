from typing import Iterable


def clamp_confidence(value: float) -> float:
    return round(max(0.0, min(0.99, value)), 2)


def confidence_from_signals(
    base: float, boosts: Iterable[float] = (), penalties: Iterable[float] = ()
) -> float:
    raw_score = base + sum(boosts) - sum(penalties)
    return clamp_confidence(raw_score)


def severity_from_confidence(confidence: float) -> str:
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"
