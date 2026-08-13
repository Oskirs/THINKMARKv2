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
    if st.session_state.baseline_locked:
        st.success("Línea base cerrada · recorrido habilitado")
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
    st.markdown(f"<div class='tm-eyebrow'>{screen_id} · PROTOTIPO NAVEGABLE</div>", unsafe_allow_html=True)
    st.title(title)
    st.write(objective)


def card(title: str, body: str) -> None:
    st.markdown(f"<div class='tm-card'><strong>{title}</strong><br><span class='tm-muted'>{body}</span></div>", unsafe_allow_html=True)


def demo_notice(next_phase: str) -> None:
    st.info(f"Vista demostrativa. La interacción y persistencia completa se implementarán en {next_phase}.")
