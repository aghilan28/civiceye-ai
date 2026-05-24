from __future__ import annotations

from pathlib import Path

from ai.training.checkpoints import CheckpointManager


def test_checkpoint_manager_captures_best_and_last(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    weights_dir = run_dir / "weights"
    weights_dir.mkdir(parents=True)
    (weights_dir / "best.pt").write_bytes(b"best")
    (weights_dir / "last.pt").write_bytes(b"last")

    manager = CheckpointManager(tmp_path / "checkpoints")
    record = manager.capture_from_ultralytics_run(run_dir, {"metrics/mAP50-95(B)": 0.42})

    assert record.best and record.best.exists()
    assert record.last and record.last.exists()
    assert record.metric_value == 0.42
    assert (tmp_path / "checkpoints" / "checkpoint_lineage.json").exists()
