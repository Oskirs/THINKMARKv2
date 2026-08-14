"""Pruebas de evaluación humana y cálculo reproducible de Reasoning Delta."""

from src.domain.evaluation import calculate_reasoning_delta, seal_evaluation, validate_evaluation


VALID_PAYLOAD = {
    "evaluator_code": "EV-DEMO-01",
    "ratings": {
        "problem": {"initial_score": 2, "final_score": 4, "evidence_note": "La respuesta final delimita actores, tensiones y restricciones que no aparecían al inicio."},
        "evidence": {"initial_score": 2, "final_score": 3, "evidence_note": "La respuesta final relaciona la fuente verificada con la decisión y reconoce una limitación."},
        "ai_critique": {"initial_score": 2, "final_score": 4, "evidence_note": "La versión final identifica supuestos, límites de cobertura y un contraargumento propio razonado."},
        "decision": {"initial_score": 2, "final_score": 4, "evidence_note": "La decisión final integra evidencia, consecuencias, salvaguardas y una concesión explícita."},
    },
    "human_validation_confirmed": True,
}


def test_evaluation_requires_human_code_scores_and_evidence_notes() -> None:
    assert validate_evaluation(VALID_PAYLOAD, require_confirmation=True) == {}
    invalid = VALID_PAYLOAD | {"evaluator_code": "persona@email.com", "human_validation_confirmed": False}
    errors = validate_evaluation(invalid, require_confirmation=True)
    assert "evaluator_code" in errors
    assert "confirmation" in errors


def test_reasoning_delta_is_final_minus_initial_for_each_dimension() -> None:
    result = calculate_reasoning_delta(VALID_PAYLOAD)
    assert result["dimensions"]["problem"]["delta"] == 2
    assert result["dimensions"]["evidence"]["delta"] == 1
    assert result["average_initial"] == 2.0
    assert result["average_final"] == 3.75
    assert result["delta_average"] == 1.75
    assert set(result["dominant_change"]) == {"Definición del problema", "Análisis crítico de IA", "Justificación de decisiones"}


def test_validated_evaluation_has_version_timestamp_and_integrity_hash() -> None:
    record = seal_evaluation(VALID_PAYLOAD)
    assert record["status"] == "validated"
    assert record["rubric_version"] == "Reasoning-Delta-v2"
    assert record["validated_at"].endswith("+00:00")
    assert len(record["integrity_hash"]) == 64
