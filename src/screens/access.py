"""Portal inicial que separa estudiante, evaluación y docencia."""

from __future__ import annotations

import streamlit as st

from src.infrastructure.settings import load_settings
from src.repositories.factory import get_session_repository
from src.services.auth import InternalAuthService
from src.services.journey import load_session_for_review


ROLE_LABELS = {
    "student": "Estudiante",
    "evaluator": "Evaluador / facilitador",
    "teacher": "Profesor",
}


def render_access_portal() -> None:
    st.markdown("<div class='tm-eyebrow'>ACCESO · THINKMARK</div>", unsafe_allow_html=True)
    st.title("Selecciona tu espacio de trabajo")
    st.write("Cada rol tiene una ruta y permisos distintos. El código del estudiante sólo permite entrar a su actividad.")
    role = st.radio(
        "Tipo de acceso",
        list(ROLE_LABELS),
        format_func=ROLE_LABELS.get,
        horizontal=True,
        label_visibility="collapsed",
    )
    if role == "student":
        st.info("Continuarás con un código que no contiene tu nombre. No se solicitará matrícula ni correo.")
        if st.button("Entrar al recorrido del estudiante", type="primary", use_container_width=True):
            st.session_state.access_role = "student"
            st.session_state.internal_authenticated = False
            st.session_state.current_screen = "E01"
            st.rerun()
        return

    settings = load_settings()
    title = "evaluación y facilitación" if role == "evaluator" else "dashboard docente"
    st.subheader(f"Acceso interno · {title}")
    if settings.uses_supabase:
        identifier = st.text_input("Correo institucional", placeholder="cuenta@institucion.edu")
        password = st.text_input("Contraseña", type="password")
    else:
        identifier = ""
        password = st.text_input("Código interno de demostración", type="password")
        demo_code = settings.local_evaluator_access_code if role == "evaluator" else settings.local_teacher_access_code
        st.warning(f"Modo local controlado. Código temporal para probar esta vista: `{demo_code}`. No publiques la app en este modo.")
    if st.button("Ingresar al espacio interno", type="primary", use_container_width=True):
        try:
            identity = InternalAuthService(settings).sign_in(role, identifier, password)
        except Exception as exc:
            st.error(str(exc))
        else:
            st.session_state.access_role = identity.role
            st.session_state.internal_authenticated = True
            st.session_state.internal_user_id = identity.user_id
            st.session_state.internal_email = identity.email
            st.session_state.internal_auth_mode = identity.mode
            st.session_state.current_screen = "V01" if identity.role == "evaluator" else "D01"
            st.rerun()


def render_review_queue() -> None:
    st.markdown("<div class='tm-eyebrow'>ACCESO INTERNO · EVALUACIÓN</div>", unsafe_allow_html=True)
    st.title("Selecciona una sesión asignada")
    if load_settings().uses_supabase:
        st.info("Cada evaluador sólo puede consultar las sesiones que le fueron asignadas.")
    else:
        st.warning("Modo local de demostración: se muestran las sesiones de prueba disponibles.")
    repository = get_session_repository()
    activity_sessions = repository.list_activity_sessions_for_evaluator(st.session_state.internal_user_id)
    if not activity_sessions:
        st.info("No hay sesiones grupales asignadas a esta cuenta.")
        return
    activity_sessions.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    sessions_by_code = {item["session_code"]: item for item in activity_sessions}
    selected_code = st.selectbox(
        "Sesión del grupo",
        list(sessions_by_code),
        format_func=lambda code: f"{code} · {sessions_by_code[code]['title']} · {sessions_by_code[code].get('status', 'sin estado')}",
    )
    selected_session = sessions_by_code[selected_code]
    all_records = repository.list_participants(selected_session["activity_session_id"])
    records = [record for record in all_records if record.get("reflection_submitted")]
    st.caption(f"{len(all_records)} participante(s) registrados · {len(records)} enviado(s) a evaluación")
    if not records:
        st.info("Esta sesión todavía no tiene participantes listos para evaluación.")
        return
    records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    by_code = {record["participant_id"]: record for record in records}
    selected = st.selectbox(
        "Participante",
        list(by_code),
        format_func=lambda code: (
            f"{code} · {by_code[code].get('academic_profile', {}).get('program_label', 'Transversal')} · "
            f"{by_code[code].get('session_status', 'sin estado')} · "
            f"{'Delta validado' if by_code[code].get('reasoning_evaluation', {}).get('status') == 'validated' else 'por evaluar'}"
        ),
    )
    if st.button("Abrir respuestas del participante", type="primary", use_container_width=True):
        if load_session_for_review(selected, selected_session["activity_session_id"]):
            st.rerun()
        st.error("Las respuestas ya no están disponibles para revisión.")
