"""Pantalla funcional de aplicación y validación humana de la rúbrica."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.domain.evaluation import MIN_NOTE_CHARS, load_rubric
from src.services.journey import save_evaluation, unload_review_session
from src.ui.layout import screen_title


def _show_errors(errors: dict[str, str]) -> None:
    st.error("Revisa la valoración antes de continuar:")
    for field, message in errors.items():
        st.markdown(f"- **{field.replace('_', ' ').replace('.', ' · ').title()}**: {message}")


def render_v01(data: dict[str, Any]) -> None:
    if st.session_state.access_role != "evaluator" or not st.session_state.internal_authenticated:
        st.error("Se requiere acceso autenticado de evaluador.")
        return
    screen_title(
        "V01",
        "Evaluación humana de la rúbrica",
        "Compara evidencia inicial y final, documenta la valoración y valida los niveles 1–4.",
    )
    st.caption(f"Sesión {st.session_state.session_code or 'anterior'} · Participante {st.session_state.participant_id}")
    if st.session_state.access_notice:
        st.info(st.session_state.pop("access_notice"))
    st.success("Vista autenticada y separada del recorrido estudiantil.")
    profile = st.session_state.academic_profile
    if profile:
        st.caption(
            f"Contexto del caso: {profile.get('program_label', 'Transversal')} · "
            f"{profile.get('semester_label', 'semestre no registrado')}. "
            "La rúbrica aplicada es la misma para todos los perfiles."
        )
    st.info(
        "Reasoning Delta describe cambio observable en el razonamiento expresado. No mide inteligencia, "
        "personalidad ni pensamiento privado, y no demuestra causalidad."
    )

    rubric = load_rubric()
    initial_evidence = st.session_state.initial_responses
    final_evidence = st.session_state.final_responses.get("responses", {})
    evaluation = st.session_state.reasoning_evaluation
    validated = evaluation.get("status") == "validated"
    current = evaluation if validated else st.session_state.evaluation_draft
    ratings = current.get("ratings", {})

    with st.expander("Evidencia complementaria del recorrido", expanded=False):
        st.markdown(f"**Verify.** {st.session_state.verifications[0].get('assessment', '')}: {st.session_state.verifications[0].get('impact', '')}")
        st.markdown(f"**Challenge.** {st.session_state.challenges[0].get('limitation', '')}")
        st.markdown(f"**Decide.** {st.session_state.decision.get('decision_type', '')}: {st.session_state.decision.get('tradeoff', '')}")
        st.caption("Esta evidencia aporta contexto, pero los niveles deben justificarse contra los mismos cuatro criterios en ambos momentos.")

    if validated:
        st.success(
            f"Evaluación validada con {evaluation['rubric_version']} · "
            f"{evaluation['validated_at'][:19].replace('T', ' ')} UTC"
        )

    with st.form("reasoning_delta_evaluation_form"):
        evaluator_code = st.text_input(
            "Código pseudónimo del evaluador",
            value=current.get("evaluator_code", ""),
            placeholder="EV-DEMO-01",
            disabled=validated,
            help="No escribas nombre, correo ni identificador institucional.",
        )
        captured: dict[str, dict[str, Any]] = {}
        for dimension in rubric["dimensions"]:
            key = dimension["key"]
            rating = ratings.get(key, {})
            with st.expander(dimension["label"], expanded=True):
                st.write(dimension["observes"])
                st.caption(f"Pregunta de control: {dimension['control_question']}")
                evidence_cols = st.columns(2)
                with evidence_cols[0]:
                    st.markdown("**Evidencia inicial**")
                    st.write(initial_evidence.get(key, ""))
                with evidence_cols[1]:
                    st.markdown("**Evidencia final**")
                    st.write(final_evidence.get(key, ""))

                score_cols = st.columns(2)
                initial_score = score_cols[0].selectbox(
                    "Nivel inicial",
                    [1, 2, 3, 4],
                    index=int(rating.get("initial_score", 2)) - 1,
                    format_func=lambda value: f"{value} · {rubric['scale'][str(value)]}",
                    key=f"evaluation_{key}_initial",
                    disabled=validated,
                )
                final_score = score_cols[1].selectbox(
                    "Nivel final",
                    [1, 2, 3, 4],
                    index=int(rating.get("final_score", 2)) - 1,
                    format_func=lambda value: f"{value} · {rubric['scale'][str(value)]}",
                    key=f"evaluation_{key}_final",
                    disabled=validated,
                )
                descriptor_cols = st.columns(2)
                descriptor_cols[0].caption(f"Descriptor inicial: {dimension['descriptors'][str(initial_score)]}")
                descriptor_cols[1].caption(f"Descriptor final: {dimension['descriptors'][str(final_score)]}")
                note = st.text_area(
                    "Evidencia y justificación de la valoración",
                    value=rating.get("evidence_note", ""),
                    height=90,
                    key=f"evaluation_{key}_note",
                    disabled=validated,
                    help=f"Señala qué elementos observables sustentan ambos niveles. Mínimo {MIN_NOTE_CHARS} caracteres.",
                )
                captured[key] = {
                    "initial_score": initial_score,
                    "final_score": final_score,
                    "evidence_note": note,
                }

        confirmed = st.checkbox(
            "Confirmo que una persona aplicó la misma rúbrica a ambos momentos y documentó evidencia observable.",
            value=bool(current.get("human_validation_confirmed", validated)),
            disabled=validated,
        )
        if not validated:
            save_col, validate_col = st.columns(2)
            save_clicked = save_col.form_submit_button("Guardar borrador", width="stretch")
            validate_clicked = validate_col.form_submit_button("Validar y publicar Delta", type="primary", width="stretch")
        else:
            save_clicked = validate_clicked = False

    payload = {
        "evaluator_code": evaluator_code,
        "ratings": captured,
        "human_validation_confirmed": confirmed,
    }
    if save_clicked or validate_clicked:
        errors = save_evaluation(payload, validate=validate_clicked)
        if errors:
            _show_errors(errors)
        elif validate_clicked:
            st.session_state.access_notice = "Evaluación humana validada. El estudiante ya puede actualizar y consultar su Reasoning Delta."
            st.rerun()
        else:
            st.success("Borrador de evaluación guardado. Aún no es visible como resultado.")

    if validated:
        st.caption(f"Sello de integridad: {evaluation['integrity_hash'][:12]}… · La evaluación validada es inmutable.")
        if st.button("Volver a la cola de sesiones", type="primary", width="stretch"):
            unload_review_session()
            st.rerun()
