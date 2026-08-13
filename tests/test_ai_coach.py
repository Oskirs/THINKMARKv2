"""Pruebas del contrato pedagógico y el fallo seguro del AI Coach."""

from src.ai.coach import (
    AdapterResponse,
    CoachOutput,
    CoachService,
    FALLBACK_QUESTIONS,
    FOCUS_LABELS,
    FakeAIAdapter,
    select_focus,
    validate_non_resolutive,
)


CASE = {
    "title": "Caso de prueba",
    "central_question": "¿Debe realizarse un piloto?",
    "facts": ["El piloto sería voluntario."],
}

INITIAL = {
    "problem": "El problema requiere equilibrar apoyo temprano y agencia de las personas participantes.",
    "evidence": "Faltan datos.",
    "ai_critique": "La recomendación puede omitir diferencias de contexto y cobertura entre grupos.",
    "decision": "Aceptaría un piloto limitado únicamente con revisión humana y consentimiento.",
}

CONFIG = {
    "enabled": True,
    "provider": "openai",
    "model": "test-model",
    "policy_version": "test-policy",
    "prompt_version": "test-prompt",
    "prompt_path": "config/prompts/coach_socratic_v1.txt",
    "max_turns": 3,
    "timeout_seconds": 1,
    "fallback_enabled": True,
}


def test_focus_selector_uses_completeness_and_rotates_dimensions() -> None:
    assert select_focus(INITIAL, []) == "evidence"
    answered = [{"focus_key": "evidence", "question": "¿Qué dato falta?", "response": "Una respuesta desarrollada."}]
    assert select_focus(INITIAL, answered) != "evidence"


def test_fake_adapter_produces_a_valid_single_question() -> None:
    result = CoachService(config=CONFIG, adapter=FakeAIAdapter()).next_question(
        case=CASE,
        initial_responses=INITIAL,
        answered_turns=[],
    )
    assert result.question == FALLBACK_QUESTIONS["evidence"]
    assert result.focus_dimension == FOCUS_LABELS["evidence"]
    assert result.question.count("?") == 1


def test_non_resolution_validator_blocks_answers_and_multiple_questions() -> None:
    answer = CoachOutput(FOCUS_LABELS["evidence"], "La respuesta es aprobar el piloto, ¿estás de acuerdo?", False)
    multiple = CoachOutput(FOCUS_LABELS["evidence"], "¿Qué dato falta? ¿Qué decidirías?", False)
    assert validate_non_resolutive(answer, "evidence")
    assert validate_non_resolutive(multiple, "evidence")


def test_invalid_provider_output_activates_safe_fallback() -> None:
    class ResolvingAdapter:
        def generate(self, **_: object) -> AdapterResponse:
            return AdapterResponse(
                CoachOutput(FOCUS_LABELS["evidence"], "La solución es aceptar el piloto, ¿puedes copiarla?", False),
                "unsafe-test-model",
            )

    result = CoachService(config=CONFIG, adapter=ResolvingAdapter()).next_question(
        case=CASE,
        initial_responses=INITIAL,
        answered_turns=[],
    )
    assert result.mode == "fallback"
    assert result.safety_triggered is True
    assert result.question == FALLBACK_QUESTIONS["evidence"]
    assert result.fallback_reason
