"""Estado temporal y reglas mínimas de navegación del paso 6.1."""

from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_STATE: dict[str, Any] = {
    "participant_id": "TM-DEMO-024",
    "session_id": "SES-DEMO-2026",
    "current_screen": "E01",
    "current_stage": 0,
    "consent_status": False,
    "initial_responses": {},
    "coach_turns": [],
    "verifications": [],
    "challenges": [],
    "decision": {},
    "final_responses": {},
    "reasoning_evaluation": {},
    "thinkmark": {},
    "feedback": {},
}


def ensure_journey_state() -> None:
    for key, value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value


def go_to_screen(screen_id: str, *, sync_query: bool = True) -> None:
    st.session_state.current_screen = screen_id
    if sync_query:
        st.query_params["screen"] = screen_id
