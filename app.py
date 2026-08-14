"""Punto de entrada del MVP navegable de THINKMARK."""

from __future__ import annotations

import streamlit as st

from src.navigation import get_screen, navigation_groups, screen_exists
from src.infrastructure.settings import ConfigurationError, load_settings
from src.screens.access import ROLE_LABELS, render_access_portal, render_review_queue
from src.services.fixtures import load_demo_case
from src.services.journey import allowed_screen_ids, ensure_journey_state, go_to_screen, reset_access_state, resolve_screen_access
from src.ui.brand import apply_brand, render_brand_header
from src.ui.layout import render_progress, render_sidebar


st.set_page_config(
    page_title="THINKMARK · Human Reasoning",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_brand()
ensure_journey_state()
demo_case = load_demo_case()

try:
    runtime_settings = load_settings()
except ConfigurationError as exc:
    st.error(f"Configuración de publicación incompleta: {exc}")
    st.info("La aplicación se detuvo para evitar usar almacenamiento local por accidente en una publicación multiusuario.")
    st.stop()

if not st.session_state.access_role:
    render_brand_header()
    render_access_portal()
    st.caption("Prototipo THINKMARK v2 · Paso 6.8.1 · Acceso separado, lenguaje claro y diseño móvil")
    st.stop()

if st.session_state.access_role == "evaluator" and not st.session_state.internal_session_loaded:
    render_brand_header()
    render_review_queue()
    if st.button("Cerrar acceso interno"):
        reset_access_state()
        st.query_params.clear()
        st.rerun()
    st.stop()

requested_screen = st.query_params.get("screen", st.session_state.current_screen)
if not screen_exists(requested_screen):
    requested_screen = "E01"
requested_screen = resolve_screen_access(requested_screen)
go_to_screen(requested_screen, sync_query=False)
if st.query_params.get("screen") != requested_screen:
    st.query_params["screen"] = requested_screen

with st.sidebar:
    render_brand_header(compact=True)
    st.caption(f"Rol: {ROLE_LABELS.get(st.session_state.access_role, st.session_state.access_role)}")
    st.caption("Persistencia: " + ("Supabase" if runtime_settings.uses_supabase else "local de demostración"))
    if st.button("Cerrar sesión / cambiar rol", use_container_width=True):
        reset_access_state()
        st.query_params.clear()
        st.rerun()
    selected = render_sidebar(navigation_groups(), st.session_state.current_screen, allowed_screen_ids())
    if selected != st.session_state.current_screen:
        go_to_screen(selected)
        st.rerun()

render_brand_header()
render_progress(st.session_state.current_screen)

screen = get_screen(st.session_state.current_screen)
screen.renderer(demo_case)

st.caption(
    "Prototipo THINKMARK v2 · Paso 6.8.1 · Accesibilidad móvil y lenguaje claro · "
    "La actividad no asigna calificación."
)
