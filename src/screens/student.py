"""Pantallas del recorrido y resultados del estudiante."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.ai.coach import load_coach_config
from src.domain.activity_session import validate_session_code
from src.domain.baseline import MIN_RESPONSE_CHARS, validate_baseline, validate_participant_code
from src.domain.thinkmark import THINKMARK_FIELDS, THINKMARK_LABELS
from src.services.academic_cases import (
    area_options,
    build_academic_profile,
    build_case_for_profile,
    program_options,
    semester_options,
    validate_academic_selection,
)
from src.services.journey import (
    close_baseline,
    create_or_resume_session,
    decide_thinkmark,
    finalize_session,
    generate_thinkmark,
    go_to_screen,
    refresh_current_session,
    save_baseline_draft,
    save_challenge,
    save_decision,
    save_reflection,
    save_student_feedback,
    save_thinkmark_corrections,
    save_verification,
    resume_screen_id,
    start_coach,
    submit_coach_turn,
    track_screen_visit,
    unload_review_session,
)
from src.ui.layout import card, screen_title
from src.ui.language import render_term_guide


def _show_errors(errors: dict[str, str], labels: dict[str, str]) -> None:
    st.error("Revisa la información antes de continuar:")
    for key, message in errors.items():
        st.markdown(f"- **{labels.get(key, key.replace('_', ' ').title())}**: {message}")


def _show_access_notice() -> None:
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))


def _counted_text_area(
    label: str,
    *,
    value: str,
    minimum: int,
    key: str,
    height: int = 110,
    disabled: bool = False,
    help: str | None = None,
    placeholder: str | None = None,
) -> str:
    text = st.text_area(
        label,
        value=value,
        height=height,
        disabled=disabled,
        help=help,
        placeholder=placeholder,
        key=key,
    )
    if not disabled:
        count = len(text.strip())
        if count < minimum:
            st.caption(f"Necesitas al menos {minimum} caracteres. Actualmente: {count}/{minimum}.")
        else:
            st.caption(f"Extensión suficiente: {count}/{minimum} caracteres.")
    return text


def render_e01(data: dict[str, Any]) -> None:
    screen_title(
        "E01",
        "Perfil académico y acuerdos de participación",
        "Selecciona tu carrera y semestre para recibir un caso cercano a tu formación.",
    )
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))

    col1, col2 = st.columns([1.45, 1])
    with col1:
        st.subheader("Antes de comenzar")
        st.write("Analizarás un caso, conversarás con un Coach que sólo hace preguntas y revisarás tu ThinkMark antes de decidir si te representa.")
        if st.session_state.consent_status:
            st.success("Consentimiento registrado y sesión activa.")
            profile = st.session_state.academic_profile
            st.markdown(
                f"**Escuela o área:** {profile.get('area', 'Transversal')}  \n"
                f"**Carrera:** {profile.get('program_label', 'Caso transversal')}  \n"
                f"**Semestre:** {profile.get('semester_label', 'No registrado')}  \n"
                f"**Nivel del caso:** {profile.get('complexity_label', 'General')}"
            )
            st.caption("El perfil y el caso quedaron fijados para que tu recorrido sea comparable de principio a fin.")
            st.text_input("Código de sesión", value=st.session_state.session_code, disabled=True)
            st.text_input("Código de participante", value=st.session_state.participant_id, disabled=True)
            accepted_at = st.session_state.consent_record.get("accepted_at", "")
            st.caption(f"Aceptación registrada: {accepted_at[:19].replace('T', ' ')} UTC")
            if st.button("Continuar a mi primera respuesta", type="primary", use_container_width=True):
                go_to_screen("E02")
                st.rerun()
        else:
            st.caption(
                "Elige el perfil que corresponde a esta actividad. La lista es un catálogo piloto editable; "
                "si tu carrera no aparece, selecciona el caso transversal."
            )
            areas = area_options()
            area_label = st.selectbox(
                "Escuela o área académica",
                list(areas),
                index=None,
                placeholder="Selecciona tu escuela o área",
                help="La carrera se mostrará después de seleccionar esta opción.",
                key="academic_area_widget",
            )
            area_id = areas.get(area_label or "")
            programs = program_options(area_id) if area_id else {}
            program_label = st.selectbox(
                "Carrera o programa académico",
                list(programs),
                index=None,
                placeholder="Selecciona tu carrera" if area_id else "Primero selecciona tu escuela o área",
                help="Esta selección adapta el contexto del caso; no cambia la rúbrica.",
                disabled=not area_id,
                key=f"academic_program_widget_{area_id or 'none'}",
            )
            semesters = semester_options()
            semester_label = st.selectbox(
                "Semestre",
                list(semesters),
                index=None,
                placeholder="Selecciona tu semestre",
                help="El piloto incluye casos para 1.º, 5.º y 7.º semestre.",
                key="academic_semester_widget",
            )
            with st.form("access_form", clear_on_submit=False):
                st.caption("Escribe los dos códigos entregados por el facilitador. No uses nombre, matrícula, grupo ni correo.")
                session_code = st.text_input(
                    "Código de sesión",
                    placeholder="Ejemplo: TM-AB12CD",
                    max_chars=9,
                    help="Es el mismo código para todo el grupo.",
                )
                participant_code = st.text_input(
                    "Código anónimo de participante",
                    placeholder="Ejemplo: ALU-024",
                    max_chars=20,
                    help="Este código identifica únicamente tu avance dentro de la actividad.",
                )
                voluntary = st.checkbox("Mi participación en esta prueba es voluntaria.")
                non_graded = st.checkbox("Entiendo que esta actividad no asigna calificación.")
                anonymized = st.checkbox("Autorizo el uso anonimizado de mis respuestas para evaluar y mejorar el prototipo.")
                submitted = st.form_submit_button("Aceptar y comenzar", type="primary", use_container_width=True)
            if submitted:
                normalized_session, session_error = validate_session_code(session_code)
                normalized, code_error = validate_participant_code(participant_code)
                program_id = programs.get(program_label or "")
                semester = semesters.get(semester_label or "")
                profile_errors = validate_academic_selection(program_id, semester)
                if session_error or code_error or profile_errors or not all((voluntary, non_graded, anonymized)):
                    st.error("Revisa la información antes de comenzar:")
                    if session_error:
                        st.markdown(f"- **Código de sesión:** {session_error}")
                    if code_error:
                        st.markdown(f"- **Código de participante:** {code_error}")
                    for message in profile_errors.values():
                        st.markdown(f"- **Perfil académico:** {message}")
                    if not all((voluntary, non_graded, anonymized)):
                        st.markdown("- **Acuerdos:** confirma las tres condiciones para participar.")
                else:
                    profile = build_academic_profile(program_id, semester)
                    assigned_case = build_case_for_profile(program_id, semester)
                    try:
                        resumed = create_or_resume_session(normalized_session, normalized, profile, assigned_case)
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        go_to_screen(resume_screen_id() if resumed else "E02")
                        st.rerun()
    with col2:
        card("Duración estimada", "25–35 minutos")
        card("Privacidad", "La demostración no solicita nombre, matrícula ni correo.")
        card("Resultado", "Un resumen editable de tu razonamiento, llamado ThinkMark.")
    st.caption(
        "La selección académica adapta el contexto, pero todas las carreras trabajan las mismas cuatro "
        "dimensiones del Reasoning Delta."
    )


def render_e02(data: dict[str, Any]) -> None:
    track_screen_visit("E02")
    screen_title("E02", "Caso y primera respuesta", "Explica qué piensas antes de conversar con el AI Coach. Esta será tu referencia inicial.")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))
    profile = data.get("academic_profile") or st.session_state.academic_profile
    if profile:
        st.markdown(
            f"<span class='tm-badge'>{profile.get('program_label', 'Caso transversal')} · "
            f"{profile.get('semester_label', '')}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("<div class='tm-case-label'>CASO</div>", unsafe_allow_html=True)
    st.subheader(data["title"])
    st.write(data["context"])
    if data.get("analysis_focus"):
        st.info(f"**Enfoque para este semestre:** {data['analysis_focus']}")
    with st.expander("Datos disponibles en el caso", expanded=False):
        for fact in data["facts"]:
            st.markdown(f"- {fact}")
    st.markdown(f"<div class='tm-question'><strong>Pregunta central</strong><br>{data['central_question']}</div>", unsafe_allow_html=True)
    st.warning("Responde con tus propias palabras. Para continuar, cada respuesta debe tener al menos 40 caracteres. Si falta texto, tu borrador se conserva.")
    render_term_guide("evidence", "assumption")

    labels = [
        ("¿Cuál es el problema principal?", "problem", "Explica qué está pasando, a quién afecta y qué debe decidirse."),
        ("¿Qué información apoya tu respuesta y qué información te falta?", "evidence", "Separa los datos disponibles de lo que todavía necesitas revisar."),
        ("¿Qué podría equivocarse, pasar por alto o dar por cierto una IA?", "ai_critique", "Piensa en errores, sesgos o información que podría faltar."),
        ("¿Qué harías por ahora y por qué?", "decision", "Escribe una decisión inicial y al menos una razón."),
    ]
    current = st.session_state.baseline_snapshot.get("responses", {}) if st.session_state.baseline_locked else st.session_state.baseline_draft
    confidence = st.session_state.baseline_snapshot.get("confidence", st.session_state.baseline_confidence) if st.session_state.baseline_locked else st.session_state.baseline_confidence

    if st.session_state.baseline_locked:
        st.success("Tu primera respuesta quedó guardada y ya no puede editarse. Después se comparará con tu respuesta final.")
        cols = st.columns(2)
        for idx, (label, key, help_text) in enumerate(labels):
            cols[idx % 2].text_area(label, value=current[key], disabled=True, height=145, help=help_text)
        st.slider("Confianza inicial", 1, 5, value=confidence, disabled=True, help="1 = muy baja · 5 = muy alta")
        snapshot = st.session_state.baseline_snapshot
        st.caption(f"Cerrada: {snapshot['locked_at'][:19].replace('T', ' ')} UTC · Sello de integridad: {snapshot['integrity_hash'][:12]}…")
        if st.button("Continuar al AI Coach", type="primary", use_container_width=True):
            go_to_screen("E03")
            st.rerun()
        return

    cols = st.columns(2)
    responses: dict[str, str] = {}
    for idx, (label, key, help_text) in enumerate(labels):
        with cols[idx % 2]:
            responses[key] = _counted_text_area(
                label,
                value=current.get(key, ""),
                minimum=MIN_RESPONSE_CHARS,
                height=145,
                help=help_text,
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
    freeze_confirmed = st.checkbox("Entiendo que esta respuesta será mi punto de partida y ya no podré modificarla.")
    baseline_ready = all(len(value.strip()) >= MIN_RESPONSE_CHARS for value in responses.values()) and freeze_confirmed
    save_col, close_col = st.columns(2)
    save_clicked = save_col.button("Guardar borrador", use_container_width=True)
    close_clicked = close_col.button("Guardar mi primera respuesta", type="primary", use_container_width=True, disabled=not baseline_ready)

    if save_clicked:
        save_baseline_draft(responses, confidence_value)
        st.success("Borrador guardado. Puedes cerrar la página y volver con tu código.")
    if close_clicked:
        errors = validate_baseline(responses, confidence_value)
        if not freeze_confirmed:
            errors["confirmation"] = "Confirma que entiendes el cierre antes de continuar."
        if errors:
            st.error("Revisa tu primera respuesta antes de guardarla:")
            friendly = {key: label for label, key, _ in labels}
            for key, message in errors.items():
                st.markdown(f"- **{friendly.get(key, 'Confirmación')}**: {message}")
        else:
            close_baseline(responses, confidence_value, data["case_id"])
            st.session_state.access_notice = "Tu primera respuesta quedó guardada. El AI Coach ya está disponible."
            go_to_screen("E03")
            st.rerun()


def render_e03(data: dict[str, Any]) -> None:
    track_screen_visit("E03")
    screen_title("E03", "AI Coach", "Responde preguntas breves para revisar mejor tus razones. El Coach no responde por ti.")
    _show_access_notice()
    config = load_coach_config()
    st.info(
        "El Coach hace una pregunta por turno. No entrega soluciones, no califica y no modifica "
        "tu primera respuesta. Tú decides qué aceptar, cuestionar y revisar."
    )
    with st.expander("Tu primera respuesta guardada", expanded=False):
        for label, key in [("Problema al comenzar", "problem"), ("Información inicial", "evidence"), ("Lo que cuestionaste de la IA", "ai_critique"), ("Decisión al comenzar", "decision")]:
            st.markdown(f"**{label}.** {st.session_state.initial_responses.get(key, '')}")

    turns = st.session_state.coach_turns
    completed = st.session_state.coach_completed or st.session_state.coach_simulation_completed
    if not turns and not completed:
        st.markdown(
            "<div class='tm-question'><strong>Listo para iniciar</strong><br>"
            "El Coach recibirá únicamente el caso, la parte necesaria de tu primera respuesta y hasta dos respuestas anteriores.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Iniciar conversación", type="primary", use_container_width=True):
            with st.spinner("Preparando una pregunta…"):
                start_coach(data)
            st.rerun()
        st.caption(f"Máximo: {config['max_turns']} preguntas · Política: {config['policy_version']}")
        return

    for turn in turns:
        mode_label = "IA conectada" if turn.get("mode") == "openai" else "Pregunta de respaldo segura"
        st.markdown(
            f"<div class='tm-question'><strong>Coach · {turn.get('focus', 'Razonamiento')}</strong><br>"
            f"{turn.get('question', '')}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Pregunta {turn.get('turn_number', 1)} de {config['max_turns']} · {mode_label}")
        if turn.get("response"):
            st.markdown(f"**Tu respuesta:** {turn['response']}")
        if turn.get("safety_triggered"):
            st.caption("La pregunta original no cumplió las reglas del Coach; se mostró una pregunta segura que no entrega la respuesta.")

    current = st.session_state.coach_bridge
    if completed:
        st.text_area("Afirmación que verificarás", value=st.session_state.claim_to_verify, disabled=True, height=90)
        st.success("Conversación cerrada por el estudiante. Verify está habilitado.")
        usage = st.session_state.ai_usage
        st.caption(
            f"Trazabilidad técnica: {len(turns)} turno(s) · {usage.get('requests', 0)} solicitud(es) · "
            f"{usage.get('fallbacks', 0)} pregunta(s) de respaldo."
        )
        if st.button("Continuar a Verify", type="primary"):
            go_to_screen("E04")
            st.rerun()
        return

    active_turn = turns[-1]
    at_limit = len(turns) >= int(config["max_turns"])
    response = _counted_text_area(
        "Tu razonamiento",
        value=current.get("response", "") if current.get("turn_number") == active_turn.get("turn_number") else "",
        minimum=int(config["minimum_response_chars"]),
        height=140,
        placeholder="Escribe con tus propias palabras; el sistema no completará el texto por ti.",
        key=f"coach_response_{active_turn.get('turn_number', len(turns))}",
    )
    claim = _counted_text_area(
        "Afirmación que quieres verificar al terminar",
        value=current.get("claim_to_verify", data["verification"]["claim"]),
        minimum=20,
        height=90,
        help="Sólo se requiere para cerrar el Coach y pasar a Verify.",
        key=f"coach_claim_{active_turn.get('turn_number', len(turns))}",
    )
    next_col, close_col = st.columns(2)
    response_ready = len(response.strip()) >= int(config["minimum_response_chars"])
    claim_ready = len(claim.strip()) >= 20
    next_clicked = next_col.button("Enviar y recibir otra pregunta", use_container_width=True, disabled=at_limit or not response_ready)
    close_clicked = close_col.button("Cerrar Coach y continuar", type="primary", use_container_width=True, disabled=not (response_ready and claim_ready))
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
    track_screen_visit("E04")
    screen_title("E04", "Verify · Contrasta una afirmación", "Consulta una fuente y decide qué efecto tiene sobre tu razonamiento inicial.")
    _show_access_notice()
    st.info(
        "En esta etapa compararás una afirmación de tu decisión inicial con una fuente. No buscamos una respuesta correcta: "
        "queremos saber si la información confirma, modifica o cuestiona lo que pensabas."
    )
    st.caption("La aplicación valida el formato de la liga; tú explicas por qué la fuente es útil y qué cambia después de revisarla.")
    render_term_guide("evidence")
    current = st.session_state.verification_draft or {"claim": st.session_state.claim_to_verify}
    read_only = st.session_state.reflection_submitted
    claim = st.text_area("Afirmación que vas a revisar", value=current.get("claim", ""), height=85, disabled=read_only, key="verify_claim")
    col1, col2 = st.columns(2)
    title = col1.text_input("Título de la fuente", value=current.get("source_title", ""), disabled=read_only, key="verify_title")
    source_type_options = ["Académica", "Institucional", "Periodística", "Datos", "Otra"]
    source_type_value = current.get("source_type", "Académica")
    source_type = col2.selectbox("Tipo de fuente", source_type_options, index=source_type_options.index(source_type_value) if source_type_value in source_type_options else 0, disabled=read_only, key="verify_source_type")
    url = st.text_input("Liga completa de la fuente", value=current.get("source_url", ""), placeholder="https://…", disabled=read_only, key="verify_url")
    assessment_options = ["confirma", "contradice", "matiza", "no permite comprobar"]
    stored_assessment = current.get("assessment", "matiza")
    if stored_assessment == "no es comprobable":
        stored_assessment = "no permite comprobar"
    assessment_label = st.selectbox("Después de leerla, la fuente…", assessment_options, index=assessment_options.index(stored_assessment), disabled=read_only, key="verify_assessment")
    assessment = "no es comprobable" if assessment_label == "no permite comprobar" else assessment_label
    reliability = _counted_text_area(
        "¿Qué dato de la fuente utilizaste y por qué es confiable o útil?",
        value=current.get("reliability_reason", ""), minimum=40, height=110, disabled=read_only,
        help="Menciona quién publica la fuente, qué información presenta o qué límite reconoce.", key="verify_reliability",
    )
    impact = _counted_text_area(
        "¿Qué parte de tu decisión se confirma, cambia o queda en duda? Explica por qué.",
        value=current.get("impact", ""), minimum=40, height=110, disabled=read_only, key="verify_impact",
    )
    limitation = current.get("access_limitation", "")
    if not read_only:
        save_col, complete_col = st.columns(2)
        save_clicked = save_col.button("Guardar borrador", use_container_width=True, key="verify_save")
        verify_ready = all((len(claim.strip()) >= 20, len(title.strip()) >= 5, bool(url.strip()), len(reliability.strip()) >= 40, len(impact.strip()) >= 40))
        complete_clicked = complete_col.button("Validar y continuar", type="primary", use_container_width=True, key="verify_complete", disabled=not verify_ready)
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
            st.session_state.access_notice = "Fuente revisada. Ahora identifica lo que la IA podría omitir o dar por cierto."
            go_to_screen("E05")
            st.rerun()


def render_e05(data: dict[str, Any]) -> None:
    track_screen_visit("E05")
    screen_title("E05", "Challenge · Revisa límites y opciones", "Señala qué falta, qué se está suponiendo y qué otra opción sería posible.")
    _show_access_notice()
    st.info(
        "Ahora pondrás a prueba tu decisión. Elige el principal límite que detectaste, explica qué falta comprobar "
        "y propone una opción que responda mejor a ese límite. No necesitas encontrar una respuesta perfecta."
    )
    render_term_guide("assumption", "counterargument")
    verified = st.session_state.verifications[0]
    st.markdown(f"<div class='tm-question'><strong>Afirmación examinada</strong><br>{verified['claim']}<br><br><strong>Resultado de Verify</strong><br>{verified['assessment']}: {verified['impact']}</div>", unsafe_allow_html=True)
    current = st.session_state.challenge_draft
    read_only = st.session_state.reflection_submitted
    focus_options = ["Falta información", "Se asumió algo sin comprobar", "Falta una perspectiva", "No se consideró una consecuencia"]
    stored_focus = current.get("assumption", focus_options[0])
    focus = st.selectbox(
        "1. ¿Qué tipo de límite es el más importante?",
        focus_options,
        index=focus_options.index(stored_focus) if stored_focus in focus_options else 0,
        disabled=read_only,
        key="challenge_focus",
    )
    limitation = _counted_text_area(
        "2. ¿Dónde aparece ese límite en el caso y por qué importa?",
        value=current.get("limitation", ""), minimum=40, height=115, disabled=read_only,
        help="Señala una condición, persona, dato o consecuencia concreta.", key="challenge_limitation",
    )
    missing = _counted_text_area(
        "3. ¿Qué información permitiría comprobar o reducir ese límite?",
        value=current.get("missing_evidence", ""), minimum=30, height=105, disabled=read_only, key="challenge_missing",
    )
    alternative = _counted_text_area(
        "4. ¿Qué otra forma de actuar propones y cómo responde al límite?",
        value=current.get("alternative", ""), minimum=40, height=115, disabled=read_only, key="challenge_alternative",
    )
    if not read_only:
        save_col, complete_col = st.columns(2)
        save_clicked = save_col.button("Guardar borrador", use_container_width=True, key="challenge_save")
        challenge_ready = len(limitation.strip()) >= 40 and len(missing.strip()) >= 30 and len(alternative.strip()) >= 40
        complete_clicked = complete_col.button("Validar y continuar", type="primary", use_container_width=True, key="challenge_complete", disabled=not challenge_ready)
    else:
        save_clicked = complete_clicked = False
    payload = {"reference_claim": verified["claim"], "limitation": limitation, "assumption": focus, "missing_evidence": missing, "alternative": alternative, "counterargument": ""}
    if save_clicked:
        save_challenge(payload, complete=False)
        st.success("Borrador de Challenge guardado.")
    if complete_clicked:
        errors = save_challenge(payload, complete=True)
        if errors:
            _show_errors(errors, {"limitation": "Explicación del límite", "missing_evidence": "Información necesaria", "alternative": "Otra forma de actuar", "own_elaboration": "Otra forma de actuar", "repetition": "Respuestas"})
        else:
            st.session_state.access_notice = "Revisión completa. Ahora toma tu decisión y explica tus razones."
            go_to_screen("E06")
            st.rerun()


def render_e06(data: dict[str, Any]) -> None:
    track_screen_visit("E06")
    screen_title("E06", "Decide · Toma una postura", "Indica qué harías, qué evidencia sostiene tu decisión y qué costo o límite aceptas.")
    _show_access_notice()
    render_term_guide("tradeoff")
    with st.expander("Referencias de tu recorrido", expanded=False):
        st.markdown(f"**Decisión al comenzar.** {st.session_state.initial_responses['decision']}")
        st.markdown(f"**Verify.** {st.session_state.verifications[0]['assessment']}: {st.session_state.verifications[0]['impact']}")
        st.markdown(f"**Challenge.** {st.session_state.challenges[0]['limitation']}")
    current = st.session_state.decision_draft
    read_only = st.session_state.reflection_submitted
    types = ["mantener", "aceptar parcialmente", "modificar", "rechazar", "combinar"]
    decision_type_value = current.get("decision_type", "modificar")
    decision_type = st.selectbox("Respecto de tu postura inicial, decides…", types, index=types.index(decision_type_value), disabled=read_only, key="decision_type_widget")
    previous_decision = " ".join(part for part in (current.get("keep", ""), current.get("change", "")) if part).strip()
    change = _counted_text_area(
        "1. ¿Qué harías ahora y qué conservas o modificas de tu postura inicial?",
        value=previous_decision, minimum=50, height=120, disabled=read_only, key="decision_summary",
    )
    previous_evidence = " ".join(part for part in (current.get("key_evidence", ""), current.get("evidence_weight", "")) if part).strip()
    key_evidence = _counted_text_area(
        "2. ¿Qué evidencia fue decisiva y por qué tiene más peso que las demás?",
        value=previous_evidence, minimum=50, height=115, disabled=read_only, key="decision_evidence",
    )
    tradeoff = _counted_text_area(
        "3. ¿Qué beneficio obtienes y qué costo, riesgo o límite aceptas?",
        value=current.get("tradeoff", ""), minimum=40, height=105, disabled=read_only,
        help="Explica el balance de tu decisión, no sólo una ventaja.", key="decision_tradeoff",
    )
    if not read_only:
        save_col, complete_col = st.columns(2)
        save_clicked = save_col.button("Guardar borrador", use_container_width=True, key="decision_save")
        decision_ready = len(change.strip()) >= 50 and len(key_evidence.strip()) >= 50 and len(tradeoff.strip()) >= 40
        complete_clicked = complete_col.button("Validar y continuar", type="primary", use_container_width=True, key="decision_complete", disabled=not decision_ready)
    else:
        save_clicked = complete_clicked = False
    payload = {"decision_type": decision_type, "keep": "", "change": change, "key_evidence": key_evidence, "evidence_weight": "", "tradeoff": tradeoff}
    if save_clicked:
        save_decision(payload, complete=False)
        st.success("Borrador de Decide guardado.")
    if complete_clicked:
        errors = save_decision(payload, complete=True)
        if errors:
            _show_errors(errors, {"decision_type": "Tipo de decisión", "change": "Decisión explicada", "key_evidence": "Evidencia decisiva", "tradeoff": "Beneficio y costo"})
        else:
            st.session_state.access_notice = "Decisión guardada. Completa ahora tu reflexión final."
            go_to_screen("E07")
            st.rerun()


def render_e07(data: dict[str, Any]) -> None:
    track_screen_visit("E07")
    screen_title("E07", "Reflect · Reflexión final", "Resume tu decisión final, qué cambió y qué todavía necesitas revisar.")
    _show_access_notice()
    render_term_guide("uncertainty")
    with st.expander("Comparar con mi primera respuesta (sólo lectura)", expanded=True):
        cols = st.columns(2)
        for idx, (label, key) in enumerate([("Problema inicial", "problem"), ("Evidencia inicial", "evidence"), ("Crítica inicial", "ai_critique"), ("Decisión inicial", "decision")]):
            cols[idx % 2].text_area(label, value=st.session_state.initial_responses[key], disabled=True, height=105, key=f"initial_compare_{key}")
    current = st.session_state.final_responses.get("responses", {}) if st.session_state.reflection_submitted else st.session_state.final_draft
    confidence = st.session_state.final_responses.get("confidence", st.session_state.final_confidence) if st.session_state.reflection_submitted else st.session_state.final_confidence
    read_only = st.session_state.reflection_submitted
    cols = st.columns(2)
    with cols[0]:
        problem = _counted_text_area(
            "1. ¿Cuál es el problema que realmente debe resolverse y a quién afecta?",
            value=current.get("problem", ""), minimum=40, height=120, disabled=read_only, key="reflect_problem",
        )
        critique = _counted_text_area(
            "3. ¿Qué límite, supuesto o posible error identificaste en la propuesta de IA?",
            value=current.get("ai_critique", ""), minimum=40, height=120, disabled=read_only, key="reflect_critique",
        )
        change = _counted_text_area(
            "5. ¿Qué cambió o se fortaleció en tu razonamiento y qué aportaste tú?",
            value=current.get("change", ""), minimum=35, height=110, disabled=read_only, key="reflect_change",
        )
    with cols[1]:
        evidence = _counted_text_area(
            "2. ¿Qué evidencia utilizaste y qué conclusión concreta permite sostener?",
            value=current.get("evidence", ""), minimum=40, height=120, disabled=read_only, key="reflect_evidence",
        )
        decision = _counted_text_area(
            "4. ¿Cuál es tu decisión final y cuáles son sus dos razones principales?",
            value=current.get("decision", ""), minimum=40, height=120, disabled=read_only, key="reflect_decision",
        )
        uncertainty = _counted_text_area(
            "6. ¿Qué falta saber y cuál sería el siguiente paso para comprobarlo?",
            value=current.get("uncertainty", ""), minimum=35, height=110, disabled=read_only, key="reflect_uncertainty",
        )
    final_confidence = st.slider("Confianza final", 1, 5, value=confidence, disabled=read_only, help="Usa la misma escala que al inicio.", key="reflect_confidence")
    confirm_submit = st.checkbox("Entiendo que al enviar esta reflexión quedará bloqueada para evaluación.", disabled=read_only, value=read_only, key="reflect_confirm")
    if not read_only:
        save_col, submit_col = st.columns(2)
        save_clicked = save_col.button("Guardar borrador", use_container_width=True, key="reflect_save")
        reflection_ready = all((len(problem.strip()) >= 40, len(evidence.strip()) >= 40, len(critique.strip()) >= 40, len(decision.strip()) >= 40, len(change.strip()) >= 35, len(uncertainty.strip()) >= 35, confirm_submit))
        submit_clicked = submit_col.button("Enviar a evaluación", type="primary", use_container_width=True, key="reflect_submit", disabled=not reflection_ready)
    else:
        save_clicked = submit_clicked = False
    payload = {"problem": problem, "evidence": evidence, "ai_critique": critique, "decision": decision, "change": change, "uncertainty": uncertainty}
    if save_clicked:
        save_reflection(payload, final_confidence, submit=False)
        st.success("Borrador de Reflect guardado.")
    if submit_clicked:
        if not confirm_submit:
            _show_errors({"confirmation": "Confirma el envío antes de continuar."}, {"confirmation": "Confirmación"})
        else:
            errors = save_reflection(payload, final_confidence, submit=True)
            if errors:
                _show_errors(errors, {"final_response": "Respuesta final", "problem": "Problema", "evidence": "Información revisada", "ai_critique": "Análisis crítico", "decision": "Decisión", "change": "Cambio y aprendizaje", "uncertainty": "Lo que falta y siguiente paso", "confidence": "Confianza"})
            else:
                st.session_state.access_notice = "Reflexión enviada. La sesión quedó en espera de evaluación humana."
                go_to_screen("V01")
                st.rerun()
    if read_only:
        if st.session_state.reasoning_evaluation.get("status") == "validated":
            st.success("La evaluación humana ya fue validada. Puedes continuar a tus resultados.")
            if st.button("Ver Reasoning Delta", type="primary"):
                go_to_screen("E08")
                st.rerun()
        else:
            st.success("Reflexión enviada. Una persona evaluadora revisará tus respuestas con la rúbrica.")
        if st.button("Actualizar estado compartido"):
            refresh_current_session()
            if st.session_state.reasoning_evaluation.get("status") == "validated":
                go_to_screen("E08")
            st.rerun()


def render_e08(data: dict[str, Any]) -> None:
    screen_title("E08", "Reasoning Delta", "Compara tu primera respuesta y tu respuesta final en cuatro aspectos. No es una calificación.")
    _show_access_notice()
    render_term_guide("reasoning_delta", title="¿Qué significa Reasoning Delta?")
    evaluation = st.session_state.reasoning_evaluation
    if evaluation.get("status") != "validated":
        st.warning("Reasoning Delta permanece bloqueado hasta que una persona valide las cuatro dimensiones en V01.")
        return
    calculation = evaluation["calculation"]
    st.success(f"Resultado validado con {evaluation['rubric_version']}. La aplicación sólo calculó las diferencias aritméticas.")

    summary_cols = st.columns(3)
    summary_cols[0].metric("Promedio inicial", f"{calculation['average_initial']:.2f}")
    summary_cols[1].metric("Promedio final", f"{calculation['average_final']:.2f}")
    summary_cols[2].metric("Delta promedio", f"{calculation['delta_average']:+.2f}")

    st.subheader("Resultados por dimensión")
    dimension_cols = st.columns(4)
    for col, item in zip(dimension_cols, calculation["dimensions"].values()):
        col.metric(item["label"], f"Nivel {item['final_score']}", delta=f"{item['delta']:+d}")

    rows = []
    for item in calculation["dimensions"].values():
        if item["delta"] > 0:
            interpretation = "La respuesta final explicó este aspecto con mayor claridad."
        elif item["delta"] < 0:
            interpretation = "La respuesta final recibió un nivel menor; conviene revisar la explicación de la persona evaluadora."
        else:
            interpretation = "El nivel se mantuvo. Aun así, pudo existir aprendizaje que la escala no muestra."
        rows.append({
            "Dimensión": item["label"],
            "Inicial": item["initial_score"],
            "Final": item["final_score"],
            "Delta": item["delta"],
            "Lectura descriptiva": interpretation,
        })
    st.dataframe(rows, width="stretch", hide_index=True)

    with st.expander("Evidencia documentada por la persona evaluadora", expanded=False):
        for item in calculation["dimensions"].values():
            st.markdown(f"**{item['label']}.** {item['evidence_note']}")

    st.info(
        "Cómo leerlo: una diferencia positiva no prueba que THINKMARK causó el cambio; una diferencia de cero no significa "
        "que no aprendiste; y una diferencia negativa no es una calificación ni un diagnóstico."
    )
    st.caption(
        "Cambio dominante observado: " + ", ".join(calculation["dominant_change"]) +
        " · Candidata(s) a oportunidad de aprendizaje: " + ", ".join(calculation["learning_opportunity_candidates"]) +
        ". La oportunidad docente se validará en el paso 6.7."
    )
    if st.button("Revisar mi ThinkMark", type="primary", use_container_width=True):
        go_to_screen("E09")
        st.rerun()


def render_e09(data: dict[str, Any]) -> None:
    screen_title(
        "E09",
        "ThinkMark · Resumen de tu razonamiento",
        "Revisa el resumen de lo que expresaste. Puedes corregirlo, aprobarlo o decidir que no te representa.",
    )
    _show_access_notice()
    render_term_guide("thinkmark", title="¿Qué es una ThinkMark?")
    st.info(
        "Tu ThinkMark es un resumen editable, no una calificación ni un diagnóstico. "
        "Sólo se vuelve final si confirmas que te representa."
    )

    if st.session_state.thinkmark_decided:
        status = st.session_state.thinkmark_approval_status
        if status == "not_approved":
            st.warning("Decidiste no aprobar esta ThinkMark. No existe una versión final atribuida a ti.")
            content = st.session_state.thinkmark_corrections
        else:
            label = "Aprobada sin cambios" if status == "approved_as_generated" else "Aprobada con correcciones"
            st.success(f"{label}. La versión final quedó sellada y ya no puede modificarse.")
            content = st.session_state.thinkmark_final["content"]
        for field in THINKMARK_FIELDS:
            st.text_area(THINKMARK_LABELS[field], value=content.get(field, ""), disabled=True, height=105, key=f"final_{field}")
        if st.session_state.thinkmark_final:
            final = st.session_state.thinkmark_final
            st.caption(
                f"Aprobada: {final['approved_at'][:19].replace('T', ' ')} UTC · "
                f"Sello de integridad: {final['integrity_hash'][:12]}…"
            )
        if st.button("Continuar a feedback y cierre", type="primary", use_container_width=True):
            go_to_screen("E10")
            st.rerun()
        return

    if not st.session_state.thinkmark_draft:
        st.subheader("Generar la primera propuesta")
        st.write(
            "El resumen utilizará únicamente tus respuestas de las etapas anteriores y el Reasoning Delta validado. "
            "Podrás editar cada sección antes de decidir."
        )
        if st.button("Generar mi borrador de ThinkMark", type="primary", use_container_width=True):
            with st.spinner("Organizando la evidencia que registraste…"):
                errors = generate_thinkmark()
            if errors:
                _show_errors(errors, {"thinkmark": "ThinkMark", "regeneration": "Nueva propuesta"})
            else:
                st.session_state.access_notice = "Propuesta generada. Revísala sección por sección antes de decidir."
                st.rerun()
        return

    current_version = len(st.session_state.thinkmark_versions)
    current = st.session_state.thinkmark_corrections or st.session_state.thinkmark_draft
    version = st.session_state.thinkmark_versions[-1]
    mode_label = "integración configurada" if version["mode"] == "openai" else "síntesis local segura"
    st.caption(
        f"Propuesta {current_version} de 3 · {mode_label} · Política {version['policy_version']} · "
        "El borrador de origen se conserva aunque hagas cambios."
    )

    with st.form(f"thinkmark_review_v{current_version}"):
        edited: dict[str, str] = {}
        for field in THINKMARK_FIELDS:
            edited[field] = st.text_area(
                THINKMARK_LABELS[field],
                value=current.get(field, ""),
                height=105,
                key=f"thinkmark_{field}_v{current_version}",
            )
        confirmed = st.checkbox(
            "Confirmo que revisé las nueve secciones y que mi decisión se refiere al razonamiento que expresé en esta actividad."
        )
        save_col, approve_col, correct_col, reject_col = st.columns([1, 1, 1.25, 1])
        save_clicked = save_col.form_submit_button("Guardar cambios", use_container_width=True)
        approve_clicked = approve_col.form_submit_button("Aprobar", type="primary", use_container_width=True)
        correct_clicked = correct_col.form_submit_button("Corregir y aprobar", use_container_width=True)
        reject_clicked = reject_col.form_submit_button("No aprobar", use_container_width=True)

    if save_clicked:
        save_thinkmark_corrections(edited)
        st.success("Cambios guardados. Aún no has aprobado ni rechazado la propuesta.")
    if approve_clicked or correct_clicked or reject_clicked:
        status = (
            "approved_as_generated" if approve_clicked else
            "approved_with_corrections" if correct_clicked else
            "not_approved"
        )
        errors = decide_thinkmark(edited, status=status, confirmed=confirmed)
        if errors:
            _show_errors(errors, THINKMARK_LABELS | {"confirmation": "Confirmación", "decision": "Decisión", "thinkmark": "ThinkMark"})
        else:
            st.session_state.access_notice = "Tu decisión sobre la ThinkMark quedó registrada explícitamente."
            st.rerun()

    config_max = 3
    with st.expander("La propuesta no me representa: solicitar otra versión", expanded=False):
        if current_version >= config_max:
            st.warning("Ya se generaron las tres propuestas permitidas en este MVP. Puedes editar la actual o decidir no aprobarla.")
        else:
            with st.form(f"thinkmark_regenerate_v{current_version}"):
                reason = st.text_area(
                    "¿Qué debería representar mejor la nueva propuesta?",
                    height=85,
                    help="Tu explicación queda en el historial y no cambia tus respuestas originales.",
                )
                regenerate = st.form_submit_button("Rechazar esta propuesta y regenerar", use_container_width=True)
            if regenerate:
                with st.spinner("Creando una nueva propuesta sin alterar tu evidencia original…"):
                    errors = generate_thinkmark(rejection_reason=reason)
                if errors:
                    _show_errors(errors, {"regeneration": "Regeneración", "thinkmark": "ThinkMark"})
                else:
                    st.session_state.access_notice = "La propuesta anterior se conservó y se generó una nueva versión."
                    st.rerun()

    with st.expander(f"Historial de versiones ({current_version} propuesta{'s' if current_version != 1 else ''})", expanded=False):
        for item in reversed(st.session_state.thinkmark_versions):
            st.markdown(
                f"**Versión {item['version_number']}** · {item['generated_at'][:19].replace('T', ' ')} UTC · "
                f"{item['mode']} · `{item['content_hash'][:12]}…`"
            )


def render_e10(data: dict[str, Any]) -> None:
    screen_title("E10", "Comentarios y cierre", "Cuéntanos cómo fue la experiencia y confirma que todo el recorrido quedó guardado.")
    _show_access_notice()
    if not st.session_state.thinkmark_decided:
        st.warning("Primero debes registrar una decisión explícita sobre tu ThinkMark.")
        return

    role = st.session_state.access_role
    if st.session_state.completed:
        st.success("Sesión completada. El feedback, los controles y la decisión sobre ThinkMark quedaron sellados.")
        cols = st.columns(3)
        cols[0].metric("Recorrido", "Completo")
        cols[1].metric("ThinkMark", "Aprobado" if st.session_state.thinkmark_final else "No aprobado")
        cols[2].metric("Controles técnicos", f"{sum(st.session_state.completion_integrity['checks'].values())}/5")
        feedback = st.session_state.feedback
        rating_labels = {
            "coach_helpfulness_rating": "Utilidad del AI Coach",
            "verification_helpfulness_rating": "Utilidad de Verify",
            "decision_agency_rating": "La decisión fue mía",
            "thinkmark_fidelity_rating": "Fidelidad del ThinkMark",
            "reuse_intention_rating": "Intención de reutilizar",
        }
        st.dataframe(
            [{"Aspecto": label, "Valoración": feedback[key]} for key, label in rating_labels.items()],
            hide_index=True,
            width="stretch",
        )
        st.caption(
            f"Cierre: {st.session_state.completed_at[:19].replace('T', ' ')} UTC · "
            f"Sello de integridad: {st.session_state.completion_integrity['integrity_hash'][:12]}…"
        )
        st.info("El feedback se utiliza únicamente de forma agregada y no modifica Delta ni ThinkMark.")
        if role == "evaluator" and st.button("Volver a la cola de sesiones", type="primary", use_container_width=True):
            unload_review_session()
            st.rerun()
        return

    rating_labels = {
        "coach_helpfulness_rating": "El AI Coach me ayudó a pensar sin darme la respuesta.",
        "verification_helpfulness_rating": "Verify me ayudó a valorar mejor la evidencia.",
        "decision_agency_rating": "La decisión final fue propia.",
        "thinkmark_fidelity_rating": "La ThinkMark representa adecuadamente lo que expresé.",
        "reuse_intention_rating": "Usaría nuevamente una actividad como THINKMARK.",
    }
    if role == "student":
        if st.session_state.feedback_submitted:
            st.success("Feedback enviado. La sesión está esperando los controles finales de un facilitador autorizado.")
            st.info("Puedes cerrar esta página. Tu Reasoning Delta y tu ThinkMark ya están guardados y no serán modificados por el cierre.")
            if st.button("Actualizar estado del cierre"):
                refresh_current_session()
                st.rerun()
            return
        st.info("Este bloque pertenece al estudiante. El feedback se enviará una sola vez y no modifica Reasoning Delta ni ThinkMark.")
        current_feedback = st.session_state.feedback_draft
        with st.form("student_feedback_form"):
            st.subheader("Feedback del estudiante")
            st.caption("1 = totalmente en desacuerdo · 5 = totalmente de acuerdo")
            ratings: dict[str, int | None] = {}
            for field, label in rating_labels.items():
                options: list[int | None] = [None, 1, 2, 3, 4, 5]
                value = current_feedback.get(field)
                ratings[field] = st.selectbox(
                    label, options, index=options.index(value) if value in options else 0,
                    format_func=lambda item: "Selecciona…" if item is None else str(item), key=f"feedback_{field}",
                )
            most_useful = st.text_area("¿Qué fue lo más útil? (opcional)", value=current_feedback.get("most_useful", ""), max_chars=1000, height=90)
            confusing = st.text_area(
                "¿Qué fue confuso o repetitivo? (opcional)", value=current_feedback.get("confusing_or_repetitive", ""), max_chars=1000, height=90
            )
            submitted = st.form_submit_button("Enviar feedback", type="primary", use_container_width=True)
        if submitted:
            payload = ratings | {"most_useful": most_useful, "confusing_or_repetitive": confusing}
            errors = save_student_feedback(payload)
            if errors:
                _show_errors(errors, rating_labels | {"feedback": "Feedback"})
            else:
                st.session_state.access_notice = "Feedback enviado. El cierre queda ahora en manos del facilitador."
                st.rerun()
        return

    if role != "evaluator":
        st.error("Esta pantalla sólo está disponible para estudiante o evaluador/facilitador.")
        return
    if not st.session_state.feedback_submitted:
        st.warning("El estudiante todavía no ha enviado el feedback. No es posible cerrar la sesión.")
        return

    current_observations = st.session_state.facilitator_observations
    st.info("Bloque autenticado del facilitador. Estos controles no son visibles ni editables desde el acceso del estudiante.")
    with st.form("facilitator_closure_form"):
        st.subheader("Controles del facilitador")
        facilitator_code = st.text_input("Código pseudónimo del facilitador", value=current_observations.get("facilitator_code", ""), placeholder="FAC-DEMO-01")
        check_labels = {
            "check_completed_without_support": "El recorrido se completó sin asistencia técnica relevante.",
            "check_evidence_appraised": "Se registró evidencia y se valoró su confiabilidad o relevancia.",
            "check_coach_non_resolutive": "El AI Coach cuestionó sin resolver ni redactar la decisión.",
            "check_four_dimensions_comparable": "Existen cuatro dimensiones comparables antes y después.",
            "check_thinkmark_approved": "La ThinkMark fue revisada y recibió una decisión explícita del estudiante.",
        }
        checks = {field: st.checkbox(label, value=bool(current_observations.get(field, False)), key=f"facilitator_{field}") for field, label in check_labels.items()}
        incidents = st.text_area(
            "Incidencias técnicas observadas (opcional)", value=current_observations.get("technical_incidents", ""),
            max_chars=1000, height=80, help="Describe sólo incidencias operativas; no incluyas juicios sobre el estudiante.",
        )
        closure_confirmed = st.checkbox("Confirmo que revisé los cinco controles y autorizo el cierre de esta sesión.")
        close_clicked = st.form_submit_button("Validar controles y cerrar sesión", type="primary", use_container_width=True)
    if close_clicked:
        observations = {"facilitator_code": facilitator_code, **checks, "technical_incidents": incidents, "closure_confirmed": closure_confirmed}
        errors = finalize_session(observations)
        if errors:
            _show_errors(errors, check_labels | {
                "facilitator_code": "Código del facilitador", "technical_incidents": "Incidencias",
                "closure_confirmed": "Confirmación de cierre", "completion": "Cierre",
            })
        else:
            st.session_state.access_notice = "Controles validados y sesión cerrada de forma inmutable."
            st.rerun()
