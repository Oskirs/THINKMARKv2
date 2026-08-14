"""Pruebas del catálogo transversal y la asignación del paso 6.8.2."""

from copy import deepcopy

import pytest

from src.repositories.local_sessions import validate_record_transition
from src.services.academic_cases import (
    build_academic_profile,
    build_case_for_profile,
    case_for_session,
    load_academic_catalog,
    program_options,
    semester_options,
    validate_academic_selection,
)


def test_catalog_exposes_program_and_semester_menus() -> None:
    catalog = load_academic_catalog()
    assert catalog["catalog_version"] == "THINKMARK-academic-cases-demo-v1"
    assert len(program_options()) >= 6
    assert set(semester_options().values()) == {5, 7}
    assert "Caso transversal / otra carrera" in program_options()


def test_selection_requires_both_profile_fields() -> None:
    assert set(validate_academic_selection(None, None)) == {"academic_program", "academic_semester"}
    assert validate_academic_selection("derecho", 7) == {}


def test_case_changes_by_program_and_semester() -> None:
    law_fifth = build_case_for_profile("derecho", 5)
    software_seventh = build_case_for_profile("ingenieria_software", 7)
    law_seventh = build_case_for_profile("derecho", 7)
    assert law_fifth["case_id"] == "CASO-DER-IA-01-S5"
    assert software_seventh["case_id"] == "CASO-ING-IA-01-S7"
    assert law_fifth["central_question"] != software_seventh["central_question"]
    assert law_fifth["analysis_focus"] != law_seventh["analysis_focus"]
    assert law_fifth["facts"][-1] != law_seventh["facts"][-1]


def test_profile_records_version_and_readable_labels() -> None:
    profile = build_academic_profile("medicina", 7)
    assert profile["program_label"] == "Medicina y Ciencias de la Salud"
    assert profile["semester_label"] == "7.º semestre"
    assert profile["catalog_version"] == "THINKMARK-academic-cases-demo-v1"


def test_session_uses_its_frozen_case_snapshot() -> None:
    assigned = build_case_for_profile("psicologia", 5)
    resolved = case_for_session({"case_snapshot": assigned})
    assert resolved == assigned
    resolved["title"] = "cambio local"
    assert assigned["title"] != resolved["title"]


def test_repository_rejects_profile_or_case_reassignment() -> None:
    profile = build_academic_profile("administracion", 5)
    case = build_case_for_profile("administracion", 5)
    existing = {
        "academic_profile": profile,
        "case_snapshot": case,
        "baseline_locked": False,
        "reflection_submitted": False,
        "thinkmark_decided": False,
        "completed": False,
    }
    validate_record_transition(existing, deepcopy(existing))
    with pytest.raises(ValueError, match="perfil académico"):
        validate_record_transition(existing, existing | {"academic_profile": build_academic_profile("derecho", 5)})
    with pytest.raises(ValueError, match="caso asignado"):
        validate_record_transition(existing, existing | {"case_snapshot": build_case_for_profile("administracion", 7)})
