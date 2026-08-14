"""Validación y sellado del feedback y cierre íntegro del recorrido."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import re
from typing import Any


FEEDBACK_RATING_FIELDS: tuple[str, ...] = (
    "coach_helpfulness_rating",
    "verification_helpfulness_rating",
    "decision_agency_rating",
    "thinkmark_fidelity_rating",
    "reuse_intention_rating",
)

FACILITATOR_CHECK_FIELDS: tuple[str, ...] = (
    "check_completed_without_support",
    "check_evidence_appraised",
    "check_coach_non_resolutive",
    "check_four_dimensions_comparable",
    "check_thinkmark_approved",
)

FACILITATOR_PATTERN = re.compile(r"^FAC-[A-Z0-9][A-Z0-9-]{2,17}$")
MAX_OPEN_TEXT_CHARS = 1000


def normalize_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **{field: payload.get(field) for field in FEEDBACK_RATING_FIELDS},
        "most_useful": str(payload.get("most_useful", "")).strip(),
        "confusing_or_repetitive": str(payload.get("confusing_or_repetitive", "")).strip(),
    }


def validate_feedback(payload: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_feedback(payload)
    errors: dict[str, str] = {}
    for field in FEEDBACK_RATING_FIELDS:
        value = normalized[field]
        if not isinstance(value, int) or isinstance(value, bool) or value not in range(1, 6):
            errors[field] = "Selecciona una valoración entre 1 y 5."
    for field in ("most_useful", "confusing_or_repetitive"):
        if len(normalized[field]) > MAX_OPEN_TEXT_CHARS:
            errors[field] = f"Reduce el comentario a {MAX_OPEN_TEXT_CHARS} caracteres."
    return errors


def validate_facilitator_observations(payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    code = re.sub(r"[^A-Z0-9-]", "", str(payload.get("facilitator_code", "")).strip().upper())
    if not FACILITATOR_PATTERN.fullmatch(code):
        errors["facilitator_code"] = "Usa un código pseudónimo con formato FAC-XXXX."
    for field in FACILITATOR_CHECK_FIELDS:
        if payload.get(field) is not True:
            errors[field] = "El facilitador debe confirmar este control o documentar la incidencia antes de cerrar."
    incidents = str(payload.get("technical_incidents", "")).strip()
    if len(incidents) > MAX_OPEN_TEXT_CHARS:
        errors["technical_incidents"] = f"Reduce las incidencias a {MAX_OPEN_TEXT_CHARS} caracteres."
    if not payload.get("closure_confirmed"):
        errors["closure_confirmed"] = "Confirma que revisaste los controles antes de cerrar la sesión."
    return errors


def journey_integrity(state: dict[str, Any]) -> dict[str, bool]:
    """Comprueba presencia técnica; no sustituye los cinco controles del facilitador."""
    initial = state.get("initial_responses", {})
    final = state.get("final_responses", {}).get("responses", {})
    return {
        "baseline_locked": bool(state.get("baseline_locked") and all(initial.get(key) for key in ("problem", "evidence", "ai_critique", "decision"))),
        "evidence_traceable": bool(state.get("verification_completed") and state.get("verifications")),
        "reflection_submitted": bool(state.get("reflection_submitted") and all(final.get(key) for key in ("problem", "evidence", "ai_critique", "decision"))),
        "evaluation_validated": state.get("reasoning_evaluation", {}).get("status") == "validated",
        "thinkmark_decided": bool(state.get("thinkmark_decided")),
    }


def seal_completion(feedback: dict[str, Any], observations: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if validate_feedback(feedback) or validate_facilitator_observations(observations):
        raise ValueError("El cierre tiene campos incompletos.")
    integrity = journey_integrity(state)
    if not all(integrity.values()):
        raise ValueError("El recorrido no supera todos los controles técnicos de integridad.")
    completed_at = datetime.now(UTC).isoformat()
    record = {
        "feedback": normalize_feedback(feedback) | {"submitted_at": str(feedback.get("submitted_at") or completed_at)},
        "facilitator_observations": {
            "facilitator_code": re.sub(r"[^A-Z0-9-]", "", str(observations["facilitator_code"]).strip().upper()),
            **{field: True for field in FACILITATOR_CHECK_FIELDS},
            "technical_incidents": str(observations.get("technical_incidents", "")).strip(),
            "validated_at": completed_at,
        },
        "integrity_checks": integrity,
        "completed_at": completed_at,
    }
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    record["integrity_hash"] = hashlib.sha256(canonical).hexdigest()
    return record
