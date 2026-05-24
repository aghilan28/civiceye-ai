from pathlib import Path

from ai.scripts.export_yolo import write_label


def test_write_empty_label(tmp_path: Path) -> None:
    label_path = tmp_path / "labels" / "empty.txt"
    write_label(label_path, [])
    assert label_path.exists()
    assert label_path.read_text(encoding="utf-8") == ""
