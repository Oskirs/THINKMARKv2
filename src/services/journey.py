"""Orquestación de acceso, recuperación y línea base del paso 6.2."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import streamlit as st

from src.domain.baseline import seal_baseline
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
    "coach_turns": [],
    "verifications": [],
    "challenges": [],
    "decision": {},
    "final_responses": {},
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
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _hydrate(record: dict[str, Any]) -> None:
    for key in (
        "participant_id", "session_id", "current_stage", "consent_status", "consent_record",
        "baseline_draft", "baseline_confidence", "baseline_locked", "baseline_snapshot",
    ):
        if key in record:
            st.session_state[key] = record[key]
    snapshot = record.get("baseline_snapshot", {})
    st.session_state.initial_responses = snapshot.get("responses", {})


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
    (repository or LocalSessionRepository()).save(_record_from_state())


def allowed_screen_ids() -> set[str]:
    if not st.session_state.consent_status:
        return {"E01"}
    if not st.session_state.baseline_locked:
        return {"E01", "E02"}
    return {"E01", "E02", "E03", "E04", "E05", "E06", "E07", "V01", "E08", "E09", "E10", "D01"}


def resolve_screen_access(requested: str) -> str:
    if requested in allowed_screen_ids():
        return requested
    st.session_state.access_notice = "Completa y cierra tu posición inicial antes de acceder a esa pantalla."
    return "E02" if st.session_state.consent_status else "E01"


def go_to_screen(screen_id: str, *, sync_query: bool = True) -> None:
    target = resolve_screen_access(screen_id)
    st.session_state.current_screen = target
    if sync_query:
        st.query_params["screen"] = target
