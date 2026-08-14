"""Pruebas de generación, revisión y sellado de Human Reasoning Signature."""

from src.ai.thinkmark import LocalThinkMarkAdapter, ThinkMarkService, build_thinkmark_context
from src.domain.thinkmark import (
    THINKMARK_FIELDS,
    content_hash,
    seal_final,
    validate_content,
    validate_student_decision,
)


STATE = {
    "initial_responses": {
        "decision": "Aceptaría un piloto limitado si existe revisión humana y consentimiento informado."
    },
    "coach_turns": [{"question": "¿Qué evidencia falta?", "response": "Compararía errores entre programas."}],
    "verifications": [{
        "claim": "Las alertas siempre mejoran la permanencia.",
        "source_title": "Estudio institucional sobre alertas",
        "assessment": "matiza",
        "reliability_reason": "Describe la muestra, el método y sus principales limitaciones.",
        "impact": "La utilidad depende de la intervención posterior.",
    }],
    "challenges": [{
        "limitation": "No considera diferencias de cobertura digital entre los programas.",
        "assumption": "Supone que menor actividad representa necesariamente mayor riesgo.",
    }],
    "decision": {"tradeoff": "Acepto menor velocidad para asegurar una revisión humana explicable."},
    "final_responses": {"responses": {
        "problem": "El reto es orientar apoyo sin convertir correlaciones imperfectas en etiquetas.",
        "decision": "Realizaría un piloto voluntario, auditado y sin decisiones automáticas.",
        "change": "Incorporé criterios explícitos de justicia, explicabilidad y consentimiento.",
        "human_contribution": "Definí salvaguardas y el derecho de cada estudiante a solicitar aclaración.",
        "uncertainty": "Falta validar el desempeño con datos reales de todos los programas.",
        "next_step": "Diseñaría una auditoría desagregada con participación estudiantil.",
    }},
    "reasoning_evaluation": {"calculation": {"delta_average": 1.5}},
}

CONFIG = {
    "policy_version": "test-policy",
    "prompt_version": "test-prompt",
    "fallback_enabled": True,
}


def test_context_contains_only_allowed_journey_evidence() -> None:
    context = build_thinkmark_context(STATE | {"participant_id": "NO-DEBE-SALIR"})
    assert set(context) == {"initial", "coach", "verification", "challenge", "decision", "reflection", "validated_delta"}
    assert "participant_id" not in context


def test_local_generator_produces_all_nine_complete_sections() -> None:
    result = ThinkMarkService(config=CONFIG, adapter=LocalThinkMarkAdapter()).generate(build_thinkmark_context(STATE))
    assert tuple(result.content) == THINKMARK_FIELDS
    assert validate_content(result.content) == {}
    assert result.mode == "injected"
    assert "Estudio institucional" in result.content["tm_evidence_reviewed"]


def test_approval_mode_must_match_student_edits() -> None:
    draft = ThinkMarkService(config=CONFIG, adapter=LocalThinkMarkAdapter()).generate(build_thinkmark_context(STATE)).content
    edited = draft | {"tm_personal_contribution": draft["tm_personal_contribution"] + " Además prioricé la agencia humana."}
    assert "decision" in validate_student_decision(draft, edited, "approved_as_generated", True)
    assert validate_student_decision(draft, edited, "approved_with_corrections", True) == {}
    assert "confirmation" in validate_student_decision(draft, draft, "approved_as_generated", False)


def test_final_version_has_timestamp_and_integrity_seal() -> None:
    draft = ThinkMarkService(config=CONFIG, adapter=LocalThinkMarkAdapter()).generate(build_thinkmark_context(STATE)).content
    final = seal_final(draft, "approved_as_generated")
    assert final["content"] == draft
    assert final["integrity_hash"] == content_hash(draft)
    assert final["approved_at"].endswith("+00:00")
