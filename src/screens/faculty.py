"""Dashboard docente orientado a oportunidades de aprendizaje."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.layout import demo_notice, screen_title


def render_d01(data: dict[str, Any]) -> None:
    dash = data["dashboard"]
    screen_title("D01", "Faculty Learning Dashboard", "Convierte evidencia agregada en una oportunidad específica para intervenir.")
    cols = st.columns(3)
    cols[0].metric("Sesiones iniciadas", dash["started"])
    cols[1].metric("Sesiones completas", dash["completed"], delta=f"{dash['completed']/dash['started']:.0%}")
    cols[2].metric("Mediana", f"{dash['median_minutes']} min")

    chart_data = [
        {"Dimensión": "Problema", "Delta medio": 1.2},
        {"Dimensión": "Evidencia", "Delta medio": 0.6},
        {"Dimensión": "Crítica de IA", "Delta medio": 1.4},
        {"Dimensión": "Decisión", "Delta medio": 1.1},
    ]
    st.markdown("#### Delta medio por dimensión")
    st.bar_chart(
        chart_data,
        x="Dimensión",
        y="Delta medio",
        horizontal=True,
        color="#76232F",
        height=300,
    )
    st.markdown(
        f"<div class='tm-opportunity'><strong>Oportunidad de aprendizaje</strong><br>{dash['opportunity']}<br><br><strong>Intervención sugerida</strong><br>{dash['intervention']}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Datos agregados de demostración; no se muestran rankings individuales.")
    demo_notice("el paso 6.7")
