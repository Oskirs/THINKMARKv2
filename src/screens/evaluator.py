"""Pantalla de aplicación y validación humana de la rúbrica."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.layout import demo_notice, screen_title


def render_v01(data: dict[str, Any]) -> None:
    screen_title("V01", "Aplicación y validación de la rúbrica", "Compara evidencia inicial y final; una persona evaluadora valida cada nivel.")
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
            initial.write(data["initial"][key])
            final.markdown("**Evidencia final**")
            final.write(data["final"][key])
            levels = data["delta"][key]
            st.caption(f"Evaluación demostrativa: nivel inicial {levels[0]} · nivel final {levels[1]} · delta {levels[1]-levels[0]:+d}")
    st.warning("El sistema calcula la diferencia; no sustituye la valoración humana ni expone razonamiento interno de la IA.")
    demo_notice("el paso 6.5")
