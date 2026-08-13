"""Pruebas de las reglas del recorrido sin IA."""

from src.domain.reasoning_journey import (
    validate_challenge,
    validate_coach_bridge,
    validate_decision,
    validate_reflection,
    validate_verification,
)


def test_coach_bridge_requires_reasoning_and_claim() -> None:
    assert validate_coach_bridge({"response": "breve", "claim_to_verify": "corta"})
    assert validate_coach_bridge({
        "response": "Compararía resultados y errores entre programas antes de aceptar la recomendación.",
        "claim_to_verify": "Las alertas tempranas siempre mejoran la permanencia estudiantil.",
    }) == {}


def test_verification_requires_traceable_url_and_human_assessment() -> None:
    payload = {
        "claim": "Las alertas tempranas siempre mejoran la permanencia.",
        "source_title": "Estudio institucional",
        "source_type": "Institucional",
        "source_url": "https://example.org/estudio",
        "assessment": "matiza",
        "reliability_reason": "La fuente describe su muestra, periodo, método y limitaciones de manera verificable.",
        "impact": "La decisión debe depender de la intervención posterior y no solamente de la precisión de la alerta.",
    }
    assert validate_verification(payload) == {}
    assert "source_url" in validate_verification(payload | {"source_url": "example.org"})


def test_challenge_accepts_alternative_or_counterargument() -> None:
    payload = {
        "limitation": "La recomendación no considera diferencias de cobertura digital entre los distintos programas.",
        "assumption": "Supone que una menor actividad digital representa necesariamente una necesidad de apoyo.",
        "missing_evidence": "Faltan resultados desagregados por programa, modalidad y tipo de intervención posterior.",
        "alternative": "Usar la alerta únicamente como invitación a una conversación voluntaria con revisión humana.",
        "counterargument": "",
    }
    assert validate_challenge(payload) == {}


def test_decision_and_reflection_require_human_tradeoff_and_comparable_evidence() -> None:
    decision = {
        "decision_type": "modificar",
        "keep": "Conservaría un piloto limitado con acompañamiento humano durante cada intervención.",
        "change": "Eliminaría decisiones automáticas y añadiría derecho de aclaración para cada estudiante.",
        "key_evidence": "Los resultados muestran diferencias de falsos positivos entre programas y modalidades.",
        "evidence_weight": "Esa diferencia pesa porque una intervención injusta puede afectar confianza y acceso a apoyos.",
        "tradeoff": "Acepto una operación más lenta para obtener mayor explicabilidad, revisión humana y confianza.",
    }
    assert validate_decision(decision) == {}

    reflection = {
        "final_response": "Realizaría un piloto voluntario, revisado por personas y auditado por programa antes de ampliar su uso.",
        "problem": "El reto es orientar apoyo temprano sin convertir correlaciones imperfectas en etiquetas permanentes.",
        "evidence": "Valoraría falsos positivos, impacto de las intervenciones y diferencias entre programas y modalidades.",
        "ai_critique": "La recomendación puede confundir actividad con necesidad y omitir desigualdades en la cobertura digital.",
        "decision": "El piloto es justificable sólo con consentimiento, revisión humana, auditoría y derecho a aclaración.",
        "change": "Mi postura incorporó criterios explícitos de justicia, explicabilidad y efectos de la intervención.",
        "learning": "Aprendí que la precisión de una alerta no garantiza por sí sola una intervención educativa útil.",
        "human_contribution": "Definí las salvaguardas y convertí la alerta en una invitación, no en una clasificación.",
        "uncertainty": "Aún desconozco el desempeño con datos reales de todos los programas.",
        "next_step": "Diseñaría una auditoría por subgrupos y una revisión con participación estudiantil.",
    }
    assert validate_reflection(reflection, 4) == {}
