"""Repositorio JSON sustituible por Supabase en el paso 6.8."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "runtime" / "sessions.json"


def validate_record_transition(existing: dict[str, Any] | None, record: dict[str, Any]) -> None:
    """Protege los artefactos sellados en cualquier backend de persistencia."""
    if existing and existing.get("baseline_locked") and record.get("baseline_snapshot") != existing.get("baseline_snapshot"):
        raise ValueError("La línea base cerrada no puede modificarse.")
    if existing and existing.get("reflection_submitted") and record.get("final_responses") != existing.get("final_responses"):
        raise ValueError("La reflexión enviada no puede modificarse.")
    existing_evaluation = existing.get("reasoning_evaluation", {}) if existing else {}
    if existing_evaluation.get("status") == "validated" and record.get("reasoning_evaluation") != existing_evaluation:
        raise ValueError("La evaluación validada no puede modificarse.")
    existing_versions = existing.get("thinkmark_versions", []) if existing else []
    record_versions = record.get("thinkmark_versions", [])
    if existing_versions and record_versions[:len(existing_versions)] != existing_versions:
        raise ValueError("El historial de propuestas ThinkMark no puede reescribirse.")
    if existing and existing.get("thinkmark_decided"):
        protected = (
            "thinkmark_final", "thinkmark_approval_status", "thinkmark_approved_at",
            "thinkmark_decided", "thinkmark_decided_at", "thinkmark_versions",
        )
        if any(record.get(key) != existing.get(key) for key in protected):
            raise ValueError("La decisión final sobre la ThinkMark no puede modificarse.")
    if existing and existing.get("completed"):
        protected = ("feedback", "facilitator_observations", "completed", "completed_at", "completion_integrity")
        if any(record.get(key) != existing.get(key) for key in protected):
            raise ValueError("La sesión cerrada y su feedback no pueden modificarse.")


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

    def list_all(self) -> list[dict[str, Any]]:
        return [record.copy() for record in self._read_all().values()]

    def list_for_evaluator(self, user_id: str) -> list[dict[str, Any]]:
        # El modo local es exclusivamente demostrativo y no tiene asignaciones persistentes.
        return self.list_all()

    def audit_access(self, actor_id: str, actor_role: str, action: str, target_type: str, target_id: str = "") -> None:
        # Sin auditoría nominal en el modo local de demostración.
        return None

    def save(self, record: dict[str, Any]) -> None:
        sessions = self._read_all()
        existing = sessions.get(record["participant_id"])
        validate_record_transition(existing, record)
        sessions[record["participant_id"]] = record
        self._write_all(sessions)
