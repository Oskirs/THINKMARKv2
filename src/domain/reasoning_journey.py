"""Validaciones del recorrido Verify–Challenge–Decide–Reflect."""

from __future__ import annotations

from difflib import SequenceMatcher
from urllib.parse import urlparse


def _required_text(payload: dict[str, str], requirements: dict[str, int]) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key, minimum in requirements.items():
        value = payload.get(key, "").strip()
        if len(value) < minimum:
            errors[key] = f"Desarrolla tu respuesta con al menos {minimum} caracteres."
    return errors


def validate_coach_bridge(payload: dict[str, str], *, require_claim: bool = True) -> dict[str, str]:
    requirements = {"response": 40}
    if require_claim:
        requirements["claim_to_verify"] = 20
    return _required_text(payload, requirements)


def validate_verification(payload: dict[str, str]) -> dict[str, str]:
    errors = _required_text(
        payload,
        {"claim": 20, "source_title": 5, "reliability_reason": 40, "impact": 40},
    )
    parsed = urlparse(payload.get("source_url", "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors["source_url"] = "Escribe una URL completa que comience con http:// o https://."
    if payload.get("assessment") not in {"confirma", "contradice", "matiza", "no es comprobable"}:
        errors["assessment"] = "Selecciona cómo se relaciona la fuente con la afirmación."
    if not payload.get("source_type"):
        errors["source_type"] = "Selecciona un tipo de fuente."
    return errors


def validate_challenge(payload: dict[str, str]) -> dict[str, str]:
    errors = _required_text(payload, {"limitation": 35, "assumption": 35, "missing_evidence": 35})
    alternative = payload.get("alternative", "").strip()
    counterargument = payload.get("counterargument", "").strip()
    if max(len(alternative), len(counterargument)) < 35:
        errors["own_elaboration"] = "Desarrolla una alternativa o un contraargumento propio con al menos 35 caracteres."
    reference = payload.get("reference_claim", "").strip().casefold()
    examined = [payload.get(key, "").strip().casefold() for key in ("limitation", "assumption", "missing_evidence", "alternative", "counterargument")]
    repeated = sum(bool(value) and SequenceMatcher(None, reference, value).ratio() > 0.88 for value in examined)
    if reference and repeated >= 3:
        errors["repetition"] = "Varias respuestas repiten la afirmación casi literalmente; explica límites y alternativas con tus propias palabras."
    return errors


def validate_decision(payload: dict[str, str]) -> dict[str, str]:
    errors = _required_text(
        payload,
        {"keep": 30, "change": 30, "key_evidence": 30, "evidence_weight": 35, "tradeoff": 35},
    )
    if payload.get("decision_type") not in {"mantener", "aceptar parcialmente", "modificar", "rechazar", "combinar"}:
        errors["decision_type"] = "Selecciona qué harás con la postura inicial."
    return errors


def validate_reflection(payload: dict[str, str], confidence: int) -> dict[str, str]:
    errors = _required_text(
        payload,
        {
            "final_response": 60,
            "problem": 40,
            "evidence": 40,
            "ai_critique": 40,
            "decision": 40,
            "change": 35,
            "learning": 35,
            "human_contribution": 35,
            "uncertainty": 25,
            "next_step": 25,
        },
    )
    if confidence not in range(1, 6):
        errors["confidence"] = "Selecciona una confianza final entre 1 y 5."
    return errors
