"""Validación y sellado de la línea base THINKMARK."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any


PARTICIPANT_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{5,19}$")
DIMENSIONS = ("problem", "evidence", "ai_critique", "decision")
MIN_RESPONSE_CHARS = 40


def normalize_participant_code(value: str) -> str:
    """Normaliza sin convertir el código en un dato personal."""
    return re.sub(r"\s+", "", value.strip().upper())


def validate_participant_code(value: str) -> tuple[str, str | None]:
    normalized = normalize_participant_code(value)
    if not PARTICIPANT_CODE_PATTERN.fullmatch(normalized):
        return normalized, "Usa de 6 a 20 caracteres: letras, números o guion. No escribas tu nombre, matrícula ni correo."
    return normalized, None


def validate_baseline(responses: dict[str, str], confidence: int) -> dict[str, str]:
    errors: dict[str, str] = {}
    for key in DIMENSIONS:
        value = responses.get(key, "").strip()
        if len(value) < MIN_RESPONSE_CHARS:
            missing = MIN_RESPONSE_CHARS - len(value)
            errors[key] = f"Desarrolla un poco más tu razonamiento ({missing} caracteres adicionales como mínimo)."
    if confidence not in range(1, 6):
        errors["confidence"] = "Selecciona una confianza entre 1 y 5."
    return errors


def seal_baseline(responses: dict[str, str], confidence: int, case_id: str) -> dict[str, Any]:
    errors = validate_baseline(responses, confidence)
    if errors:
        raise ValueError("La línea base está incompleta.")
    snapshot = {
        "case_id": case_id,
        "responses": {key: responses[key].strip() for key in DIMENSIONS},
        "confidence": confidence,
        "locked_at": datetime.now(UTC).isoformat(),
    }
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
    snapshot["integrity_hash"] = hashlib.sha256(canonical).hexdigest()
    return snapshot
