"""Pruebas del modelo de sesiones grupales del paso 7.3.1."""

from pathlib import Path

import pytest

from src.domain.activity_session import (
    generate_session_code,
    participant_may_enter,
    validate_session_code,
    validate_status_transition,
)
from src.repositories.local_sessions import LocalSessionRepository


def test_session_code_uses_exact_public_format() -> None:
    assert validate_session_code(" tm-ab12cd ") == ("TM-AB12CD", None)
    assert validate_session_code("TM-CORTO")[1] is not None
    generated = generate_session_code({"TM-ABC234"})
    assert validate_session_code(generated)[1] is None
    assert generated != "TM-ABC234"


def test_session_status_transitions_and_student_entry_rules() -> None:
    validate_status_transition("open", "closed")
    validate_status_transition("closed", "open")
    validate_status_transition("closed", "archived")
    with pytest.raises(ValueError):
        validate_status_transition("archived", "open")
    assert participant_may_enter("open", already_joined=False)
    assert participant_may_enter("closed", already_joined=True)
    assert not participant_may_enter("closed", already_joined=False)
    assert not participant_may_enter("archived", already_joined=True)


def test_incremental_migration_preserves_existing_schema() -> None:
    root = Path(__file__).resolve().parents[1]
    sql = (root / "supabase/migrations/202608210001_sessions_traceability.sql").read_text(encoding="utf-8")
    assert "create table if not exists public.activity_sessions" in sql
    assert "create table if not exists public.activity_session_assignments" in sql
    assert "add column if not exists activity_session_id" in sql
    assert "TM-LEGACY" in sql
    assert "drop table" not in sql.casefold()
    assert "enable row level security" in sql
    assert "save_thinkmark_session_v2" in sql


def test_participant_code_hotfix_matches_application_validation() -> None:
    root = Path(__file__).resolve().parents[1]
    sql = (root / "supabase/migrations/202608210003_align_participant_code_constraint.sql").read_text(
        encoding="utf-8"
    )
    assert "drop constraint if exists thinkmark_sessions_participant_code_check" in sql
    assert "^[A-Z0-9][A-Z0-9-]{5,19}$" in sql
    assert "validate constraint thinkmark_sessions_participant_code_check" in sql


def test_local_repository_groups_participants_and_controls_status(tmp_path: Path) -> None:
    repository = LocalSessionRepository(tmp_path / "sessions.json")
    activity = repository.create_activity_session("Grupo piloto", "local-teacher", "local-evaluator")
    record = {
        "participant_id": "ALU-001",
        "session_id": "SES-001",
        "activity_session_id": activity["activity_session_id"],
        "session_code": activity["session_code"],
        "baseline_locked": False,
        "baseline_snapshot": {},
    }
    repository.save(record)
    assert repository.get("ALU-001", activity["activity_session_id"])["session_code"] == activity["session_code"]
    assert [item["participant_id"] for item in repository.list_participants(activity["activity_session_id"])] == ["ALU-001"]
    assert repository.list_activity_sessions_for_evaluator("local-evaluator")[0]["session_code"] == activity["session_code"]
    repository.set_activity_session_status(activity["session_code"], "closed")
    assert repository.get_activity_session(activity["session_code"])["status"] == "closed"


def test_student_and_internal_views_expose_session_then_participant() -> None:
    root = Path(__file__).resolve().parents[1]
    student = (root / "src/screens/student.py").read_text(encoding="utf-8")
    access = (root / "src/screens/access.py").read_text(encoding="utf-8")
    faculty = (root / "src/screens/faculty.py").read_text(encoding="utf-8")
    assert "Código de sesión" in student
    assert "Código anónimo de participante" in student
    assert "Sesión del grupo" in access and '"Participante"' in access
    assert "Crear sesión y generar código" in faculty
