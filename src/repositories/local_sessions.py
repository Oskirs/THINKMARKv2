"""Repositorio JSON sustituible por Supabase en el paso 6.8."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "runtime" / "sessions.json"


class LocalSessionRepository:
    def __init__(self, path: Path = DEFAULT_STORE) -> None:
        self.path = path

    def _read_all(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, sessions: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temp:
            json.dump(sessions, temp, ensure_ascii=False, indent=2, sort_keys=True)
            temp_path = Path(temp.name)
        temp_path.replace(self.path)

    def get(self, participant_id: str) -> dict[str, Any] | None:
        record = self._read_all().get(participant_id)
        return record.copy() if record else None

    def save(self, record: dict[str, Any]) -> None:
        sessions = self._read_all()
        existing = sessions.get(record["participant_id"])
        if existing and existing.get("baseline_locked") and record.get("baseline_snapshot") != existing.get("baseline_snapshot"):
            raise ValueError("La línea base cerrada no puede modificarse.")
        if existing and existing.get("reflection_submitted") and record.get("final_responses") != existing.get("final_responses"):
            raise ValueError("La reflexión enviada no puede modificarse.")
        sessions[record["participant_id"]] = record
        self._write_all(sessions)
