"""Reglas auditables para una oportunidad docente, sin diagnóstico ni ranking."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import re
from statistics import median
from typing import Any


DIMENSION_ORDER = ("problem", "evidence", "ai_critique", "decision")
INTERVENTIONS = {
    "problem": "Realizar un mapa breve de actores, restricciones y consecuencias antes de formular una solución.",
    "evidence": "Comparar dos fuentes en un mini-ejercicio sobre confiabilidad, relevancia y suficiencia.",
    "ai_critique": "Examinar una recomendación de IA e identificar un supuesto, una limitación y una alternativa propia.",
    "decision": "Usar una matriz breve que conecte evidencia, alternativas, consecuencias y trade-offs.",
}
TEACHER_PATTERN = re.compile(r"^DOC-[A-Z0-9][A-Z0-9-]{2,17}$")


def build_dashboard_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [record for record in records if record.get("consent_status")]
    evaluated = [record for record in eligible if record.get("reasoning_evaluation", {}).get("status") == "validated"]
    completed = [record for record in eligible if record.get("completed")]
    durations: list[float] = []
    for record in completed:
        start = record.get("consent_record", {}).get("accepted_at")
        end = record.get("completed_at")
        if start and end:
            try:
                from datetime import datetime
                minutes = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 60
                if 0 <= minutes <= 240:
                    durations.append(minutes)
            except ValueError:
                pass

    dimensions: dict[str, dict[str, Any]] = {}
    for key in DIMENSION_ORDER:
        items = [record["reasoning_evaluation"]["calculation"]["dimensions"][key] for record in evaluated]
        if items:
            dimensions[key] = {
                "label": items[0]["label"],
                "average_initial": round(sum(item["initial_score"] for item in items) / len(items), 2),
                "average_final": round(sum(item["final_score"] for item in items) / len(items), 2),
                "average_delta": round(sum(item["delta"] for item in items) / len(items), 2),
                "evidence_count": sum(bool(item.get("evidence_note")) for item in items),
            }
    summary = {
        "started": len(eligible),
        "completed": len(completed),
        "completion_rate": round(len(completed) / len(eligible), 4) if eligible else 0.0,
        "median_minutes": round(median(durations)) if durations else None,
        "evaluated": len(evaluated),
        "dimensions": dimensions,
    }
    if not dimensions:
        summary["proposal"] = {}
        return summary

    opportunity_key = min(DIMENSION_ORDER, key=lambda key: (dimensions[key]["average_final"], dimensions[key]["average_delta"]))
    strength_key = max(DIMENSION_ORDER, key=lambda key: (dimensions[key]["average_final"], dimensions[key]["average_delta"]))
    opportunity = dimensions[opportunity_key]
    strength = dimensions[strength_key]
    summary["proposal"] = {
        "learning_strength": (
            f"La mayor explicitación final se observa en {strength['label']} "
            f"(nivel final medio {strength['average_final']:.2f}; Δ {strength['average_delta']:+.2f})."
        ),
        "learning_opportunity": opportunity["label"],
        "opportunity_evidence": (
            f"{opportunity['evidence_count']} de {len(evaluated)} evaluaciones incluyen evidencia documentada; "
            f"el nivel final medio es {opportunity['average_final']:.2f} y el cambio medio {opportunity['average_delta']:+.2f}."
        ),
        "suggested_intervention": INTERVENTIONS[opportunity_key],
        "dimension_key": opportunity_key,
        "rule_version": "learning-opportunity-rules-v1",
    }
    return summary


def validate_teacher_decision(proposal: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    code = re.sub(r"[^A-Z0-9-]", "", str(payload.get("teacher_code", "")).strip().upper())
    if not TEACHER_PATTERN.fullmatch(code):
        errors["teacher_code"] = "Usa un código pseudónimo con formato DOC-XXXX."
    status = payload.get("teacher_validation_status")
    if status not in {"accepted", "adjusted", "rejected"}:
        errors["teacher_validation_status"] = "Selecciona aceptar, ajustar o rechazar."
    fields = ("learning_strength", "learning_opportunity", "opportunity_evidence", "suggested_intervention")
    for field in fields:
        if len(str(payload.get(field, "")).strip()) < 20:
            errors[field] = "Describe esta pieza con al menos 20 caracteres."
    changed = any(str(payload.get(field, "")).strip() != str(proposal.get(field, "")).strip() for field in fields)
    if status == "accepted" and changed:
        errors["teacher_validation_status"] = "Hay cambios; selecciona ‘Ajustada’."
    if status == "adjusted" and not changed:
        errors["teacher_validation_status"] = "Modifica al menos una pieza antes de validar como ajustada."
    if status == "rejected" and len(str(payload.get("teacher_note", "")).strip()) < 20:
        errors["teacher_note"] = "Explica brevemente por qué la propuesta no debe utilizarse."
    if not payload.get("teacher_confirmed"):
        errors["teacher_confirmed"] = "Confirma que una persona revisó la evidencia antes de decidir."
    return errors


def seal_teacher_decision(proposal: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if validate_teacher_decision(proposal, payload):
        raise ValueError("La validación docente está incompleta.")
    validated_at = datetime.now(UTC).isoformat()
    fields = ("learning_strength", "learning_opportunity", "opportunity_evidence", "suggested_intervention")
    record = {
        "proposal": proposal,
        "final": {field: str(payload[field]).strip() for field in fields},
        "teacher_code": re.sub(r"[^A-Z0-9-]", "", str(payload["teacher_code"]).strip().upper()),
        "teacher_user_id": str(payload.get("teacher_user_id", "")),
        "teacher_validation_status": payload["teacher_validation_status"],
        "teacher_note": str(payload.get("teacher_note", "")).strip(),
        "validated_at": validated_at,
    }
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    record["integrity_hash"] = hashlib.sha256(canonical).hexdigest()
    return record
