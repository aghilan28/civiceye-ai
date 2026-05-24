from __future__ import annotations

from ai.evaluation.metrics import latency_summary, parse_ultralytics_metrics


def test_parse_ultralytics_detection_metrics() -> None:
    metrics = parse_ultralytics_metrics(
        {
            "metrics/mAP50(B)": 0.7,
            "metrics/mAP50-95(B)": 0.41,
            "metrics/precision(B)": 0.8,
            "metrics/recall(B)": 0.6,
        },
        [10, 20, 30],
    )

    assert metrics.map50 == 0.7
    assert metrics.false_positive_rate == 0.19999999999999996
    assert metrics.false_negative_rate == 0.4
    assert round(metrics.f1_score or 0, 3) == 0.686
    assert metrics.latency_p50_ms == 20
    assert metrics.throughput_fps == 50


def test_latency_summary() -> None:
    summary = latency_summary([4.0, 1.0, 2.0, 3.0])

    assert summary["min_ms"] == 1.0
    assert summary["max_ms"] == 4.0
