"""Reglas reproducibles para la evaluación humana y Reasoning Delta."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUBRIC_PATH = ROOT / "config" / "reasoning_delta_rubric.json"
EVALUATOR_PATTERN = re.compile(r"^EV-[A-Z0-9][A-Z0-9-]{2,17}$")
MIN_NOTE_CHARS = 30


def load_rubric(path: Path = RUBRIC_PATH) -> dict[str, Any]:
    rubric = json.loads(path.read_text(encoding="utf-8"))
    if [dimension["key"] for dimension in rubric["dimensions"]] != ["problem", "evidence", "ai_critique", "decision"]:
        raise ValueError("La rúbrica debe conservar las cuatro dimensiones comparables en el orden aprobado.")
    return rubric


def normalize_evaluator_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9-]", "", value.strip().upper())


def validate_evaluation(payload: dict[str, Any], *, require_confirmation: bool = False) -> dict[str, str]:
    errors: dict[str, str] = {}
    code = normalize_evaluator_code(str(payload.get("evaluator_code", "")))
    if not EVALUATOR_PATTERN.fullmatch(code):
        errors["evaluator_code"] = "Usa un código pseudónimo con formato EV-XXXX, sin nombre ni correo."

    rubric = load_rubric()
    ratings = payload.get("ratings", {})
    for dimension in rubric["dimensions"]:
        key = dimension["key"]
        rating = ratings.get(key, {})
        for moment in ("initial_score", "final_score"):
            score = rating.get(moment)
            if not isinstance(score, int) or isinstance(score, bool) or score not in range(1, 5):
                errors[f"{key}.{moment}"] = "Selecciona un nivel entero entre 1 y 4."
        note = str(rating.get("evidence_note", "")).strip()
        if len(note) < MIN_NOTE_CHARS:
            errors[f"{key}.evidence_note"] = f"Documenta la evidencia de la valoración con al menos {MIN_NOTE_CHARS} caracteres."
    if require_confirmation and not payload.get("human_validation_confirmed"):
        errors["confirmation"] = "Confirma que la valoración fue realizada por una persona usando evidencia observable."
    return errors


def calculate_reasoning_delta(payload: dict[str, Any]) -> dict[str, Any]:
    """Calcula únicamente aritmética sobre niveles ya asignados por una persona."""
    errors = validate_evaluation(payload)
    if errors:
        raise ValueError("La evaluación debe estar completa antes de calcular Reasoning Delta.")

    rubric = load_rubric()
    dimensions: dict[str, dict[str, Any]] = {}
    initial_scores: list[int] = []
    final_scores: list[int] = []
    for dimension in rubric["dimensions"]:
        key = dimension["key"]
        rating = payload["ratings"][key]
        initial_score = rating["initial_score"]
        final_score = rating["final_score"]
        dimensions[key] = {
            "label": dimension["label"],
            "initial_score": initial_score,
            "final_score": final_score,
            "delta": final_score - initial_score,
            "evidence_note": rating["evidence_note"].strip(),
        }
        initial_scores.append(initial_score)
        final_scores.append(final_score)

    average_initial = round(sum(initial_scores) / len(initial_scores), 2)
    average_final = round(sum(final_scores) / len(final_scores), 2)
    delta_average = round(average_final - average_initial, 2)
    max_delta = max(item["delta"] for item in dimensions.values())
    dominant = [item["label"] for item in dimensions.values() if item["delta"] == max_delta]
    lowest_final = min(item["final_score"] for item in dimensions.values())
    opportunities = [item["label"] for item in dimensions.values() if item["final_score"] == lowest_final]
    return {
        "dimensions": dimensions,
        "average_initial": average_initial,
        "average_final": average_final,
        "delta_average": delta_average,
        "dominant_change": dominant,
        "learning_opportunity_candidates": opportunities,
    }


def seal_evaluation(payload: dict[str, Any]) -> dict[str, Any]:
    errors = validate_evaluation(payload, require_confirmation=True)
    if errors:
        raise ValueError("La evaluación no puede validarse mientras existan campos incompletos.")
    rubric = load_rubric()
    record = {
        "status": "validated",
        "rubric_version": rubric["rubric_version"],
        "evaluator_code": normalize_evaluator_code(payload["evaluator_code"]),
        "ratings": payload["ratings"],
        "calculation": calculate_reasoning_delta(payload),
        "validated_at": datetime.now(UTC).isoformat(),
        "human_validation_confirmed": True,
    }
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    record["integrity_hash"] = hashlib.sha256(canonical).hexdigest()
    return record
