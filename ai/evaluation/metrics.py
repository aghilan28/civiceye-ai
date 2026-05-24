from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median
from typing import Any


@dataclass(frozen=True)
class DetectionMetrics:
    map50: float | None
    map5095: float | None
    precision: float | None
    recall: float | None
    false_positive_rate: float | None
    false_negative_rate: float | None
    f1_score: float | None
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    throughput_fps: float | None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "map50": self.map50,
            "map5095": self.map5095,
            "precision": self.precision,
            "recall": self.recall,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
            "f1_score": self.f1_score,
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "throughput_fps": self.throughput_fps,
        }


def parse_ultralytics_metrics(results_dict: dict[str, Any], latencies_ms: list[float] | None = None) -> DetectionMetrics:
    precision = _first(results_dict, "metrics/precision(B)", "precision")
    recall = _first(results_dict, "metrics/recall(B)", "recall")
    fp_rate = None if precision is None else max(0.0, 1.0 - precision)
    fn_rate = None if recall is None else max(0.0, 1.0 - recall)
    f1_score = None
    if precision is not None and recall is not None and precision + recall > 0:
        f1_score = 2 * precision * recall / (precision + recall)
    p50_latency = _percentile(latencies_ms or [], 50)
    return DetectionMetrics(
        map50=_first(results_dict, "metrics/mAP50(B)", "map50"),
        map5095=_first(results_dict, "metrics/mAP50-95(B)", "map5095"),
        precision=precision,
        recall=recall,
        false_positive_rate=fp_rate,
        false_negative_rate=fn_rate,
        f1_score=f1_score,
        latency_p50_ms=p50_latency,
        latency_p95_ms=_percentile(latencies_ms or [], 95),
        throughput_fps=None if not p50_latency or p50_latency <= 0 else 1000.0 / p50_latency,
    )


def latency_summary(latencies_ms: list[float]) -> dict[str, float]:
    if not latencies_ms:
        return {}
    return {
        "mean_ms": round(mean(latencies_ms), 3),
        "median_ms": round(median(latencies_ms), 3),
        "p50_ms": round(_percentile(latencies_ms, 50) or 0.0, 3),
        "p95_ms": round(_percentile(latencies_ms, 95) or 0.0, 3),
        "min_ms": round(min(latencies_ms), 3),
        "max_ms": round(max(latencies_ms), 3),
    }


def _first(payload: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((percentile / 100) * (len(ordered) - 1)))
    return float(ordered[index])
