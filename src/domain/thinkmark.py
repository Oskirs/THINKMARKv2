"""Reglas de dominio para una Human Reasoning Signature revisable y aprobada."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any


THINKMARK_FIELDS: tuple[str, ...] = (
    "tm_initial_position",
    "tm_problem_reframed",
    "tm_evidence_reviewed",
    "tm_evidence_appraisal",
    "tm_ai_analysis",
    "tm_final_decision",
    "tm_reasoning_change",
    "tm_personal_contribution",
    "tm_remaining_limits",
)

THINKMARK_LABELS = {
    "tm_initial_position": "Posición inicial",
    "tm_problem_reframed": "Problema reformulado",
    "tm_evidence_reviewed": "Evidencia revisada",
    "tm_evidence_appraisal": "Valoración de la evidencia",
    "tm_ai_analysis": "Análisis crítico de IA",
    "tm_final_decision": "Decisión final",
    "tm_reasoning_change": "Cambio en el razonamiento",
    "tm_personal_contribution": "Contribución propia",
    "tm_remaining_limits": "Límites e incertidumbre pendiente",
}

MIN_SECTION_CHARS = 12
MAX_SECTION_CHARS = 1200


def normalize_content(content: dict[str, Any]) -> dict[str, str]:
    return {field: str(content.get(field, "")).strip() for field in THINKMARK_FIELDS}


def validate_content(content: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_content(content)
    errors: dict[str, str] = {}
    for field, value in normalized.items():
        if len(value) < MIN_SECTION_CHARS:
            errors[field] = f"Escribe al menos {MIN_SECTION_CHARS} caracteres."
        elif len(value) > MAX_SECTION_CHARS:
            errors[field] = f"Reduce esta sección a {MAX_SECTION_CHARS} caracteres."
    return errors


def content_hash(content: dict[str, Any]) -> str:
    canonical = json.dumps(normalize_content(content), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def seal_final(content: dict[str, Any], status: str) -> dict[str, Any]:
    if status not in {"approved_as_generated", "approved_with_corrections"}:
        raise ValueError("Sólo una ThinkMark aprobada puede convertirse en versión final.")
    errors = validate_content(content)
    if errors:
        raise ValueError("La ThinkMark no contiene las nueve secciones completas.")
    approved_at = datetime.now(UTC).isoformat()
    normalized = normalize_content(content)
    return {
        "content": normalized,
        "approval_status": status,
        "approved_at": approved_at,
        "integrity_hash": content_hash(normalized),
    }


def validate_student_decision(
    draft: dict[str, Any],
    edited: dict[str, Any],
    status: str,
    confirmed: bool,
) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not confirmed:
        errors["confirmation"] = "Confirma que revisaste la representación antes de decidir."
    errors.update(validate_content(edited))
    changed = normalize_content(draft) != normalize_content(edited)
    if status == "approved_as_generated" and changed:
        errors["decision"] = "Hay cambios en el texto; selecciona ‘Corregir y aprobar’."
    if status == "approved_with_corrections" and not changed:
        errors["decision"] = "Modifica al menos una sección antes de aprobar con correcciones."
    if status not in {"approved_as_generated", "approved_with_corrections", "not_approved"}:
        errors["decision"] = "Selecciona una decisión válida."
    return errors
