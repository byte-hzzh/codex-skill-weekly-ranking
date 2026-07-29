from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from .io import read_json


def validate_document(root: Path, schema_name: str, value: Any) -> None:
    schema = read_json(root / "schemas" / schema_name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path)
    )
    if errors:
        details = "; ".join(error.message for error in errors[:5])
        raise ValueError(f"{schema_name} validation failed: {details}")
