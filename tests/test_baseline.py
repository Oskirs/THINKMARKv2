"""Pruebas del acceso pseudónimo y la línea base inmutable."""

from pathlib import Path

import pytest

from src.domain.baseline import normalize_participant_code, seal_baseline, validate_baseline, validate_participant_code
from src.repositories.local_sessions import LocalSessionRepository


COMPLETE_RESPONSES = {
    "problem": "El problema es ofrecer apoyo temprano sin convertir una correlación en una etiqueta definitiva.",
    "evidence": "Necesito comparar precisión, falsos positivos y resultados de las intervenciones por cada programa.",
    "ai_critique": "La IA puede confundir menor actividad digital con desinterés y omitir diferencias de contexto.",
    "decision": "Aceptaría un piloto voluntario porque permitiría evaluar beneficios con revisión humana y salvaguardas.",
}


def test_participant_code_is_normalized_and_validated() -> None:
    assert normalize_participant_code(" tm-demo-024 ") == "TM-DEMO-024"
    assert validate_participant_code("tm-demo-024") == ("TM-DEMO-024", None)
    _, error = validate_participant_code("oscar@email.com")
    assert error is not None


def test_baseline_requires_four_developed_responses() -> None:
    errors = validate_baseline({"problem": "Muy breve"}, 3)
    assert set(errors) == {"problem", "evidence", "ai_critique", "decision"}
    assert validate_baseline(COMPLETE_RESPONSES, 4) == {}


def test_sealed_baseline_has_timestamp_and_integrity_hash() -> None:
    snapshot = seal_baseline(COMPLETE_RESPONSES, 4, "CASO-DEMO-01")
    assert snapshot["responses"] == COMPLETE_RESPONSES
    assert snapshot["confidence"] == 4
    assert len(snapshot["integrity_hash"]) == 64
    assert snapshot["locked_at"].endswith("+00:00")


def test_repository_recovers_draft_and_rejects_locked_overwrite(tmp_path: Path) -> None:
    repository = LocalSessionRepository(tmp_path / "sessions.json")
    record = {
        "participant_id": "TM-DEMO-024",
        "session_id": "SES-TEST",
        "baseline_locked": False,
        "baseline_draft": {"problem": "borrador"},
        "baseline_snapshot": {},
    }
    repository.save(record)
    assert repository.get("TM-DEMO-024")["baseline_draft"]["problem"] == "borrador"

    locked = record | {"baseline_locked": True, "baseline_snapshot": seal_baseline(COMPLETE_RESPONSES, 4, "CASO-DEMO-01")}
    repository.save(locked)
    changed = locked | {"baseline_snapshot": {"responses": {"problem": "alterado"}}}
    with pytest.raises(ValueError, match="no puede modificarse"):
        repository.save(changed)


def test_repository_rejects_submitted_reflection_overwrite(tmp_path: Path) -> None:
    repository = LocalSessionRepository(tmp_path / "sessions.json")
    submitted = {
        "participant_id": "TM-DEMO-025",
        "session_id": "SES-FINAL",
        "baseline_locked": False,
        "baseline_snapshot": {},
        "reflection_submitted": True,
        "final_responses": {"responses": {"problem": "versión final"}, "integrity_hash": "abc"},
    }
    repository.save(submitted)
    with pytest.raises(ValueError, match="reflexión enviada"):
        repository.save(submitted | {"final_responses": {"responses": {"problem": "alterada"}}})


def test_repository_rejects_validated_evaluation_overwrite(tmp_path: Path) -> None:
    repository = LocalSessionRepository(tmp_path / "sessions.json")
    validated = {
        "participant_id": "TM-DEMO-026",
        "session_id": "SES-EVALUATED",
        "baseline_locked": False,
        "baseline_snapshot": {},
        "reflection_submitted": True,
        "final_responses": {"responses": {"problem": "versión final"}},
        "reasoning_evaluation": {"status": "validated", "integrity_hash": "abc"},
    }
    repository.save(validated)
    with pytest.raises(ValueError, match="evaluación validada"):
        repository.save(validated | {"reasoning_evaluation": {"status": "validated", "integrity_hash": "otro"}})
