"""Pantalla de aplicación y validación humana de la rúbrica."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.layout import demo_notice, screen_title


def render_v01(data: dict[str, Any]) -> None:
    screen_title("V01", "Aplicación y validación de la rúbrica", "Compara evidencia inicial y final; una persona evaluadora valida cada nivel.")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))
    st.warning("Vista previa. La aplicación funcional de la rúbrica y el cálculo reproducible del Delta se implementarán en el paso 6.5.")
    initial_evidence = st.session_state.initial_responses
    final_evidence = st.session_state.final_responses.get("responses", {})
    dimensions = [
        ("Problema", "problem"),
        ("Evidencia", "evidence"),
        ("Análisis crítico de IA", "ai_critique"),
        ("Justificación de decisiones", "decision"),
    ]
    tabs = st.tabs([label for label, _ in dimensions])
    for tab, (label, key) in zip(tabs, dimensions):
        with tab:
            initial, final = st.columns(2)
            initial.markdown("**Evidencia inicial**")
            initial.write(initial_evidence.get(key, ""))
            final.markdown("**Evidencia final**")
            final.write(final_evidence.get(key, ""))
            st.caption("Pendiente de valoración humana con niveles 1–4.")
    st.warning("El sistema calcula la diferencia; no sustituye la valoración humana ni expone razonamiento interno de la IA.")
    demo_notice("el paso 6.5")
