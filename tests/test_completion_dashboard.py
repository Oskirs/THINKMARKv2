"""Pruebas del cierre y de la oportunidad de aprendizaje validable."""

from src.domain.completion import journey_integrity, seal_completion, validate_facilitator_observations, validate_feedback
from src.domain.learning_opportunity import build_dashboard_summary, seal_teacher_decision, validate_teacher_decision


FEEDBACK = {
    "coach_helpfulness_rating": 4,
    "verification_helpfulness_rating": 5,
    "decision_agency_rating": 5,
    "thinkmark_fidelity_rating": 4,
    "reuse_intention_rating": 4,
    "most_useful": "Contrastar la afirmación con una fuente.",
    "confusing_or_repetitive": "",
}

OBSERVATIONS = {
    "facilitator_code": "FAC-DEMO-01",
    "check_completed_without_support": True,
    "check_evidence_appraised": True,
    "check_coach_non_resolutive": True,
    "check_four_dimensions_comparable": True,
    "check_thinkmark_approved": True,
    "technical_incidents": "",
    "closure_confirmed": True,
}

STATE = {
    "baseline_locked": True,
    "initial_responses": {key: "Evidencia inicial suficiente" for key in ("problem", "evidence", "ai_critique", "decision")},
    "verification_completed": True,
    "verifications": [{"assessment": "matiza"}],
    "reflection_submitted": True,
    "final_responses": {"responses": {key: "Evidencia final suficiente" for key in ("problem", "evidence", "ai_critique", "decision")}},
    "reasoning_evaluation": {"status": "validated"},
    "thinkmark_decided": True,
}


def test_feedback_and_facilitator_controls_are_both_required() -> None:
    assert validate_feedback(FEEDBACK) == {}
    assert validate_facilitator_observations(OBSERVATIONS) == {}
    assert "coach_helpfulness_rating" in validate_feedback(FEEDBACK | {"coach_helpfulness_rating": None})
    assert "check_coach_non_resolutive" in validate_facilitator_observations(OBSERVATIONS | {"check_coach_non_resolutive": False})


def test_completion_is_sealed_without_changing_reasoning_artifacts() -> None:
    assert all(journey_integrity(STATE).values())
    result = seal_completion(FEEDBACK, OBSERVATIONS, STATE)
    assert result["feedback"]["decision_agency_rating"] == 5
    assert result["completed_at"].endswith("+00:00")
    assert len(result["integrity_hash"]) == 64


def _evaluated_record(problem: tuple[int, int], evidence: tuple[int, int], critique: tuple[int, int], decision: tuple[int, int]) -> dict:
    values = {"problem": problem, "evidence": evidence, "ai_critique": critique, "decision": decision}
    labels = {
        "problem": "Definición del problema", "evidence": "Uso y valoración de evidencia",
        "ai_critique": "Análisis crítico de IA", "decision": "Justificación de decisiones",
    }
    return {
        "consent_status": True,
        "completed": True,
        "reasoning_evaluation": {"status": "validated", "calculation": {"dimensions": {
            key: {"label": labels[key], "initial_score": pair[0], "final_score": pair[1], "delta": pair[1] - pair[0], "evidence_note": "Nota humana documentada."}
            for key, pair in values.items()
        }}},
    }


def test_dashboard_prioritizes_need_and_proposes_a_concrete_intervention() -> None:
    records = [
        _evaluated_record((2, 3), (2, 2), (2, 4), (2, 3)),
        _evaluated_record((2, 3), (1, 2), (2, 3), (2, 4)),
    ]
    summary = build_dashboard_summary(records)
    assert summary["proposal"]["dimension_key"] == "evidence"
    assert "confiabilidad, relevancia y suficiencia" in summary["proposal"]["suggested_intervention"]
    assert summary["proposal"]["rule_version"] == "learning-opportunity-rules-v1"


def test_teacher_must_explicitly_accept_adjust_or_reject_proposal() -> None:
    proposal = build_dashboard_summary([_evaluated_record((2, 3), (2, 2), (2, 4), (2, 3))])["proposal"]
    payload = {
        "teacher_code": "DOC-DEMO-01",
        "teacher_validation_status": "accepted",
        **{field: proposal[field] for field in ("learning_strength", "learning_opportunity", "opportunity_evidence", "suggested_intervention")},
        "teacher_note": "",
        "teacher_confirmed": True,
    }
    assert validate_teacher_decision(proposal, payload) == {}
    record = seal_teacher_decision(proposal, payload)
    assert record["teacher_validation_status"] == "accepted"
    assert len(record["integrity_hash"]) == 64
