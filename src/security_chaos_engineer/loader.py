"""Load the target system from YAML with strict validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import TargetSystem
from .resources import packaged_path

MAX_DOCUMENT_BYTES = 1_048_576


def _read_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError(f"{path} exceeds {MAX_DOCUMENT_BYTES} bytes")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a top-level mapping")
    return data


def load_system(path: Path) -> TargetSystem:
    return TargetSystem.model_validate(_read_yaml(path))


def load_default_system() -> TargetSystem:
    return load_system(packaged_path("system.yaml"))
