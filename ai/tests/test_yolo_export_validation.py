from __future__ import annotations

from pathlib import Path

from ai.scripts.validate_yolo_export import validate_yolo_export


def test_validate_yolo_export_accepts_valid_export(tmp_path: Path) -> None:
    export_dir = tmp_path / "export"
    for split in ("train", "val", "test"):
        (export_dir / "images" / split).mkdir(parents=True)
        (export_dir / "labels" / split).mkdir(parents=True)
        (export_dir / "images" / split / f"{split}.jpg").write_bytes(b"image")
        (export_dir / "labels" / split / f"{split}.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    (export_dir / "data.yaml").write_text("path: .\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: pothole\n", encoding="utf-8")

    report = validate_yolo_export(export_dir, tmp_path / "report.json")

    assert report["passed"] is True
    assert report["counts"]["train"]["images"] == 1
