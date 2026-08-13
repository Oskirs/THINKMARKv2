"""Orquestación del recorrido persistente THINKMARK hasta el paso 6.4."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any
from uuid import uuid4

import streamlit as st

from src.ai.coach import CoachResult, CoachService, FOCUS_LABELS, load_coach_config
from src.domain.baseline import seal_baseline
from src.domain.reasoning_journey import (
    validate_challenge,
    validate_coach_bridge,
    validate_decision,
    validate_reflection,
    validate_verification,
)
from src.repositories.local_sessions import LocalSessionRepository


INSTRUMENT_VERSION = "THINKMARK-v2"
CASE_VERSION = "CASO-DEMO-01-v1"

DEFAULT_STATE: dict[str, Any] = {
    "participant_id": "",
    "session_id": "SIN-SESIÓN",
    "current_screen": "E01",
    "current_stage": 0,
    "consent_status": False,
    "consent_record": {},
    "baseline_draft": {},
    "baseline_confidence": 3,
    "baseline_locked": False,
    "baseline_snapshot": {},
    "initial_responses": {},
    "coach_simulation_completed": False,
    "coach_completed": False,
    "coach_bridge": {},
    "coach_turns": [],
    "coach_events": [],
    "ai_usage": {"requests": 0, "input_tokens": 0, "output_tokens": 0, "fallbacks": 0},
    "claim_to_verify": "",
    "verification_draft": {},
    "verifications": [],
    "verification_completed": False,
    "challenge_draft": {},
    "challenges": [],
    "challenge_completed": False,
    "decision_draft": {},
    "decision": {},
    "decision_completed": False,
    "final_draft": {},
    "final_confidence": 3,
    "final_responses": {},
    "reflection_submitted": False,
    "session_status": "not_started",
    "reasoning_evaluation": {},
    "thinkmark": {},
    "feedback": {},
    "access_notice": "",
}


def ensure_journey_state() -> None:
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value


def _record_from_state() -> dict[str, Any]:
    return {
        "participant_id": st.session_state.participant_id,
        "session_id": st.session_state.session_id,
        "current_stage": st.session_state.current_stage,
        "consent_status": st.session_state.consent_status,
        "consent_record": st.session_state.consent_record,
        "baseline_draft": st.session_state.baseline_draft,
        "baseline_confidence": st.session_state.baseline_confidence,
        "baseline_locked": st.session_state.baseline_locked,
        "baseline_snapshot": st.session_state.baseline_snapshot,
        "coach_simulation_completed": st.session_state.coach_simulation_completed,
        "coach_completed": st.session_state.coach_completed,
        "coach_bridge": st.session_state.coach_bridge,
        "coach_turns": st.session_state.coach_turns,
        "coach_events": st.session_state.coach_events,
        "ai_usage": st.session_state.ai_usage,
        "claim_to_verify": st.session_state.claim_to_verify,
        "verification_draft": st.session_state.verification_draft,
        "verifications": st.session_state.verifications,
        "verification_completed": st.session_state.verification_completed,
        "challenge_draft": st.session_state.challenge_draft,
        "challenges": st.session_state.challenges,
        "challenge_completed": st.session_state.challenge_completed,
        "decision_draft": st.session_state.decision_draft,
        "decision": st.session_state.decision,
        "decision_completed": st.session_state.decision_completed,
        "final_draft": st.session_state.final_draft,
        "final_confidence": st.session_state.final_confidence,
        "final_responses": st.session_state.final_responses,
        "reflection_submitted": st.session_state.reflection_submitted,
        "session_status": st.session_state.session_status,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _hydrate(record: dict[str, Any]) -> None:
    for key in (
        "participant_id", "session_id", "current_stage", "consent_status", "consent_record",
        "baseline_draft", "baseline_confidence", "baseline_locked", "baseline_snapshot",
        "coach_simulation_completed", "coach_completed", "coach_bridge", "coach_turns",
        "coach_events", "ai_usage", "claim_to_verify",
        "verification_draft", "verifications", "verification_completed",
        "challenge_draft", "challenges", "challenge_completed",
        "decision_draft", "decision", "decision_completed",
        "final_draft", "final_confidence", "final_responses", "reflection_submitted", "session_status",
    ):
        if key in record:
            st.session_state[key] = record[key]
    snapshot = record.get("baseline_snapshot", {})
    st.session_state.initial_responses = snapshot.get("responses", {})
    # Compatibilidad con sesiones creadas en el paso 6.3.
    if "coach_completed" not in record and record.get("coach_simulation_completed"):
        st.session_state.coach_completed = True


def create_or_resume_session(participant_id: str, repository: LocalSessionRepository | None = None) -> bool:
    """Devuelve True si recuperó una sesión previa."""
    repository = repository or LocalSessionRepository()
    previous = repository.get(participant_id)
    if previous:
        _hydrate(previous)
        st.session_state.access_notice = "Sesión recuperada. Puedes continuar desde el último punto guardado."
        return True

    accepted_at = datetime.now(UTC).isoformat()
    st.session_state.participant_id = participant_id
    st.session_state.session_id = f"SES-{uuid4().hex[:10].upper()}"
    st.session_state.current_stage = 1
    st.session_state.consent_status = True
    st.session_state.session_status = "in_progress"
    st.session_state.consent_record = {
        "accepted_at": accepted_at,
        "voluntary_participation": True,
        "non_graded_activity": True,
        "anonymized_use_authorized": True,
        "instrument_version": INSTRUMENT_VERSION,
        "case_version": CASE_VERSION,
    }
    repository.save(_record_from_state())
    st.session_state.access_notice = "Sesión creada. Tu código pseudónimo permite recuperar este avance."
    return False


def save_baseline_draft(responses: dict[str, str], confidence: int, repository: LocalSessionRepository | None = None) -> None:
    if st.session_state.baseline_locked:
        raise ValueError("La línea base ya está cerrada.")
    st.session_state.baseline_draft = {key: value.strip() for key, value in responses.items()}
    st.session_state.baseline_confidence = confidence
    (repository or LocalSessionRepository()).save(_record_from_state())


def close_baseline(responses: dict[str, str], confidence: int, case_id: str, repository: LocalSessionRepository | None = None) -> None:
    if st.session_state.baseline_locked:
        raise ValueError("La línea base ya está cerrada.")
    snapshot = seal_baseline(responses, confidence, case_id)
    st.session_state.baseline_draft = snapshot["responses"].copy()
    st.session_state.baseline_confidence = confidence
    st.session_state.baseline_snapshot = snapshot
    st.session_state.initial_responses = snapshot["responses"].copy()
    st.session_state.baseline_locked = True
    st.session_state.current_stage = 2
    st.session_state.session_status = "baseline_locked"
    (repository or LocalSessionRepository()).save(_record_from_state())


def _ensure_reflection_open() -> None:
    if st.session_state.reflection_submitted:
        raise ValueError("El recorrido ya fue enviado a revisión.")


def _append_coach_question(result: CoachResult) -> None:
    focus_key = next((key for key, label in FOCUS_LABELS.items() if label == result.focus_dimension), "evidence")
    st.session_state.coach_turns.append({
        "turn_number": len(st.session_state.coach_turns) + 1,
        "focus_key": focus_key,
        "focus": result.focus_dimension,
        "question": result.question,
        "response": "",
        "mode": result.mode,
        "model": result.model,
        "policy_version": result.policy_version,
        "prompt_version": result.prompt_version,
        "safety_triggered": result.safety_triggered,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "generated_at": datetime.now(UTC).isoformat(),
    })
    usage = st.session_state.ai_usage.copy()
    usage["requests"] = usage.get("requests", 0) + 1
    usage["input_tokens"] = usage.get("input_tokens", 0) + result.input_tokens
    usage["output_tokens"] = usage.get("output_tokens", 0) + result.output_tokens
    usage["fallbacks"] = usage.get("fallbacks", 0) + int(result.mode == "fallback")
    st.session_state.ai_usage = usage
    if result.fallback_reason:
        st.session_state.coach_events.append({
            "event": "coach_fallback",
            "turn_number": len(st.session_state.coach_turns),
            "reason": result.fallback_reason,
            "created_at": datetime.now(UTC).isoformat(),
        })


def start_coach(
    case: dict[str, Any],
    *,
    coach_service: CoachService | None = None,
    repository: LocalSessionRepository | None = None,
) -> None:
    """Genera la primera pregunta sólo una vez y conserva el resultado recuperable."""
    _ensure_reflection_open()
    if st.session_state.coach_turns or st.session_state.coach_completed:
        return
    service = coach_service or CoachService()
    result = service.next_question(case=case, initial_responses=st.session_state.initial_responses, answered_turns=[])
    _append_coach_question(result)
    (repository or LocalSessionRepository()).save(_record_from_state())


def submit_coach_turn(
    response: str,
    claim_to_verify: str,
    *,
    continue_conversation: bool,
    case: dict[str, Any],
    coach_service: CoachService | None = None,
    repository: LocalSessionRepository | None = None,
) -> dict[str, str]:
    """Guarda primero la respuesta humana y después, si aplica, solicita otra pregunta."""
    _ensure_reflection_open()
    repository = repository or LocalSessionRepository()
    response = response.strip()
    claim_to_verify = claim_to_verify.strip()
    payload = {"response": response, "claim_to_verify": claim_to_verify}
    errors = validate_coach_bridge(payload, require_claim=not continue_conversation)
    if not st.session_state.coach_turns:
        errors["coach"] = "Inicia el Coach antes de responder."
    elif st.session_state.coach_turns[-1].get("response"):
        errors["coach"] = "La pregunta actual ya tiene una respuesta registrada."
    if errors:
        st.session_state.coach_bridge = payload | {"turn_number": len(st.session_state.coach_turns)}
        repository.save(_record_from_state())
        return errors

    # La evidencia humana se persiste antes de cualquier llamada externa.
    turns = [turn.copy() for turn in st.session_state.coach_turns]
    turns[-1]["response"] = response
    turns[-1]["answered_at"] = datetime.now(UTC).isoformat()
    st.session_state.coach_turns = turns
    st.session_state.coach_bridge = payload | {"turn_number": len(turns)}
    repository.save(_record_from_state())

    config = load_coach_config()
    if continue_conversation and len(turns) < int(config["max_turns"]):
        result = (coach_service or CoachService(config=config)).next_question(
            case=case,
            initial_responses=st.session_state.initial_responses,
            answered_turns=turns,
        )
        _append_coach_question(result)
        st.session_state.coach_bridge = {"response": "", "claim_to_verify": claim_to_verify, "turn_number": len(turns) + 1}
        repository.save(_record_from_state())
        return {}

    if continue_conversation:
        return {"coach": f"Alcanzaste el máximo de {config['max_turns']} preguntas. Define una afirmación y cierra el Coach."}

    st.session_state.claim_to_verify = claim_to_verify
    st.session_state.coach_completed = True
    st.session_state.coach_simulation_completed = True  # alias de compatibilidad para rutas 6.3
    st.session_state.current_stage = 3
    repository.save(_record_from_state())
    return {}


def save_verification(payload: dict[str, str], *, complete: bool, repository: LocalSessionRepository | None = None) -> dict[str, str]:
    repository = repository or LocalSessionRepository()
    _ensure_reflection_open()
    st.session_state.verification_draft = {key: value.strip() if isinstance(value, str) else value for key, value in payload.items()}
    if complete:
        errors = validate_verification(payload)
        if errors:
            repository.save(_record_from_state())
            return errors
        record = st.session_state.verification_draft | {"completed_at": datetime.now(UTC).isoformat()}
        st.session_state.verifications = [record]
        st.session_state.verification_completed = True
        st.session_state.current_stage = max(st.session_state.current_stage, 4)
    repository.save(_record_from_state())
    return {}


def save_challenge(payload: dict[str, str], *, complete: bool, repository: LocalSessionRepository | None = None) -> dict[str, str]:
    repository = repository or LocalSessionRepository()
    _ensure_reflection_open()
    st.session_state.challenge_draft = {key: value.strip() for key, value in payload.items()}
    if complete:
        errors = validate_challenge(payload)
        if errors:
            repository.save(_record_from_state())
            return errors
        record = st.session_state.challenge_draft | {"completed_at": datetime.now(UTC).isoformat()}
        st.session_state.challenges = [record]
        st.session_state.challenge_completed = True
        st.session_state.current_stage = max(st.session_state.current_stage, 5)
    repository.save(_record_from_state())
    return {}


def save_decision(payload: dict[str, str], *, complete: bool, repository: LocalSessionRepository | None = None) -> dict[str, str]:
    repository = repository or LocalSessionRepository()
    _ensure_reflection_open()
    st.session_state.decision_draft = {key: value.strip() for key, value in payload.items()}
    if complete:
        errors = validate_decision(payload)
        if errors:
            repository.save(_record_from_state())
            return errors
        st.session_state.decision = st.session_state.decision_draft | {"completed_at": datetime.now(UTC).isoformat()}
        st.session_state.decision_completed = True
        st.session_state.current_stage = max(st.session_state.current_stage, 6)
    repository.save(_record_from_state())
    return {}


def save_reflection(payload: dict[str, str], confidence: int, *, submit: bool, repository: LocalSessionRepository | None = None) -> dict[str, str]:
    repository = repository or LocalSessionRepository()
    _ensure_reflection_open()
    st.session_state.final_draft = {key: value.strip() for key, value in payload.items()}
    st.session_state.final_confidence = confidence
    if submit:
        errors = validate_reflection(payload, confidence)
        if errors:
            repository.save(_record_from_state())
            return errors
        st.session_state.final_responses = {
            "responses": st.session_state.final_draft.copy(),
            "confidence": confidence,
            "submitted_at": datetime.now(UTC).isoformat(),
        }
        canonical = json.dumps(st.session_state.final_responses, ensure_ascii=False, sort_keys=True).encode("utf-8")
        st.session_state.final_responses["integrity_hash"] = hashlib.sha256(canonical).hexdigest()
        st.session_state.reflection_submitted = True
        st.session_state.session_status = "awaiting_review"
        st.session_state.current_stage = 7
    repository.save(_record_from_state())
    return {}


def allowed_screen_ids() -> set[str]:
    if not st.session_state.consent_status:
        return {"E01"}
    if not st.session_state.baseline_locked:
        return {"E01", "E02"}
    allowed = {"E01", "E02", "E03"}
    if st.session_state.coach_completed or st.session_state.coach_simulation_completed:
        allowed.add("E04")
    if st.session_state.verification_completed:
        allowed.add("E05")
    if st.session_state.challenge_completed:
        allowed.add("E06")
    if st.session_state.decision_completed:
        allowed.add("E07")
    if st.session_state.reflection_submitted:
        allowed.add("V01")
    return allowed


def resolve_screen_access(requested: str) -> str:
    if requested in allowed_screen_ids():
        return requested
    if not st.session_state.consent_status:
        st.session_state.access_notice = "Acepta las condiciones para iniciar el recorrido."
        return "E01"
    if not st.session_state.baseline_locked:
        st.session_state.access_notice = "Completa y cierra tu posición inicial antes de continuar."
        return "E02"
    sequence = [
        ("E03", True),
        ("E04", st.session_state.coach_completed or st.session_state.coach_simulation_completed),
        ("E05", st.session_state.verification_completed),
        ("E06", st.session_state.challenge_completed),
        ("E07", st.session_state.decision_completed),
        ("V01", st.session_state.reflection_submitted),
    ]
    for screen_id, unlocked in sequence:
        if not unlocked:
            st.session_state.access_notice = "Completa la etapa actual para habilitar la siguiente."
            previous = {"E04": "E03", "E05": "E04", "E06": "E05", "E07": "E06", "V01": "E07"}
            return previous.get(screen_id, "E03")
    st.session_state.access_notice = "La evaluación Reasoning Delta corresponde al paso 6.5."
    return "V01" if st.session_state.reflection_submitted else "E03"


def go_to_screen(screen_id: str, *, sync_query: bool = True) -> None:
    target = resolve_screen_access(screen_id)
    st.session_state.current_screen = target
    if sync_query:
        st.query_params["screen"] = target
