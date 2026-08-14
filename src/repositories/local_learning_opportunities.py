"""Persistencia local de la validación docente; reemplazable por Supabase."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "runtime" / "learning_opportunities.json"


class LocalLearningOpportunityRepository:
    def __init__(self, path: Path = DEFAULT_STORE) -> None:
        self.path = path

    def get(self, activity_id: str) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.path.read_text(encoding="utf-8")).get(activity_id)
        except (json.JSONDecodeError, OSError):
            return None

    def save_once(self, activity_id: str, record: dict[str, Any]) -> None:
        records: dict[str, Any] = {}
        if self.path.exists():
            try:
                records = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                records = {}
        if activity_id in records:
            raise ValueError("La decisión docente de esta actividad ya fue registrada.")
        records[activity_id] = record
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temp:
            json.dump(records, temp, ensure_ascii=False, indent=2, sort_keys=True)
            temp_path = Path(temp.name)
        temp_path.replace(self.path)
