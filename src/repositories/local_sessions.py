"""Repositorio JSON sustituible por Supabase en el paso 6.8."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from src.domain.activity_session import generate_session_code, validate_status_transition


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "runtime" / "sessions.json"


def validate_record_transition(existing: dict[str, Any] | None, record: dict[str, Any]) -> None:
    """Protege los artefactos sellados en cualquier backend de persistencia."""
    if existing and existing.get("academic_profile") and record.get("academic_profile") != existing.get("academic_profile"):
        raise ValueError("El perfil académico asignado a la sesión no puede modificarse.")
    if existing and existing.get("case_snapshot") and record.get("case_snapshot") != existing.get("case_snapshot"):
        raise ValueError("El caso asignado a la sesión no puede modificarse.")
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
        self.activity_path = path.with_name("activity_sessions.json")

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

    def get(self, participant_id: str, activity_session_id: str = "") -> dict[str, Any] | None:
        sessions = self._read_all()
        record = sessions.get(f"{activity_session_id}:{participant_id}") if activity_session_id else sessions.get(participant_id)
        if not record:
            record = next((item for item in sessions.values() if item.get("participant_id") == participant_id and (not activity_session_id or item.get("activity_session_id") == activity_session_id)), None)
        return record.copy() if record else None

    def list_all(self) -> list[dict[str, Any]]:
        return [record.copy() for record in self._read_all().values()]

    def list_for_evaluator(self, user_id: str) -> list[dict[str, Any]]:
        # El modo local es exclusivamente demostrativo y no tiene asignaciones persistentes.
        return self.list_all()

    def _read_activity_sessions(self) -> dict[str, dict[str, Any]]:
        if not self.activity_path.exists():
            return {}
        try:
            return json.loads(self.activity_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_activity_sessions(self, sessions: dict[str, dict[str, Any]]) -> None:
        self.activity_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.activity_path.parent, delete=False) as temp:
            json.dump(sessions, temp, ensure_ascii=False, indent=2, sort_keys=True)
            temp_path = Path(temp.name)
        temp_path.replace(self.activity_path)

    def get_activity_session(self, session_code: str) -> dict[str, Any] | None:
        record = self._read_activity_sessions().get(session_code)
        return record.copy() if record else None

    def create_activity_session(self, title: str, created_by: str, evaluator_id: str = "") -> dict[str, Any]:
        sessions = self._read_activity_sessions()
        code = generate_session_code(sessions)
        record = {
            "activity_session_id": f"AS-{uuid4().hex.upper()}",
            "session_code": code,
            "title": title.strip(),
            "activity_id": "CASO-DEMO-01-v1",
            "status": "open",
            "created_by": created_by,
            "evaluator_ids": [evaluator_id] if evaluator_id else [],
        }
        sessions[code] = record
        self._write_activity_sessions(sessions)
        return record.copy()

    def list_activity_sessions_for_creator(self, user_id: str) -> list[dict[str, Any]]:
        return [item.copy() for item in self._read_activity_sessions().values() if item.get("created_by") == user_id]

    def list_activity_sessions_for_evaluator(self, user_id: str) -> list[dict[str, Any]]:
        sessions = self._read_activity_sessions().values()
        return [item.copy() for item in sessions if not item.get("evaluator_ids") or user_id in item.get("evaluator_ids", [])]

    def list_participants(self, activity_session_id: str) -> list[dict[str, Any]]:
        return [record.copy() for record in self._read_all().values() if record.get("activity_session_id") == activity_session_id]

    def list_evaluators(self) -> list[dict[str, str]]:
        return [{"user_id": "local-evaluator", "display_code": "Evaluador de demostración"}]

    def set_activity_session_status(self, session_code: str, status: str) -> None:
        sessions = self._read_activity_sessions()
        current = sessions.get(session_code)
        if not current:
            raise ValueError("La sesión no existe.")
        validate_status_transition(current["status"], status)
        current["status"] = status
        self._write_activity_sessions(sessions)

    def audit_access(self, actor_id: str, actor_role: str, action: str, target_type: str, target_id: str = "") -> None:
        # Sin auditoría nominal en el modo local de demostración.
        return None

    def save(self, record: dict[str, Any]) -> None:
        sessions = self._read_all()
        key = f"{record['activity_session_id']}:{record['participant_id']}" if record.get("activity_session_id") else record["participant_id"]
        existing = sessions.get(key)
        validate_record_transition(existing, record)
        sessions[key] = record
        self._write_all(sessions)
