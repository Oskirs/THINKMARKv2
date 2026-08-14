"""Orquestación del recorrido persistente THINKMARK hasta el paso 6.6."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any
from uuid import uuid4

import streamlit as st

from src.ai.coach import CoachResult, CoachService, FOCUS_LABELS, load_coach_config
from src.ai.thinkmark import ThinkMarkService, build_thinkmark_context, load_thinkmark_config
from src.domain.baseline import seal_baseline
from src.domain.completion import seal_completion, validate_facilitator_observations, validate_feedback
from src.domain.evaluation import normalize_evaluator_code, seal_evaluation, validate_evaluation
from src.domain.thinkmark import content_hash, normalize_content, seal_final, validate_student_decision
from src.domain.reasoning_journey import (
    validate_challenge,
    validate_coach_bridge,
    validate_decision,
    validate_reflection,
    validate_verification,
)
from src.repositories.contracts import SessionRepository
from src.repositories.factory import get_session_repository


INSTRUMENT_VERSION = "THINKMARK-v2"

DEFAULT_STATE: dict[str, Any] = {
    "participant_id": "",
    "session_id": "SIN-SESIÓN",
    "current_screen": "E01",
    "current_stage": 0,
    "consent_status": False,
    "consent_record": {},
    "academic_profile": {},
    "case_snapshot": {},
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
    "evaluation_draft": {},
    "reasoning_evaluation": {},
    "thinkmark": {},
    "thinkmark_draft": {},
    "thinkmark_corrections": {},
    "thinkmark_versions": [],
    "thinkmark_events": [],
    "thinkmark_final": {},
    "thinkmark_approval_status": "pending",
    "thinkmark_approved_at": "",
    "thinkmark_decided": False,
    "thinkmark_decided_at": "",
    "thinkmark_usage": {"requests": 0, "input_tokens": 0, "output_tokens": 0, "fallbacks": 0},
    "feedback": {},
    "feedback_draft": {},
    "facilitator_observations": {},
    "completion_integrity": {},
    "completed": False,
    "completed_at": "",
    "technical_incidents": "",
    "feedback_submitted": False,
    "access_role": "",
    "internal_authenticated": False,
    "internal_user_id": "",
    "internal_email": "",
    "internal_auth_mode": "",
    "internal_session_loaded": False,
    "selected_review_participant": "",
    "dashboard_access_logged": False,
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
        "academic_profile": st.session_state.academic_profile,
        "case_snapshot": st.session_state.case_snapshot,
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
        "evaluation_draft": st.session_state.evaluation_draft,
        "reasoning_evaluation": st.session_state.reasoning_evaluation,
        "thinkmark": st.session_state.thinkmark,
        "thinkmark_draft": st.session_state.thinkmark_draft,
        "thinkmark_corrections": st.session_state.thinkmark_corrections,
        "thinkmark_versions": st.session_state.thinkmark_versions,
        "thinkmark_events": st.session_state.thinkmark_events,
        "thinkmark_final": st.session_state.thinkmark_final,
        "thinkmark_approval_status": st.session_state.thinkmark_approval_status,
        "thinkmark_approved_at": st.session_state.thinkmark_approved_at,
        "thinkmark_decided": st.session_state.thinkmark_decided,
        "thinkmark_decided_at": st.session_state.thinkmark_decided_at,
        "thinkmark_usage": st.session_state.thinkmark_usage,
        "feedback": st.session_state.feedback,
        "feedback_draft": st.session_state.feedback_draft,
        "facilitator_observations": st.session_state.facilitator_observations,
        "completion_integrity": st.session_state.completion_integrity,
        "completed": st.session_state.completed,
        "completed_at": st.session_state.completed_at,
        "technical_incidents": st.session_state.technical_incidents,
        "feedback_submitted": st.session_state.feedback_submitted,
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _hydrate(record: dict[str, Any]) -> None:
    for key in (
        "participant_id", "session_id", "current_stage", "consent_status", "consent_record",
        "academic_profile", "case_snapshot",
        "baseline_draft", "baseline_confidence", "baseline_locked", "baseline_snapshot",
        "coach_simulation_completed", "coach_completed", "coach_bridge", "coach_turns",
        "coach_events", "ai_usage", "claim_to_verify",
        "verification_draft", "verifications", "verification_completed",
        "challenge_draft", "challenges", "challenge_completed",
        "decision_draft", "decision", "decision_completed",
        "final_draft", "final_confidence", "final_responses", "reflection_submitted", "session_status",
        "evaluation_draft", "reasoning_evaluation", "thinkmark", "thinkmark_draft",
        "thinkmark_corrections", "thinkmark_versions", "thinkmark_events", "thinkmark_final",
        "thinkmark_approval_status", "thinkmark_approved_at", "thinkmark_decided",
        "thinkmark_decided_at", "thinkmark_usage",
        "feedback", "feedback_draft", "facilitator_observations", "completion_integrity",
        "completed", "completed_at", "technical_incidents",
        "feedback_submitted",
    ):
        if key in record:
            st.session_state[key] = record[key]
    snapshot = record.get("baseline_snapshot", {})
    st.session_state.initial_responses = snapshot.get("responses", {})
    # Compatibilidad con sesiones creadas en el paso 6.3.
    if "coach_completed" not in record and record.get("coach_simulation_completed"):
        st.session_state.coach_completed = True


def reset_access_state() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def unload_review_session() -> None:
    auth = {
        "access_role": st.session_state.access_role,
        "internal_authenticated": st.session_state.internal_authenticated,
        "internal_user_id": st.session_state.internal_user_id,
        "internal_email": st.session_state.internal_email,
        "internal_auth_mode": st.session_state.internal_auth_mode,
    }
    for key, value in DEFAULT_STATE.items():
        st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value
    for key, value in auth.items():
        st.session_state[key] = value
    st.session_state.internal_session_loaded = False
    st.session_state.selected_review_participant = ""


def load_session_for_review(participant_id: str, repository: SessionRepository | None = None) -> bool:
    if st.session_state.access_role != "evaluator" or not st.session_state.internal_authenticated:
        raise PermissionError("Se requiere acceso de evaluador.")
    repository = repository or get_session_repository()
    record = repository.get(participant_id)
    if not record or not record.get("reflection_submitted"):
        return False
    _hydrate(record)
    repository.audit_access(
        st.session_state.internal_user_id, "evaluator", "open_review", "session", record["session_id"]
    )
    st.session_state.internal_session_loaded = True
    st.session_state.selected_review_participant = participant_id
    st.session_state.current_screen = "E10" if record.get("thinkmark_decided") else "V01"
    return True


def refresh_current_session(repository: SessionRepository | None = None) -> bool:
    if not st.session_state.participant_id:
        return False
    record = (repository or get_session_repository()).get(st.session_state.participant_id)
    if not record:
        return False
    _hydrate(record)
    st.session_state.access_notice = "Estado actualizado desde el almacenamiento compartido."
    return True


def create_or_resume_session(
    participant_id: str,
    academic_profile: dict[str, Any],
    case_snapshot: dict[str, Any],
    repository: SessionRepository | None = None,
) -> bool:
    """Devuelve True si recuperó una sesión previa."""
    if st.session_state.access_role != "student":
        raise PermissionError("El código de participante sólo puede utilizarse en el acceso estudiantil.")
    repository = repository or get_session_repository()
    previous = repository.get(participant_id)
    if previous:
        _hydrate(previous)
        if not previous.get("academic_profile"):
            # Compatibilidad: una sesión anterior ya cerrada conserva el caso transversal original.
            if previous.get("baseline_locked"):
                from src.services.academic_cases import legacy_academic_profile
                from src.services.fixtures import load_demo_case

                st.session_state.academic_profile = legacy_academic_profile()
                st.session_state.case_snapshot = load_demo_case()
            else:
                st.session_state.academic_profile = academic_profile.copy()
                st.session_state.case_snapshot = case_snapshot.copy()
            repository.save(_record_from_state())
        st.session_state.access_notice = "Sesión recuperada. Puedes continuar desde el último punto guardado."
        return True

    accepted_at = datetime.now(UTC).isoformat()
    st.session_state.participant_id = participant_id
    st.session_state.session_id = f"SES-{uuid4().hex[:10].upper()}"
    st.session_state.current_stage = 1
    st.session_state.consent_status = True
    st.session_state.session_status = "in_progress"
    st.session_state.academic_profile = academic_profile.copy()
    st.session_state.case_snapshot = case_snapshot.copy()
    st.session_state.consent_record = {
        "accepted_at": accepted_at,
        "voluntary_participation": True,
        "non_graded_activity": True,
        "anonymized_use_authorized": True,
        "instrument_version": INSTRUMENT_VERSION,
        "case_version": case_snapshot.get("case_version", case_snapshot.get("case_id", "sin-versión")),
        "academic_catalog_version": academic_profile.get("catalog_version", "sin-versión"),
    }
    repository.save(_record_from_state())
    st.session_state.access_notice = "Sesión creada. Tu código te permitirá recuperar este avance sin usar tu nombre."
    return False


def save_baseline_draft(responses: dict[str, str], confidence: int, repository: SessionRepository | None = None) -> None:
    if st.session_state.baseline_locked:
        raise ValueError("Tu primera respuesta ya está guardada y no puede modificarse.")
    st.session_state.baseline_draft = {key: value.strip() for key, value in responses.items()}
    st.session_state.baseline_confidence = confidence
    (repository or get_session_repository()).save(_record_from_state())


def close_baseline(responses: dict[str, str], confidence: int, case_id: str, repository: SessionRepository | None = None) -> None:
    if st.session_state.baseline_locked:
        raise ValueError("Tu primera respuesta ya está guardada y no puede modificarse.")
    snapshot = seal_baseline(responses, confidence, case_id)
    st.session_state.baseline_draft = snapshot["responses"].copy()
    st.session_state.baseline_confidence = confidence
    st.session_state.baseline_snapshot = snapshot
    st.session_state.initial_responses = snapshot["responses"].copy()
    st.session_state.baseline_locked = True
    st.session_state.current_stage = 2
    st.session_state.session_status = "baseline_locked"
    (repository or get_session_repository()).save(_record_from_state())


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
    repository: SessionRepository | None = None,
) -> None:
    """Genera la primera pregunta sólo una vez y conserva el resultado recuperable."""
    _ensure_reflection_open()
    if st.session_state.coach_turns or st.session_state.coach_completed:
        return
    service = coach_service or CoachService()
    result = service.next_question(case=case, initial_responses=st.session_state.initial_responses, answered_turns=[])
    _append_coach_question(result)
    (repository or get_session_repository()).save(_record_from_state())


def submit_coach_turn(
    response: str,
    claim_to_verify: str,
    *,
    continue_conversation: bool,
    case: dict[str, Any],
    coach_service: CoachService | None = None,
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    """Guarda primero la respuesta humana y después, si aplica, solicita otra pregunta."""
    _ensure_reflection_open()
    repository = repository or get_session_repository()
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


def save_verification(payload: dict[str, str], *, complete: bool, repository: SessionRepository | None = None) -> dict[str, str]:
    repository = repository or get_session_repository()
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


def save_challenge(payload: dict[str, str], *, complete: bool, repository: SessionRepository | None = None) -> dict[str, str]:
    repository = repository or get_session_repository()
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


def save_decision(payload: dict[str, str], *, complete: bool, repository: SessionRepository | None = None) -> dict[str, str]:
    repository = repository or get_session_repository()
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


def save_reflection(payload: dict[str, str], confidence: int, *, submit: bool, repository: SessionRepository | None = None) -> dict[str, str]:
    repository = repository or get_session_repository()
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


def save_evaluation(
    payload: dict[str, Any],
    *,
    validate: bool,
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    """Guarda un borrador o sella una valoración humana completa."""
    if st.session_state.access_role != "evaluator" or not st.session_state.internal_authenticated:
        return {"evaluation": "Se requiere una sesión autenticada con rol de evaluador."}
    if not st.session_state.reflection_submitted:
        return {"evaluation": "La reflexión final debe estar enviada antes de evaluar."}
    if st.session_state.reasoning_evaluation.get("status") == "validated":
        return {"evaluation": "Esta evaluación ya fue validada y no puede modificarse."}

    repository = repository or get_session_repository()
    normalized = {
        "evaluator_code": normalize_evaluator_code(str(payload.get("evaluator_code", ""))),
        "ratings": {
            key: {
                "initial_score": int(rating.get("initial_score", 1)),
                "final_score": int(rating.get("final_score", 1)),
                "evidence_note": str(rating.get("evidence_note", "")).strip(),
            }
            for key, rating in payload.get("ratings", {}).items()
        },
        "human_validation_confirmed": bool(payload.get("human_validation_confirmed")),
    }
    st.session_state.evaluation_draft = normalized
    errors = validate_evaluation(normalized, require_confirmation=validate)
    if errors:
        repository.save(_record_from_state())
        return errors
    if validate:
        st.session_state.reasoning_evaluation = seal_evaluation(normalized)
        st.session_state.session_status = "evaluated"
        st.session_state.current_stage = 8
    repository.save(_record_from_state())
    return {}


def generate_thinkmark(
    *,
    rejection_reason: str = "",
    service: ThinkMarkService | None = None,
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    """Crea una propuesta nueva y conserva cada versión generada como evidencia de origen."""
    if st.session_state.reasoning_evaluation.get("status") != "validated":
        return {"thinkmark": "Se requiere un Reasoning Delta validado antes de generar la ThinkMark."}
    if st.session_state.thinkmark_decided:
        return {"thinkmark": "Ya registraste una decisión final sobre esta ThinkMark."}
    config = load_thinkmark_config()
    versions = list(st.session_state.thinkmark_versions)
    if len(versions) >= int(config["max_versions"]):
        return {"regeneration": f"Se alcanzó el máximo de {config['max_versions']} propuestas para este MVP."}
    if versions and len(rejection_reason.strip()) < 12:
        return {"regeneration": "Explica brevemente qué no te representa antes de solicitar otra propuesta."}

    state = {key: st.session_state.get(key) for key in (
        "initial_responses", "coach_turns", "verifications", "challenges", "decision",
        "final_responses", "reasoning_evaluation",
    )}
    result = (service or ThinkMarkService(config=config)).generate(build_thinkmark_context(state))
    generated_at = datetime.now(UTC).isoformat()
    version_number = len(versions) + 1
    version = {
        "thinkmark_id": f"{st.session_state.session_id}-TM-{version_number}",
        "version_number": version_number,
        "content": result.content,
        "content_hash": content_hash(result.content),
        "generated_at": generated_at,
        "mode": result.mode,
        "model": result.model,
        "policy_version": result.policy_version,
        "prompt_version": result.prompt_version,
    }
    st.session_state.thinkmark_versions = versions + [version]
    st.session_state.thinkmark_draft = result.content.copy()
    st.session_state.thinkmark_corrections = result.content.copy()
    st.session_state.thinkmark_events = list(st.session_state.thinkmark_events) + ([{
        "event": "draft_rejected_for_regeneration",
        "rejected_version": version_number - 1,
        "reason": rejection_reason.strip(),
        "created_at": generated_at,
    }] if versions else [])
    usage = st.session_state.thinkmark_usage.copy()
    usage["requests"] = usage.get("requests", 0) + 1
    usage["input_tokens"] = usage.get("input_tokens", 0) + result.input_tokens
    usage["output_tokens"] = usage.get("output_tokens", 0) + result.output_tokens
    usage["fallbacks"] = usage.get("fallbacks", 0) + int(result.mode == "fallback")
    st.session_state.thinkmark_usage = usage
    if result.fallback_reason:
        st.session_state.thinkmark_events = list(st.session_state.thinkmark_events) + [{
            "event": "generation_fallback",
            "version": version_number,
            "reason": result.fallback_reason,
            "created_at": generated_at,
        }]
    st.session_state.current_stage = 9
    st.session_state.session_status = "thinkmark_review"
    (repository or get_session_repository()).save(_record_from_state())
    return {}


def save_thinkmark_corrections(
    content: dict[str, Any], repository: SessionRepository | None = None
) -> dict[str, str]:
    if st.session_state.thinkmark_decided:
        return {"thinkmark": "La decisión ya está sellada y no puede modificarse."}
    normalized = normalize_content(content)
    st.session_state.thinkmark_corrections = normalized
    (repository or get_session_repository()).save(_record_from_state())
    return {}


def decide_thinkmark(
    content: dict[str, Any],
    *,
    status: str,
    confirmed: bool,
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    if st.session_state.thinkmark_decided:
        return {"thinkmark": "La decisión ya está registrada y no puede modificarse."}
    if not st.session_state.thinkmark_draft:
        return {"thinkmark": "Genera y revisa primero una propuesta."}
    normalized = normalize_content(content)
    errors = validate_student_decision(st.session_state.thinkmark_draft, normalized, status, confirmed)
    if errors:
        st.session_state.thinkmark_corrections = normalized
        (repository or get_session_repository()).save(_record_from_state())
        return errors

    decided_at = datetime.now(UTC).isoformat()
    st.session_state.thinkmark_corrections = normalized
    st.session_state.thinkmark_approval_status = status
    st.session_state.thinkmark_decided = True
    st.session_state.thinkmark_decided_at = decided_at
    st.session_state.thinkmark_events = list(st.session_state.thinkmark_events) + [{
        "event": "student_decision",
        "status": status,
        "source_version": len(st.session_state.thinkmark_versions),
        "created_at": decided_at,
    }]
    if status in {"approved_as_generated", "approved_with_corrections"}:
        final = seal_final(normalized, status)
        st.session_state.thinkmark_final = final
        st.session_state.thinkmark = final["content"].copy()  # alias para consumidores posteriores
        st.session_state.thinkmark_approved_at = final["approved_at"]
        st.session_state.session_status = "thinkmark_approved"
    else:
        st.session_state.thinkmark_final = {}
        st.session_state.thinkmark = {}
        st.session_state.thinkmark_approved_at = ""
        st.session_state.session_status = "thinkmark_not_approved"
    st.session_state.current_stage = 10
    (repository or get_session_repository()).save(_record_from_state())
    return {}


def save_student_feedback(
    feedback: dict[str, Any],
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    if st.session_state.access_role != "student":
        return {"feedback": "Este bloque pertenece al estudiante."}
    if st.session_state.feedback_submitted:
        return {"feedback": "El feedback ya fue enviado y no puede modificarse."}
    if not st.session_state.thinkmark_decided:
        return {"feedback": "Primero registra una decisión explícita sobre tu ThinkMark."}
    errors = validate_feedback(feedback)
    st.session_state.feedback_draft = feedback.copy()
    repository = repository or get_session_repository()
    if errors:
        repository.save(_record_from_state())
        return errors
    st.session_state.feedback = {
        **{key: value for key, value in feedback.items()},
        "submitted_at": datetime.now(UTC).isoformat(),
    }
    st.session_state.feedback_submitted = True
    st.session_state.session_status = "awaiting_facilitator_closure"
    repository.save(_record_from_state())
    return {}


def finalize_session(
    observations: dict[str, Any],
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    if st.session_state.access_role != "evaluator" or not st.session_state.internal_authenticated:
        return {"completion": "Se requiere acceso autenticado de evaluador/facilitador."}
    if st.session_state.completed:
        return {"completion": "Esta sesión ya fue cerrada."}
    if not st.session_state.feedback_submitted or not st.session_state.feedback:
        return {"completion": "El estudiante debe enviar su feedback antes del cierre del facilitador."}
    errors = validate_facilitator_observations(observations)
    st.session_state.facilitator_observations = observations.copy()
    repository = repository or get_session_repository()
    if errors:
        repository.save(_record_from_state())
        return errors
    state = {key: st.session_state.get(key) for key in (
        "baseline_locked", "initial_responses", "verification_completed", "verifications",
        "reflection_submitted", "final_responses", "reasoning_evaluation", "thinkmark_decided",
    )}
    try:
        sealed = seal_completion(st.session_state.feedback, observations, state)
    except ValueError as exc:
        return {"completion": str(exc)}
    st.session_state.feedback = sealed["feedback"]
    st.session_state.facilitator_observations = sealed["facilitator_observations"]
    st.session_state.completion_integrity = {"checks": sealed["integrity_checks"], "integrity_hash": sealed["integrity_hash"]}
    st.session_state.technical_incidents = sealed["facilitator_observations"]["technical_incidents"]
    st.session_state.completed = True
    st.session_state.completed_at = sealed["completed_at"]
    st.session_state.session_status = "completed"
    st.session_state.current_stage = 11
    repository.save(_record_from_state())
    return {}


def complete_session(
    feedback: dict[str, Any],
    observations: dict[str, Any],
    repository: SessionRepository | None = None,
) -> dict[str, str]:
    """Compatibilidad para pruebas antiguas; el UI 6.8 separa estudiante y facilitador."""
    if st.session_state.completed:
        return {"completion": "Esta sesión ya fue cerrada y no puede enviarse otra vez."}
    if not st.session_state.thinkmark_decided:
        return {"completion": "Primero registra una decisión explícita sobre tu ThinkMark."}
    repository = repository or get_session_repository()
    st.session_state.feedback_draft = feedback.copy()
    st.session_state.facilitator_observations = observations.copy()
    feedback_errors = validate_feedback(feedback)
    observation_errors = validate_facilitator_observations(observations)
    errors = feedback_errors | observation_errors
    if errors:
        repository.save(_record_from_state())
        return errors

    state = {key: st.session_state.get(key) for key in (
        "baseline_locked", "initial_responses", "verification_completed", "verifications",
        "reflection_submitted", "final_responses", "reasoning_evaluation", "thinkmark_decided",
    )}
    try:
        sealed = seal_completion(feedback, observations, state)
    except ValueError as exc:
        return {"completion": str(exc)}
    st.session_state.feedback = sealed["feedback"]
    st.session_state.facilitator_observations = sealed["facilitator_observations"]
    st.session_state.completion_integrity = {
        "checks": sealed["integrity_checks"],
        "integrity_hash": sealed["integrity_hash"],
    }
    st.session_state.technical_incidents = sealed["facilitator_observations"]["technical_incidents"]
    st.session_state.completed = True
    st.session_state.completed_at = sealed["completed_at"]
    st.session_state.session_status = "completed"
    st.session_state.current_stage = 11
    repository.save(_record_from_state())
    return {}


def allowed_screen_ids() -> set[str]:
    role = st.session_state.access_role
    if role == "teacher":
        return {"D01"} if st.session_state.internal_authenticated else set()
    if role == "evaluator":
        if not st.session_state.internal_authenticated or not st.session_state.internal_session_loaded:
            return set()
        allowed = {"V01"}
        if st.session_state.thinkmark_decided:
            allowed.add("E10")
        return allowed
    if role != "student":
        return set()
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
    if st.session_state.reasoning_evaluation.get("status") == "validated":
        allowed.update({"E08", "E09"})
    if st.session_state.thinkmark_decided:
        allowed.add("E10")
    return allowed


def resume_screen_id() -> str:
    """Devuelve la etapa más avanzada disponible para una sesión recuperada."""
    if st.session_state.access_role == "teacher":
        return "D01"
    if st.session_state.access_role == "evaluator":
        return "E10" if st.session_state.thinkmark_decided else "V01"
    if st.session_state.completed or st.session_state.thinkmark_decided:
        return "E10"
    if st.session_state.reasoning_evaluation.get("status") == "validated":
        return "E09"
    if st.session_state.reflection_submitted:
        return "E07"
    if st.session_state.decision_completed:
        return "E07"
    if st.session_state.challenge_completed:
        return "E06"
    if st.session_state.verification_completed:
        return "E05"
    if st.session_state.coach_completed or st.session_state.coach_simulation_completed:
        return "E04"
    if st.session_state.baseline_locked:
        return "E03"
    return "E02"


def resolve_screen_access(requested: str) -> str:
    role = st.session_state.access_role
    if role == "teacher":
        return "D01"
    if role == "evaluator":
        return "E10" if requested == "E10" and st.session_state.thinkmark_decided else "V01"
    if requested in allowed_screen_ids():
        return requested
    if not st.session_state.consent_status:
        st.session_state.access_notice = "Acepta las condiciones para iniciar el recorrido."
        return "E01"
    if not st.session_state.baseline_locked:
        st.session_state.access_notice = "Completa y guarda tu primera respuesta antes de continuar."
        return "E02"
    sequence = [
        ("E03", True),
        ("E04", st.session_state.coach_completed or st.session_state.coach_simulation_completed),
        ("E05", st.session_state.verification_completed),
        ("E06", st.session_state.challenge_completed),
        ("E07", st.session_state.decision_completed),
        ("E08", st.session_state.reasoning_evaluation.get("status") == "validated"),
        ("E09", st.session_state.reasoning_evaluation.get("status") == "validated"),
        ("E10", st.session_state.thinkmark_decided),
        ("D01", st.session_state.completed),
    ]
    for screen_id, unlocked in sequence:
        if not unlocked:
            st.session_state.access_notice = "Completa la etapa actual para habilitar la siguiente."
            previous = {
                "E04": "E03", "E05": "E04", "E06": "E05", "E07": "E06",
                "E08": "E07", "E09": "E08", "E10": "E09", "D01": "E10",
            }
            return previous.get(screen_id, "E03")
    st.session_state.access_notice = "Completa la etapa actual para habilitar la siguiente."
    if st.session_state.completed:
        return "D01"
    if st.session_state.thinkmark_decided:
        return "E10"
    return "E09" if st.session_state.reasoning_evaluation.get("status") == "validated" else ("V01" if st.session_state.reflection_submitted else "E03")


def go_to_screen(screen_id: str, *, sync_query: bool = True) -> None:
    target = resolve_screen_access(screen_id)
    st.session_state.current_screen = target
    if sync_query:
        st.query_params["screen"] = target
