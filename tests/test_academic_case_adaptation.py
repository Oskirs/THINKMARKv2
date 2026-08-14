"""Pruebas del catálogo transversal y la asignación del paso 6.8.2."""

from copy import deepcopy

import pytest

from src.repositories.local_sessions import validate_record_transition
from src.services.academic_cases import (
    area_options,
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
    assert catalog["catalog_version"] == "THINKMARK-UAG-GDL-v2"
    assert catalog["source"]["url"] == "https://www.uag.mx/es/profesional"
    assert len(area_options()) == 8
    assert len(program_options()) == 42
    assert set(semester_options().values()) == {1, 5, 7}
    assert "Otra carrera / caso transversal" in program_options("transversal")
    assert "Ingeniería en Mecatrónica" in program_options("ingenierias_agroindustria")
    assert "Ciencias de la Nutrición" in program_options("salud")


def test_selection_requires_both_profile_fields() -> None:
    assert set(validate_academic_selection(None, None)) == {"academic_program", "academic_semester"}
    assert validate_academic_selection("derecho", 7) == {}


def test_case_changes_by_program_and_semester() -> None:
    law_fifth = build_case_for_profile("derecho", 5)
    software_seventh = build_case_for_profile("ingenieria_software_mineria_datos", 7)
    law_seventh = build_case_for_profile("derecho", 7)
    law_first = build_case_for_profile("derecho", 1)
    assert law_fifth["case_id"] == "CASO-DERECHO-S5"
    assert software_seventh["case_id"] == "CASO-INGENIERIA-SOFTWARE-MINERIA-DATOS-S7"
    assert law_fifth["central_question"] != software_seventh["central_question"]
    assert law_fifth["analysis_focus"] != law_seventh["analysis_focus"]
    assert law_fifth["facts"][-1] != law_seventh["facts"][-1]
    assert law_first["academic_profile"]["semester_label"] == "1.er semestre"
    assert law_first["analysis_focus"] != law_fifth["analysis_focus"]


def test_all_catalog_profiles_build_the_three_pilot_variants() -> None:
    profiles = program_options()
    built = [build_case_for_profile(program_id, semester) for program_id in profiles.values() for semester in (1, 5, 7)]
    assert len(built) == 126
    assert len({case["case_version"] for case in built}) == 126
    assert all(len(case["facts"]) == 4 for case in built)


def test_profile_records_version_and_readable_labels() -> None:
    profile = build_academic_profile("ciencias_nutricion", 7)
    assert profile["program_label"] == "Ciencias de la Nutrición"
    assert profile["area"] == "Escuela de Medicina y Ciencias de la Salud"
    assert profile["semester_label"] == "7.º semestre"
    assert profile["catalog_version"] == "THINKMARK-UAG-GDL-v2"


def test_session_uses_its_frozen_case_snapshot() -> None:
    assigned = build_case_for_profile("psicologia", 5)
    resolved = case_for_session({"case_snapshot": assigned})
    assert resolved == assigned
    resolved["title"] = "cambio local"
    assert assigned["title"] != resolved["title"]


def test_repository_rejects_profile_or_case_reassignment() -> None:
    profile = build_academic_profile("administracion_empresas", 5)
    case = build_case_for_profile("administracion_empresas", 5)
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
        validate_record_transition(existing, existing | {"case_snapshot": build_case_for_profile("administracion_empresas", 7)})
