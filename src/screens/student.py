"""Pantallas del recorrido y resultados del estudiante."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.layout import card, demo_notice, screen_title


def render_e01(data: dict[str, Any]) -> None:
    screen_title("E01", "Inicio, código y consentimiento", "Comprende el recorrido y crea una identidad pseudónima antes de iniciar.")
    col1, col2 = st.columns([1.45, 1])
    with col1:
        st.subheader("Antes de comenzar")
        st.write("Explorarás un caso, dialogarás con un Coach que sólo hace preguntas y conservarás el control de tu ThinkMark.")
        st.text_input("Código de participante", value=data["participant"]["participant_id"], disabled=True)
        st.checkbox("He leído el aviso y deseo participar en esta demostración", value=True, disabled=True)
    with col2:
        card("Duración estimada", "25–35 minutos")
        card("Privacidad", "El demo no solicita nombre, matrícula ni correo.")
        card("Resultado", "Una firma de razonamiento revisable por el estudiante.")
    demo_notice("el paso 6.2")


def render_e02(data: dict[str, Any]) -> None:
    screen_title("E02", "Caso y posición inicial", "Captura una línea base antes de cualquier intervención de IA.")
    st.subheader(data["title"])
    st.write(data["context"])
    st.markdown(f"<div class='tm-question'><strong>Pregunta central</strong><br>{data['central_question']}</div>", unsafe_allow_html=True)
    cols = st.columns(2)
    labels = [("Problema", "problem"), ("Evidencia", "evidence"), ("Análisis crítico de IA", "ai_critique"), ("Justificación", "decision")]
    for idx, (label, key) in enumerate(labels):
        with cols[idx % 2]:
            st.text_area(label, value=data["initial"][key], disabled=True, height=115)
    demo_notice("el paso 6.2")


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
