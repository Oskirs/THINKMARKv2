"""Pruebas de configuración, acceso por rol y políticas del paso 6.8."""

from pathlib import Path

import pytest

from src.infrastructure.settings import ConfigurationError, RuntimeSettings
from src.repositories.factory import get_session_repository
from src.repositories.local_sessions import LocalSessionRepository, validate_record_transition
from src.services.auth import InternalAuthService


LOCAL_SETTINGS = RuntimeSettings(
    persistence_mode="local",
    supabase_url="",
    supabase_publishable_key="",
    supabase_secret_key="",
    demo_internal_access=True,
    local_evaluator_access_code="EV-TEST-2026",
    local_teacher_access_code="DOC-TEST-2026",
)


def test_supabase_mode_fails_closed_when_secrets_are_missing_or_legacy() -> None:
    missing = LOCAL_SETTINGS.__class__(
        persistence_mode="supabase",
        supabase_url="https://project.supabase.co",
        supabase_publishable_key="",
        supabase_secret_key="",
        demo_internal_access=False,
        local_evaluator_access_code="",
        local_teacher_access_code="",
    )
    with pytest.raises(ConfigurationError):
        missing.validate()
    legacy = missing.__class__(
        **{**missing.__dict__, "supabase_publishable_key": "legacy-anon", "supabase_secret_key": "legacy-service-role"}
    )
    with pytest.raises(ConfigurationError):
        legacy.validate()


def test_local_internal_access_separates_evaluator_and_teacher_codes() -> None:
    auth = InternalAuthService(LOCAL_SETTINGS)
    assert auth.sign_in("evaluator", "", "EV-TEST-2026").role == "evaluator"
    assert auth.sign_in("teacher", "", "DOC-TEST-2026").role == "teacher"
    with pytest.raises(ValueError):
        auth.sign_in("teacher", "", "EV-TEST-2026")


def test_local_factory_remains_available_for_offline_demo() -> None:
    assert isinstance(get_session_repository(LOCAL_SETTINGS), LocalSessionRepository)


def test_sealed_record_transition_is_shared_by_all_backends() -> None:
    existing = {
        "baseline_locked": True,
        "baseline_snapshot": {"integrity_hash": "abc"},
        "thinkmark_decided": False,
        "completed": False,
    }
    validate_record_transition(existing, existing.copy())
    with pytest.raises(ValueError):
        validate_record_transition(existing, existing | {"baseline_snapshot": {"integrity_hash": "changed"}})


def test_sql_enables_rls_and_does_not_grant_student_public_access() -> None:
    sql = (Path(__file__).resolve().parents[1] / "supabase" / "migrations" / "202608130001_thinkmark_v2.sql").read_text(encoding="utf-8")
    for table in ("profiles", "thinkmark_sessions", "session_assignments", "learning_opportunities", "access_audit"):
        assert f"alter table public.{table} enable row level security" in sql
    assert "revoke all on public.profiles" in sql
    assert "from anon" in sql
    assert "grant execute on function public.save_thinkmark_session" in sql
    assert "to service_role" in sql
    assert "raw_user_meta_data" in sql  # Comentario explícito: no usar metadatos editables para roles.
