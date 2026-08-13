"""Pantallas del recorrido y resultados del estudiante."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.domain.baseline import DIMENSIONS, MIN_RESPONSE_CHARS, validate_baseline, validate_participant_code
from src.services.journey import close_baseline, create_or_resume_session, go_to_screen, save_baseline_draft
from src.ui.layout import card, demo_notice, screen_title


def render_e01(data: dict[str, Any]) -> None:
    screen_title("E01", "Inicio, código y consentimiento", "Comprende el recorrido y crea una identidad pseudónima antes de iniciar.")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))

    col1, col2 = st.columns([1.45, 1])
    with col1:
        st.subheader("Antes de comenzar")
        st.write("Explorarás un caso, dialogarás con un Coach que sólo hace preguntas y conservarás el control de tu ThinkMark.")
        if st.session_state.consent_status:
            st.success("Consentimiento registrado y sesión activa.")
            st.text_input("Código de participante", value=st.session_state.participant_id, disabled=True)
            accepted_at = st.session_state.consent_record.get("accepted_at", "")
            st.caption(f"Aceptación registrada: {accepted_at[:19].replace('T', ' ')} UTC")
            if st.button("Continuar a mi posición inicial", type="primary", use_container_width=True):
                go_to_screen("E02")
                st.rerun()
        else:
            st.caption("Usa únicamente el código entregado por el facilitador. No escribas nombre, matrícula ni correo.")
            with st.form("access_form", clear_on_submit=False):
                participant_code = st.text_input("Código de participante", placeholder="Ejemplo: TM-DEMO-024", max_chars=20)
                voluntary = st.checkbox("Mi participación en esta prueba es voluntaria.")
                non_graded = st.checkbox("Entiendo que esta actividad no asigna calificación.")
                anonymized = st.checkbox("Autorizo el uso anonimizado de mis respuestas para evaluar y mejorar el prototipo.")
                submitted = st.form_submit_button("Aceptar y comenzar", type="primary", use_container_width=True)
            if submitted:
                normalized, code_error = validate_participant_code(participant_code)
                if code_error:
                    st.error(code_error)
                elif not all((voluntary, non_graded, anonymized)):
                    st.error("Para continuar debes confirmar las tres condiciones. Si no deseas participar, puedes cerrar esta página sin crear una sesión.")
                else:
                    resumed = create_or_resume_session(normalized)
                    go_to_screen("E03" if resumed and st.session_state.baseline_locked else "E02")
                    st.rerun()
    with col2:
        card("Duración estimada", "25–35 minutos")
        card("Privacidad", "El demo no solicita nombre, matrícula ni correo.")
        card("Resultado", "Una firma de razonamiento revisable por el estudiante.")
    st.caption("Las condiciones aceptadas quedan asociadas a las versiones vigentes del instrumento y del caso.")


def render_e02(data: dict[str, Any]) -> None:
    screen_title("E02", "Caso y posición inicial", "Captura una línea base antes de cualquier intervención de IA.")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))
    st.subheader(data["title"])
    st.write(data["context"])
    with st.expander("Datos disponibles en el caso", expanded=False):
        for fact in data["facts"]:
            st.markdown(f"- {fact}")
    st.markdown(f"<div class='tm-question'><strong>Pregunta central</strong><br>{data['central_question']}</div>", unsafe_allow_html=True)
    st.warning("Responde primero con tu propio razonamiento. El AI Coach permanecerá bloqueado hasta que cierres esta posición inicial.")

    labels = [
        ("¿Cómo defines el problema central?", "problem", "Explica qué está en juego y para quién."),
        ("¿Qué evidencia tienes y cuál necesitarías?", "evidence", "Distingue datos disponibles de evidencia faltante."),
        ("¿Qué riesgos, límites o supuestos tendría una posible IA?", "ai_critique", "Considera errores, sesgos o aspectos que la IA podría omitir."),
        ("¿Qué decisión inicial tomarías y por qué?", "decision", "Incluye una postura o acción y al menos una razón."),
    ]
    current = st.session_state.baseline_snapshot.get("responses", {}) if st.session_state.baseline_locked else st.session_state.baseline_draft
    confidence = st.session_state.baseline_snapshot.get("confidence", st.session_state.baseline_confidence) if st.session_state.baseline_locked else st.session_state.baseline_confidence

    if st.session_state.baseline_locked:
        st.success("Tu posición inicial está cerrada. Esta instantánea ya no puede editarse y será el punto de comparación del Reasoning Delta.")
        cols = st.columns(2)
        for idx, (label, key, help_text) in enumerate(labels):
            cols[idx % 2].text_area(label, value=current[key], disabled=True, height=145, help=help_text)
        st.slider("Confianza inicial", 1, 5, value=confidence, disabled=True, help="1 = muy baja · 5 = muy alta")
        snapshot = st.session_state.baseline_snapshot
        st.caption(f"Cerrada: {snapshot['locked_at'][:19].replace('T', ' ')} UTC · Sello de integridad: {snapshot['integrity_hash'][:12]}…")
        if st.button("Continuar al AI Coach", type="primary"):
            go_to_screen("E03")
            st.rerun()
        return

    with st.form("baseline_form", clear_on_submit=False):
        cols = st.columns(2)
        responses: dict[str, str] = {}
        for idx, (label, key, help_text) in enumerate(labels):
            responses[key] = cols[idx % 2].text_area(
                label,
                value=current.get(key, ""),
                height=145,
                help=f"{help_text} Mínimo orientativo: {MIN_RESPONSE_CHARS} caracteres.",
                key=f"baseline_{key}",
            )
        confidence_value = st.slider(
            "¿Qué tanta confianza tienes ahora en tu decisión?",
            1,
            5,
            value=confidence,
            help="1 = muy baja · 5 = muy alta",
            key="baseline_confidence_widget",
        )
        freeze_confirmed = st.checkbox("Entiendo que esta versión quedará como mi punto de partida y ya no podré modificarla.")
        save_col, close_col = st.columns(2)
        save_clicked = save_col.form_submit_button("Guardar borrador", use_container_width=True)
        close_clicked = close_col.form_submit_button("Cerrar mi posición inicial", type="primary", use_container_width=True)

    if save_clicked:
        save_baseline_draft(responses, confidence_value)
        st.success("Borrador guardado. Puedes cerrar la página y recuperarlo con tu código.")
    if close_clicked:
        errors = validate_baseline(responses, confidence_value)
        if not freeze_confirmed:
            errors["confirmation"] = "Confirma que entiendes el cierre antes de continuar."
        if errors:
            st.error("Revisa la línea base antes de cerrarla:")
            friendly = {key: label for label, key, _ in labels}
            for key, message in errors.items():
                st.markdown(f"- **{friendly.get(key, 'Confirmación')}**: {message}")
        else:
            close_baseline(responses, confidence_value, data["case_id"])
            st.session_state.access_notice = "Línea base cerrada correctamente. El AI Coach ya está habilitado."
            go_to_screen("E03")
            st.rerun()


def render_e03(data: dict[str, Any]) -> None:
    screen_title("E03", "AI Coach", "Profundiza tu razonamiento mediante preguntas socráticas; el Coach no responde por ti.")
    st.markdown(f"<div class='tm-question'><strong>Coach · foco: {data['coach']['focus']}</strong><br>{data['coach']['question']}</div>", unsafe_allow_html=True)
    st.text_area("Tu razonamiento", value=data["coach"]["answer"], disabled=True, height=130)
    st.caption("El contrato técnico limitará cada turno a una pregunta breve, sin recomendaciones ni texto sustitutivo.")
    demo_notice("el paso 6.4")


def render_e04(data: dict[str, Any]) -> None:
    v = data["verification"]
    screen_title("E04", "Verify", "Contrasta una afirmación relevante con una fuente y explica cómo afecta tu postura.")
    st.text_input("Afirmación seleccionada", value=v["claim"], disabled=True)
    a, b = st.columns(2)
    a.text_input("Fuente", value=v["source_title"], disabled=True)
    b.selectbox("Valoración", [v["assessment"]], disabled=True)
    st.text_area("Impacto en mi postura", value=v["impact"], disabled=True)
    st.warning("La URL de esta vista es ficticia y sólo demuestra la estructura del formulario.")
    demo_notice("el paso 6.3")


def render_e05(data: dict[str, Any]) -> None:
    c = data["challenge"]
    screen_title("E05", "Challenge", "Examina límites y supuestos de la IA; formula una alternativa propia.")
    labels = [("Limitación u omisión", "limitation"), ("Supuesto cuestionable", "assumption"), ("Evidencia faltante", "missing_evidence"), ("Alternativa propia", "alternative")]
    cols = st.columns(2)
    for idx, (label, key) in enumerate(labels):
        cols[idx % 2].text_area(label, value=c[key], disabled=True, height=105)
    demo_notice("el paso 6.3")


def render_e06(data: dict[str, Any]) -> None:
    d = data["decision"]
    screen_title("E06", "Decide", "Registra una decisión humana con evidencia, criterios y concesiones.")
    st.selectbox("Decisión", [d["position"]], disabled=True)
    cols = st.columns(2)
    cols[0].text_area("Qué conservo", value=d["keep"], disabled=True)
    cols[1].text_area("Qué modifico o rechazo", value=d["change"], disabled=True)
    st.text_area("Trade-off reconocido", value=d["tradeoff"], disabled=True)
    demo_notice("el paso 6.3")


def render_e07(data: dict[str, Any]) -> None:
    screen_title("E07", "Reflect", "Captura la evidencia final comparable y reconoce qué cambió y qué sigue incierto.")
    labels = [("Problema reformulado", "problem"), ("Evidencia valorada", "evidence"), ("Análisis crítico de IA", "ai_critique"), ("Justificación final", "decision")]
    cols = st.columns(2)
    for idx, (label, key) in enumerate(labels):
        cols[idx % 2].text_area(label, value=data["final"][key], disabled=True, height=120)
    demo_notice("el paso 6.3")


def render_e08(data: dict[str, Any]) -> None:
    screen_title("E08", "Reasoning Delta", "Observa el cambio validado en cuatro dimensiones, sin convertirlo en ranking o calificación.")
    names = {"problem": "Problema", "evidence": "Evidencia", "ai_critique": "Crítica de IA", "decision": "Decisión"}
    cols = st.columns(4)
    for col, (key, (initial, final)) in zip(cols, data["delta"].items()):
        col.metric(names[key], f"Nivel {final}", delta=f"{final-initial:+d}")
    st.caption("Resultados simulados sujetos a validación humana mediante la Rúbrica Reasoning Delta v2.")
    demo_notice("el paso 6.5")


def render_e09(data: dict[str, Any]) -> None:
    screen_title("E09", "ThinkMark · Human Reasoning Signature", "Revisa y decide cómo queda representado tu razonamiento.")
    labels = {
        "reframed_problem": "Problema reformulado",
        "reviewed_evidence": "Evidencia revisada",
        "ai_analysis": "Análisis de IA",
        "human_decision": "Decisión humana",
        "change": "Cambio",
        "human_contribution": "Contribución propia",
        "limits": "Límites",
    }
    for key, label in labels.items():
        st.text_area(label, value=data["thinkmark"][key], disabled=True, height=85)
    st.radio("Decisión del estudiante", ["Aprobar", "Corregir antes de aprobar"], horizontal=True, disabled=True)
    demo_notice("el paso 6.6")


def render_e10(data: dict[str, Any]) -> None:
    screen_title("E10", "Feedback y cierre", "Valora la experiencia y confirma que el recorrido quedó íntegramente guardado.")
    cols = st.columns(3)
    cols[0].metric("Recorrido", "Completo")
    cols[1].metric("ThinkMark", "Aprobado")
    cols[2].metric("Integridad", "10/10 etapas")
    st.slider("¿Qué tan útil fue el Coach?", 1, 5, 4, disabled=True)
    st.text_area("¿Qué fue lo más útil?", value="Las preguntas me hicieron precisar qué evidencia necesitaba.", disabled=True)
    st.success("Demostración cerrada. No se ha enviado información a servicios externos.")
    demo_notice("el paso 6.7")
