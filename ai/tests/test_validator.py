from pathlib import Path

from ai.utils.schema import DatasetManifest
from ai.validation.validator import validate_manifest


def test_empty_manifest_fails() -> None:
    manifest = DatasetManifest(
        dataset_id="test",
        version="v0",
        created_at="2026-05-15T00:00:00Z",
        description="empty",
        annotation_version="v1",
        source_ids=[],
        items=[],
    )
    report = validate_manifest(manifest)
    assert not report.passed
    assert any(issue.code == "NO_POSITIVES" for issue in report.issues)
    assert any(issue.code == "NO_NEGATIVES" for issue in report.issues)


def test_manifest_paths_are_path_objects() -> None:
    assert isinstance(Path("raw/example.jpg"), Path)
