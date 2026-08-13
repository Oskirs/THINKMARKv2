"""Punto de entrada del MVP navegable de THINKMARK."""

from __future__ import annotations

import streamlit as st

from src.navigation import get_screen, navigation_groups, screen_exists
from src.services.fixtures import load_demo_case
from src.services.journey import allowed_screen_ids, ensure_journey_state, go_to_screen, resolve_screen_access
from src.ui.brand import apply_brand, render_brand_header
from src.ui.layout import render_progress, render_sidebar


st.set_page_config(
    page_title="THINKMARK · Human Reasoning",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_brand()
ensure_journey_state()
demo_case = load_demo_case()

requested_screen = st.query_params.get("screen", st.session_state.current_screen)
if not screen_exists(requested_screen):
    requested_screen = "E01"
requested_screen = resolve_screen_access(requested_screen)
go_to_screen(requested_screen, sync_query=False)
if st.query_params.get("screen") != requested_screen:
    st.query_params["screen"] = requested_screen

with st.sidebar:
    render_brand_header(compact=True)
    selected = render_sidebar(navigation_groups(), st.session_state.current_screen, allowed_screen_ids())
    if selected != st.session_state.current_screen:
        go_to_screen(selected)
        st.rerun()

render_brand_header()
render_progress(st.session_state.current_screen)

screen = get_screen(st.session_state.current_screen)
screen.renderer(demo_case)

st.caption(
    "Prototipo THINKMARK v2 · Paso 6.4 · AI Coach con guardrails y fallback · "
    "La actividad no asigna calificación."
)
