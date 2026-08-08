"""Dashboard docente orientado a oportunidades de aprendizaje."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui.layout import demo_notice, screen_title


def render_d01(data: dict[str, Any]) -> None:
    dash = data["dashboard"]
    screen_title("D01", "Faculty Learning Dashboard", "Convierte evidencia agregada en una oportunidad específica para intervenir.")
    cols = st.columns(3)
    cols[0].metric("Sesiones iniciadas", dash["started"])
    cols[1].metric("Sesiones completas", dash["completed"], delta=f"{dash['completed']/dash['started']:.0%}")
    cols[2].metric("Mediana", f"{dash['median_minutes']} min")

    chart_data = pd.DataFrame(
        {"Dimensión": ["Problema", "Evidencia", "Crítica de IA", "Decisión"], "Delta medio": [1.2, 0.6, 1.4, 1.1]}
    )
    fig = px.bar(chart_data, x="Dimensión", y="Delta medio", color="Delta medio", color_continuous_scale=["#D9D4FF", "#5B4BDB"])
    fig.update_layout(height=330, coloraxis_showscale=False, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f"<div class='tm-opportunity'><strong>Oportunidad de aprendizaje</strong><br>{dash['opportunity']}<br><br><strong>Intervención sugerida</strong><br>{dash['intervention']}</div>",
        unsafe_allow_html=True,
    )
    st.caption("Datos agregados de demostración; no se muestran rankings individuales.")
    demo_notice("el paso 6.7")
