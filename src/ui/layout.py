"""Patrones visuales compartidos por todas las pantallas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import streamlit as st


def render_sidebar(groups: Mapping[str, Sequence[Any]], current: str, allowed: set[str]) -> str:
    st.markdown("#### Recorrido")
    options = [screen.screen_id for screens in groups.values() for screen in screens if screen.screen_id in allowed]
    labels = {
        screen.screen_id: f"{screen.screen_id} · {screen.label}"
        for screens in groups.values()
        for screen in screens
    }
    selected = st.selectbox(
        "Pantalla activa",
        options,
        index=options.index(current),
        format_func=labels.get,
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Sesión actual")
    st.code(st.session_state.session_id, language=None)
    if st.session_state.completed:
        if st.session_state.access_role == "evaluator":
            st.success("Sesión cerrada · vuelve a la cola")
        else:
            st.success("Recorrido completo")
    elif st.session_state.thinkmark_decided:
        status = "aprobado" if st.session_state.thinkmark_final else "no aprobado"
        st.success(f"ThinkMark {status} · completa E10")
    elif st.session_state.thinkmark_draft:
        st.info("Siguiente acción: E09 · revisar y decidir sobre tu ThinkMark")
    elif st.session_state.reasoning_evaluation.get("status") == "validated":
        st.success("Reasoning Delta validado · E08 disponible")
    elif st.session_state.reflection_submitted:
        st.success("Recorrido enviado · awaiting_review")
    elif st.session_state.decision_completed:
        st.info("Siguiente etapa: E07 · Reflect")
    elif st.session_state.challenge_completed:
        st.info("Siguiente etapa: E06 · Decide")
    elif st.session_state.verification_completed:
        st.info("Siguiente etapa: E05 · Challenge")
    elif st.session_state.coach_completed or st.session_state.coach_simulation_completed:
        st.info("Siguiente etapa: E04 · Verify")
    elif st.session_state.baseline_locked:
        st.info("Siguiente etapa: E03 · conversación con el AI Coach")
    elif st.session_state.consent_status:
        st.info("Completa E02 para habilitar el resto del recorrido.")
    else:
        st.info("Acepta las condiciones de E01 para crear o recuperar una sesión.")
    return selected


def render_progress(current: str) -> None:
    from src.navigation import SCREENS, get_screen

    screen = get_screen(current)
    st.progress(screen.step / len(SCREENS), text=f"Pantalla {screen.step} de {len(SCREENS)} · {screen.screen_id}")


def screen_title(screen_id: str, title: str, objective: str) -> None:
    st.markdown(f"<div class='tm-eyebrow'>{screen_id} · MVP THINKMARK</div>", unsafe_allow_html=True)
    st.title(title)
    st.write(objective)


def card(title: str, body: str) -> None:
    st.markdown(f"<div class='tm-card'><strong>{title}</strong><br><span class='tm-muted'>{body}</span></div>", unsafe_allow_html=True)


def demo_notice(next_phase: str) -> None:
    st.info(f"Vista demostrativa. La interacción y persistencia completa se implementarán en {next_phase}.")
