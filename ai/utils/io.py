from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ai.utils.schema import DatasetManifest


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def read_manifest(path: Path, root: Path | None = None) -> DatasetManifest:
    manifest_root = root or path.parent.parent.parent
    return DatasetManifest.from_dict(read_json(path), manifest_root)


def write_manifest(path: Path, manifest: DatasetManifest, root: Path) -> None:
    write_json(path, manifest.to_dict(root))
