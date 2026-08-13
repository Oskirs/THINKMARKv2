"""Pantallas del recorrido y resultados del estudiante."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ai.coach import load_coach_config
from src.domain.baseline import MIN_RESPONSE_CHARS, validate_baseline, validate_participant_code
from src.services.journey import (
    close_baseline,
    create_or_resume_session,
    go_to_screen,
    save_baseline_draft,
    save_challenge,
    save_decision,
    save_reflection,
    save_verification,
    start_coach,
    submit_coach_turn,
)
from src.ui.layout import card, demo_notice, screen_title


def _show_errors(errors: dict[str, str], labels: dict[str, str]) -> None:
    st.error("Revisa la información antes de continuar:")
    for key, message in errors.items():
        st.markdown(f"- **{labels.get(key, key.replace('_', ' ').title())}**: {message}")


def _show_access_notice() -> None:
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))


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
    _show_access_notice()
    config = load_coach_config()
    st.info(
        "El Coach formula una pregunta por turno. No entrega soluciones, no califica y no modifica "
        "tu posición inicial. Tú decides qué aceptar, cuestionar y verificar."
    )
    with st.expander("Tu posición inicial cerrada", expanded=False):
        for label, key in [("Problema", "problem"), ("Evidencia", "evidence"), ("Crítica de IA", "ai_critique"), ("Decisión", "decision")]:
            st.markdown(f"**{label}.** {st.session_state.initial_responses.get(key, '')}")

    turns = st.session_state.coach_turns
    completed = st.session_state.coach_completed or st.session_state.coach_simulation_completed
    if not turns and not completed:
        st.markdown(
            "<div class='tm-question'><strong>Listo para iniciar</strong><br>"
            "El Coach recibirá únicamente el caso, el fragmento pertinente de tu línea base y hasta dos turnos previos.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Iniciar conversación socrática", type="primary", use_container_width=True):
            with st.spinner("Preparando una pregunta…"):
                start_coach(data)
            st.rerun()
        st.caption(f"Máximo: {config['max_turns']} preguntas · Política: {config['policy_version']}")
        return

    for turn in turns:
        mode_label = "IA conectada" if turn.get("mode") == "openai" else "Banco pedagógico seguro"
        st.markdown(
            f"<div class='tm-question'><strong>Coach · {turn.get('focus', 'Razonamiento')}</strong><br>"
            f"{turn.get('question', '')}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Pregunta {turn.get('turn_number', 1)} de {config['max_turns']} · {mode_label}")
        if turn.get("response"):
            st.markdown(f"**Tu respuesta:** {turn['response']}")
        if turn.get("safety_triggered"):
            st.caption("Se activó una regla de seguridad pedagógica; la conversación continuó con una pregunta no resolutiva.")

    current = st.session_state.coach_bridge
    if completed:
        st.text_area("Afirmación que verificarás", value=st.session_state.claim_to_verify, disabled=True, height=90)
        st.success("Conversación cerrada por el estudiante. Verify está habilitado.")
        usage = st.session_state.ai_usage
        st.caption(
            f"Trazabilidad técnica: {len(turns)} turno(s) · {usage.get('requests', 0)} solicitud(es) · "
            f"{usage.get('fallbacks', 0)} fallback(s)."
        )
        if st.button("Continuar a Verify", type="primary"):
            go_to_screen("E04")
            st.rerun()
        return

    active_turn = turns[-1]
    at_limit = len(turns) >= int(config["max_turns"])
    with st.form(f"coach_turn_form_{active_turn.get('turn_number', len(turns))}"):
        response = st.text_area(
            "Tu razonamiento",
            value=current.get("response", "") if current.get("turn_number") == active_turn.get("turn_number") else "",
            height=140,
            placeholder="Responde con tu propio análisis; el sistema no completará el texto por ti.",
            help=f"Desarrolla al menos {config['minimum_response_chars']} caracteres.",
        )
        claim = st.text_area(
            "Afirmación que quieres verificar al terminar",
            value=current.get("claim_to_verify", data["verification"]["claim"]),
            height=90,
            help="Se requiere únicamente para cerrar el Coach y pasar a Verify.",
        )
        next_col, close_col = st.columns(2)
        next_clicked = next_col.form_submit_button(
            "Enviar y recibir otra pregunta",
            use_container_width=True,
            disabled=at_limit,
        )
        close_clicked = close_col.form_submit_button("Cerrar Coach y continuar", type="primary", use_container_width=True)
    if at_limit:
        st.caption("Alcanzaste el máximo de preguntas. Responde la actual y cierra el Coach para continuar.")
    if next_clicked or close_clicked:
        with st.spinner("Guardando tu respuesta y preparando el siguiente paso…"):
            errors = submit_coach_turn(
                response,
                claim,
                continue_conversation=next_clicked,
                case=data,
            )
        if errors:
            _show_errors(errors, {"response": "Tu razonamiento", "claim_to_verify": "Afirmación", "coach": "AI Coach"})
        else:
            if next_clicked:
                st.session_state.access_notice = "Respuesta guardada. El Coach preparó una nueva pregunta."
                go_to_screen("E03")
            else:
                st.session_state.access_notice = "Conversación cerrada. Ahora contrasta tu afirmación con una fuente."
                go_to_screen("E04")
            st.rerun()


def render_e04(data: dict[str, Any]) -> None:
    screen_title("E04", "Verify", "Contrasta una afirmación relevante con una fuente y explica cómo afecta tu postura.")
    _show_access_notice()
    st.caption("La aplicación valida la estructura de la URL; no certifica que una fuente sea confiable.")
    current = st.session_state.verification_draft or {"claim": st.session_state.claim_to_verify}
    read_only = st.session_state.reflection_submitted
    with st.form("verification_form"):
        claim = st.text_area("Afirmación seleccionada", value=current.get("claim", ""), height=85, disabled=read_only)
        col1, col2 = st.columns(2)
        title = col1.text_input("Título de la fuente", value=current.get("source_title", ""), disabled=read_only)
        source_type_options = ["Académica", "Institucional", "Periodística", "Datos", "Otra"]
        source_type_value = current.get("source_type", "Académica")
        source_type = col2.selectbox("Tipo de fuente", source_type_options, index=source_type_options.index(source_type_value) if source_type_value in source_type_options else 0, disabled=read_only)
        url = st.text_input("URL de la fuente", value=current.get("source_url", ""), placeholder="https://…", disabled=read_only)
        assessment_options = ["confirma", "contradice", "matiza", "no es comprobable"]
        assessment_value = current.get("assessment", "matiza")
        assessment = st.selectbox("¿Qué hace la fuente respecto de la afirmación?", assessment_options, index=assessment_options.index(assessment_value), disabled=read_only)
        reliability = st.text_area("¿Por qué esta fuente es pertinente o confiable?", value=current.get("reliability_reason", ""), height=110, disabled=read_only)
        impact = st.text_area("¿Qué cambia o se fortalece en tu decisión?", value=current.get("impact", ""), height=110, disabled=read_only)
        limitation = st.text_area("Limitación de acceso o de la fuente (opcional)", value=current.get("access_limitation", ""), height=75, disabled=read_only)
        if not read_only:
            save_col, complete_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Guardar borrador", use_container_width=True)
            complete_clicked = complete_col.form_submit_button("Completar Verify", type="primary", use_container_width=True)
        else:
            save_clicked = complete_clicked = False
    payload = {
        "claim": claim,
        "source_title": title,
        "source_type": source_type,
        "source_url": url,
        "assessment": assessment,
        "reliability_reason": reliability,
        "impact": impact,
        "access_limitation": limitation,
    }
    if save_clicked:
        save_verification(payload, complete=False)
        st.success("Borrador de Verify guardado.")
    if complete_clicked:
        errors = save_verification(payload, complete=True)
        if errors:
            _show_errors(errors, {"claim": "Afirmación", "source_title": "Título", "source_type": "Tipo", "source_url": "URL", "assessment": "Valoración", "reliability_reason": "Pertinencia/confiabilidad", "impact": "Impacto"})
        else:
            st.session_state.access_notice = "Verificación completa. Ahora examina límites y supuestos."
            go_to_screen("E05")
            st.rerun()


def render_e05(data: dict[str, Any]) -> None:
    screen_title("E05", "Challenge", "Examina límites y supuestos de la IA; formula una alternativa propia.")
    _show_access_notice()
    verified = st.session_state.verifications[0]
    st.markdown(f"<div class='tm-question'><strong>Afirmación examinada</strong><br>{verified['claim']}<br><br><strong>Resultado de Verify</strong><br>{verified['assessment']}: {verified['impact']}</div>", unsafe_allow_html=True)
    current = st.session_state.challenge_draft
    read_only = st.session_state.reflection_submitted
    with st.form("challenge_form"):
        cols = st.columns(2)
        limitation = cols[0].text_area("Limitación u omisión específica", value=current.get("limitation", ""), height=115, disabled=read_only, help="¿Qué condición podría fallar?")
        assumption = cols[1].text_area("Supuesto cuestionable", value=current.get("assumption", ""), height=115, disabled=read_only, help="¿Qué se está dando por cierto sin demostrarlo?")
        missing = cols[0].text_area("Evidencia adicional necesaria", value=current.get("missing_evidence", ""), height=115, disabled=read_only)
        alternative = cols[1].text_area("Alternativa propia", value=current.get("alternative", ""), height=115, disabled=read_only)
        counterargument = st.text_area("Contraargumento propio (puede sustituir a la alternativa)", value=current.get("counterargument", ""), height=100, disabled=read_only)
        if not read_only:
            save_col, complete_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Guardar borrador", use_container_width=True)
            complete_clicked = complete_col.form_submit_button("Completar Challenge", type="primary", use_container_width=True)
        else:
            save_clicked = complete_clicked = False
    payload = {"reference_claim": verified["claim"], "limitation": limitation, "assumption": assumption, "missing_evidence": missing, "alternative": alternative, "counterargument": counterargument}
    if save_clicked:
        save_challenge(payload, complete=False)
        st.success("Borrador de Challenge guardado.")
    if complete_clicked:
        errors = save_challenge(payload, complete=True)
        if errors:
            _show_errors(errors, {"limitation": "Limitación", "assumption": "Supuesto", "missing_evidence": "Evidencia necesaria", "own_elaboration": "Elaboración propia", "repetition": "Autoría"})
        else:
            st.session_state.access_notice = "Challenge completo. Ahora registra tu decisión humana."
            go_to_screen("E06")
            st.rerun()


def render_e06(data: dict[str, Any]) -> None:
    screen_title("E06", "Decide", "Registra una decisión humana con evidencia, criterios y concesiones.")
    _show_access_notice()
    with st.expander("Referencias de tu recorrido", expanded=False):
        st.markdown(f"**Posición inicial.** {st.session_state.initial_responses['decision']}")
        st.markdown(f"**Verify.** {st.session_state.verifications[0]['assessment']}: {st.session_state.verifications[0]['impact']}")
        st.markdown(f"**Challenge.** {st.session_state.challenges[0]['limitation']}")
    current = st.session_state.decision_draft
    read_only = st.session_state.reflection_submitted
    types = ["mantener", "aceptar parcialmente", "modificar", "rechazar", "combinar"]
    with st.form("decision_form"):
        decision_type_value = current.get("decision_type", "modificar")
        decision_type = st.selectbox("¿Qué harás con tu postura inicial?", types, index=types.index(decision_type_value), disabled=read_only)
        cols = st.columns(2)
        keep = cols[0].text_area("Elementos que conservas", value=current.get("keep", ""), height=115, disabled=read_only)
        change = cols[1].text_area("Elementos que modificas o rechazas", value=current.get("change", ""), height=115, disabled=read_only)
        key_evidence = st.text_area("Evidencia clave", value=current.get("key_evidence", ""), height=100, disabled=read_only)
        evidence_weight = st.text_area("¿Por qué esa evidencia pesa en tu decisión?", value=current.get("evidence_weight", ""), height=100, disabled=read_only)
        tradeoff = st.text_area("Aportación, criterio o trade-off que tú incorporaste", value=current.get("tradeoff", ""), height=100, disabled=read_only)
        if not read_only:
            save_col, complete_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Guardar borrador", use_container_width=True)
            complete_clicked = complete_col.form_submit_button("Completar Decide", type="primary", use_container_width=True)
        else:
            save_clicked = complete_clicked = False
    payload = {"decision_type": decision_type, "keep": keep, "change": change, "key_evidence": key_evidence, "evidence_weight": evidence_weight, "tradeoff": tradeoff}
    if save_clicked:
        save_decision(payload, complete=False)
        st.success("Borrador de Decide guardado.")
    if complete_clicked:
        errors = save_decision(payload, complete=True)
        if errors:
            _show_errors(errors, {"decision_type": "Tipo de decisión", "keep": "Elementos conservados", "change": "Cambios", "key_evidence": "Evidencia clave", "evidence_weight": "Peso de la evidencia", "tradeoff": "Aportación o trade-off"})
        else:
            st.session_state.access_notice = "Decisión guardada. Completa ahora tu reflexión final."
            go_to_screen("E07")
            st.rerun()


def render_e07(data: dict[str, Any]) -> None:
    screen_title("E07", "Reflect", "Captura la evidencia final comparable y reconoce qué cambió y qué sigue incierto.")
    _show_access_notice()
    with st.expander("Comparar con mi posición inicial (solo lectura)", expanded=True):
        cols = st.columns(2)
        for idx, (label, key) in enumerate([("Problema inicial", "problem"), ("Evidencia inicial", "evidence"), ("Crítica inicial", "ai_critique"), ("Decisión inicial", "decision")]):
            cols[idx % 2].text_area(label, value=st.session_state.initial_responses[key], disabled=True, height=105, key=f"initial_compare_{key}")
    current = st.session_state.final_responses.get("responses", {}) if st.session_state.reflection_submitted else st.session_state.final_draft
    confidence = st.session_state.final_responses.get("confidence", st.session_state.final_confidence) if st.session_state.reflection_submitted else st.session_state.final_confidence
    read_only = st.session_state.reflection_submitted
    with st.form("reflection_form"):
        final_response = st.text_area("Respuesta final integrada", value=current.get("final_response", ""), height=140, disabled=read_only)
        cols = st.columns(2)
        problem = cols[0].text_area("Problema reformulado", value=current.get("problem", ""), height=120, disabled=read_only)
        evidence = cols[1].text_area("Evidencia valorada", value=current.get("evidence", ""), height=120, disabled=read_only)
        critique = cols[0].text_area("Análisis crítico de IA", value=current.get("ai_critique", ""), height=120, disabled=read_only)
        decision = cols[1].text_area("Justificación de la decisión final", value=current.get("decision", ""), height=120, disabled=read_only)
        change = st.text_area("¿Qué cambió o se fortaleció?", value=current.get("change", ""), height=95, disabled=read_only)
        learning = st.text_area("¿Qué aprendiste?", value=current.get("learning", ""), height=95, disabled=read_only)
        contribution = st.text_area("¿Cuál fue tu contribución propia?", value=current.get("human_contribution", ""), height=95, disabled=read_only)
        uncertainty = st.text_area("¿Qué incertidumbre permanece?", value=current.get("uncertainty", ""), height=85, disabled=read_only)
        next_step = st.text_area("¿Cuál sería tu siguiente paso?", value=current.get("next_step", ""), height=85, disabled=read_only)
        final_confidence = st.slider("Confianza final", 1, 5, value=confidence, disabled=read_only, help="Usa la misma escala que al inicio.")
        confirm_submit = st.checkbox("Entiendo que al enviar esta reflexión quedará bloqueada para evaluación.", disabled=read_only, value=read_only)
        if not read_only:
            save_col, submit_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Guardar borrador", use_container_width=True)
            submit_clicked = submit_col.form_submit_button("Enviar a evaluación", type="primary", use_container_width=True)
        else:
            save_clicked = submit_clicked = False
    payload = {"final_response": final_response, "problem": problem, "evidence": evidence, "ai_critique": critique, "decision": decision, "change": change, "learning": learning, "human_contribution": contribution, "uncertainty": uncertainty, "next_step": next_step}
    if save_clicked:
        save_reflection(payload, final_confidence, submit=False)
        st.success("Borrador de Reflect guardado.")
    if submit_clicked:
        if not confirm_submit:
            _show_errors({"confirmation": "Confirma el envío antes de continuar."}, {"confirmation": "Confirmación"})
        else:
            errors = save_reflection(payload, final_confidence, submit=True)
            if errors:
                _show_errors(errors, {"final_response": "Respuesta final", "problem": "Problema", "evidence": "Evidencia", "ai_critique": "Análisis crítico", "decision": "Decisión", "change": "Cambio", "learning": "Aprendizaje", "human_contribution": "Contribución propia", "uncertainty": "Incertidumbre", "next_step": "Siguiente paso", "confidence": "Confianza"})
            else:
                st.session_state.access_notice = "Reflexión enviada. La sesión quedó en espera de evaluación humana."
                go_to_screen("V01")
                st.rerun()
    if read_only:
        st.success("Reflexión enviada · estado: awaiting_review. Sólo un facilitador podrá solicitar una reapertura en una fase posterior.")
        if st.button("Ir a validación de la rúbrica", type="primary"):
            go_to_screen("V01")
            st.rerun()


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
