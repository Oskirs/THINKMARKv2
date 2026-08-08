"""Carga validada de datos simulados para el prototipo."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def load_demo_case() -> dict[str, Any]:
    path = ROOT / "data" / "fixtures" / "demo_case.json"
    with path.open(encoding="utf-8") as fixture:
        data = json.load(fixture)
    required = {"case_id", "title", "central_question", "participant"}
    missing = required.difference(data)
    if missing:
        raise ValueError(f"Fixture incompleto; faltan: {', '.join(sorted(missing))}")
    return data
