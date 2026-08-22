"""Dashboard docente con oportunidad accionable y validación humana."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.domain.learning_opportunity import build_dashboard_summary, seal_teacher_decision, validate_teacher_decision
from src.repositories.factory import get_learning_opportunity_repository, get_session_repository
from src.ui.layout import screen_title


ACTIVITY_ID = "CASO-DEMO-01-v1"
STATUS_LABELS = {"open": "Abierta", "closed": "Cerrada", "archived": "Archivada"}


def _show_errors(errors: dict[str, str]) -> None:
    labels = {
        "teacher_code": "Código docente",
        "teacher_validation_status": "Decisión docente",
        "learning_strength": "Fortaleza",
        "learning_opportunity": "Oportunidad",
        "opportunity_evidence": "Evidencia",
        "suggested_intervention": "Intervención",
        "teacher_note": "Nota docente",
        "teacher_confirmed": "Confirmación",
    }
    st.error("Revisa la validación docente:")
    for field, message in errors.items():
        st.markdown(f"- **{labels.get(field, field)}**: {message}")


def _render_session_management() -> None:
    repository = get_session_repository()
    st.subheader("Sesiones del grupo")
    st.write("Crea un código para reunir las respuestas del grupo y facilitar su revisión.")
    evaluators = repository.list_evaluators()
    evaluator_by_label = {item["display_code"]: item["user_id"] for item in evaluators}
    with st.form("create_activity_session_form"):
        title = st.text_input("Nombre interno de la sesión", placeholder="Ejemplo: 5.º semestre · Grupo A")
        evaluator_label = st.selectbox("Evaluador asignado", ["Sin asignar"] + list(evaluator_by_label))
        create_clicked = st.form_submit_button("Crear sesión y generar código", type="primary", use_container_width=True)
    if create_clicked:
        if not 3 <= len(title.strip()) <= 120:
            st.error("Escribe un nombre de sesión de 3 a 120 caracteres.")
        else:
            created = repository.create_activity_session(
                title, st.session_state.internal_user_id, evaluator_by_label.get(evaluator_label, "")
            )
            st.session_state.access_notice = f"Sesión creada. Comparte el código {created['session_code']} con el grupo."
            st.rerun()

    sessions = repository.list_activity_sessions_for_creator(st.session_state.internal_user_id)
    if not sessions:
        st.info("Todavía no has creado sesiones.")
        return
    sessions.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    by_code = {item["session_code"]: item for item in sessions}
    selected_code = st.selectbox(
        "Administrar sesión",
        list(by_code),
        format_func=lambda code: f"{code} · {by_code[code]['title']} · {STATUS_LABELS.get(by_code[code]['status'], by_code[code]['status'])}",
    )
    selected = by_code[selected_code]
    participants = repository.list_participants(selected["activity_session_id"])
    cols = st.columns(3)
    cols[0].metric("Código", selected_code)
    cols[1].metric("Participantes", len(participants))
    cols[2].metric("Estado", STATUS_LABELS.get(selected["status"], selected["status"]))
    if selected["status"] == "open":
        if st.button("Cerrar ingreso de nuevos participantes", use_container_width=True):
            repository.set_activity_session_status(selected_code, "closed")
            st.rerun()
    elif selected["status"] == "closed":
        action_cols = st.columns(2)
        if action_cols[0].button("Reabrir sesión", use_container_width=True):
            repository.set_activity_session_status(selected_code, "open")
            st.rerun()
        if action_cols[1].button("Archivar sesión", use_container_width=True):
            repository.set_activity_session_status(selected_code, "archived")
            st.rerun()
    else:
        st.caption("La sesión archivada se conserva sólo para consulta.")


def _render_fatigue_indicators(records: list[dict[str, Any]]) -> None:
    rows = []
    for screen_id in ("E02", "E03", "E04", "E05", "E06", "E07"):
        stages = [record.get("stage_metrics", {}).get(screen_id, {}) for record in records]
        started = [stage for stage in stages if stage.get("started_at")]
        completed = [stage for stage in started if stage.get("completed_at")]
        elapsed = [int(stage.get("elapsed_seconds", 0)) for stage in completed]
        lengths = [sum(stage.get("response_characters", {}).values()) for stage in completed]
        rows.append({
            "Pantalla": screen_id,
            "Iniciaron": len(started),
            "Completaron": len(completed),
            "Sin completar": len(started) - len(completed),
            "Minutos promedio": round(sum(elapsed) / len(elapsed) / 60, 1) if elapsed else None,
            "Caracteres promedio": round(sum(lengths) / len(lengths)) if lengths else None,
        })
    st.subheader("Carga y posible fatiga del recorrido")
    st.caption("Indicadores descriptivos por pantalla. Sirven para detectar abandono o respuestas cada vez más cortas; no califican estudiantes.")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_d01(data: dict[str, Any]) -> None:
    if st.session_state.access_role != "teacher" or not st.session_state.internal_authenticated:
        st.error("Se requiere acceso autenticado de profesor.")
        return
    screen_title("D01", "Dashboard docente de aprendizaje", "Convierte evidencia agregada en una oportunidad específica para intervenir.")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))
    st.success("Vista separada para el rol docente. El código estudiantil no permite abrir este dashboard.")
    st.info(
        "Los resultados describen evidencia expresada y evaluada durante la actividad. "
        "No son calificaciones, diagnósticos ni rankings de estudiantes."
    )

    _render_session_management()
    st.divider()

    session_repository = get_session_repository()
    records = session_repository.list_all()
    if not st.session_state.dashboard_access_logged:
        session_repository.audit_access(st.session_state.internal_user_id, "teacher", "open_dashboard", "activity", ACTIVITY_ID)
        st.session_state.dashboard_access_logged = True
    summary = build_dashboard_summary(records)
    cols = st.columns(4)
    cols[0].metric("Sesiones iniciadas", summary["started"])
    cols[1].metric("Sesiones completas", summary["completed"], delta=f"{summary['completion_rate']:.0%}")
    cols[2].metric("Deltas validados", summary["evaluated"])
    cols[3].metric("Mediana de recorrido", f"{summary['median_minutes']} min" if summary["median_minutes"] is not None else "Sin dato")

    _render_fatigue_indicators(records)

    if not summary["proposal"]:
        st.warning("Aún no existen evaluaciones humanas validadas suficientes para proponer una oportunidad de aprendizaje.")
        return

    st.subheader("Reasoning Delta agregado")
    chart_data = [
        {"Dimensión": item["label"], "Delta medio": item["average_delta"]}
        for item in summary["dimensions"].values()
    ]
    st.bar_chart(chart_data, x="Dimensión", y="Delta medio", color="#76232F", height=300)

    completed_feedback = [record["feedback"] for record in records if record.get("completed") and record.get("feedback")]
    if completed_feedback:
        rating_fields = {
            "coach_helpfulness_rating": "Coach",
            "verification_helpfulness_rating": "Verify",
            "decision_agency_rating": "Agencia",
            "thinkmark_fidelity_rating": "Fidelidad ThinkMark",
            "reuse_intention_rating": "Reutilización",
        }
        st.subheader("Feedback agregado del estudiante")
        feedback_cols = st.columns(5)
        for col, (field, label) in zip(feedback_cols, rating_fields.items()):
            values = [item[field] for item in completed_feedback]
            col.metric(label, f"{sum(values) / len(values):.1f}/5")
        st.caption(f"Promedios descriptivos de {len(completed_feedback)} sesión(es) completas; no se muestran comentarios individuales.")

    proposal = summary["proposal"]
    st.subheader("Propuesta del sistema · pendiente de juicio docente")
    st.markdown(
        "<div class='tm-opportunity'>"
        f"<strong>Fortaleza observada</strong><br>{proposal['learning_strength']}<br><br>"
        f"<strong>Oportunidad de aprendizaje</strong><br>{proposal['learning_opportunity']}<br><br>"
        f"<strong>Evidencia agregada</strong><br>{proposal['opportunity_evidence']}<br><br>"
        f"<strong>Intervención sugerida</strong><br>{proposal['suggested_intervention']}"
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Regla auditable: {proposal['rule_version']} · La dimensión se prioriza por necesidad formativa agregada; "
        "la regla no etiqueta rasgos personales."
    )

    repository = get_learning_opportunity_repository()
    existing = repository.get(ACTIVITY_ID)
    if existing:
        status_labels = {"accepted": "Aceptada", "adjusted": "Ajustada", "rejected": "Rechazada"}
        st.success(f"Decisión docente registrada: {status_labels[existing['teacher_validation_status']]}")
        final = existing["final"]
        for label, field in (
            ("Fortaleza validada", "learning_strength"),
            ("Oportunidad validada", "learning_opportunity"),
            ("Evidencia validada", "opportunity_evidence"),
            ("Intervención validada", "suggested_intervention"),
        ):
            st.text_area(label, value=final[field], disabled=True, height=90, key=f"validated_{field}")
        st.caption(
            f"Validación: {existing['validated_at'][:19].replace('T', ' ')} UTC · "
            f"Sello de integridad: {existing['integrity_hash'][:12]}…"
        )
        return

    st.subheader("Validación del profesor")
    with st.form("teacher_validation_form"):
        teacher_code = st.text_input("Código pseudónimo del profesor", placeholder="DOC-DEMO-01")
        strength = st.text_area("Fortaleza observada", value=proposal["learning_strength"], height=90)
        opportunity = st.text_area("Oportunidad de aprendizaje", value=proposal["learning_opportunity"], height=90)
        evidence = st.text_area("Evidencia que la sustenta", value=proposal["opportunity_evidence"], height=90)
        intervention = st.text_area("Intervención que se aplicará", value=proposal["suggested_intervention"], height=100)
        status_label = st.radio(
            "Decisión sobre la propuesta",
            ["Aceptar sin cambios", "Validar con ajustes", "Rechazar"],
            horizontal=True,
        )
        note = st.text_area("Nota docente (obligatoria si se rechaza)", height=80, max_chars=1000)
        confirmed = st.checkbox("Confirmo que una persona revisó la evidencia agregada y tomó esta decisión pedagógica.")
        submitted = st.form_submit_button("Registrar decisión docente", type="primary", use_container_width=True)

    if submitted:
        statuses = {"Aceptar sin cambios": "accepted", "Validar con ajustes": "adjusted", "Rechazar": "rejected"}
        payload = {
            "teacher_code": teacher_code,
            "teacher_validation_status": statuses[status_label],
            "learning_strength": strength,
            "learning_opportunity": opportunity,
            "opportunity_evidence": evidence,
            "suggested_intervention": intervention,
            "teacher_note": note,
            "teacher_confirmed": confirmed,
            "teacher_user_id": st.session_state.internal_user_id,
        }
        errors = validate_teacher_decision(proposal, payload)
        if errors:
            _show_errors(errors)
        else:
            repository.save_once(ACTIVITY_ID, seal_teacher_decision(proposal, payload))
            st.success("Decisión docente registrada. La propuesta y la versión validada quedaron separadas.")
            st.rerun()
