"""Catálogo transversal y asignación reproducible de casos por perfil académico."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping

from src.services.fixtures import load_demo_case


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "fixtures" / "academic_case_catalog.json"


@lru_cache(maxsize=1)
def load_academic_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as source:
        catalog = json.load(source)
    required = {"catalog_version", "semesters", "areas", "programs"}
    missing = required.difference(catalog)
    if missing:
        raise ValueError(f"Catálogo académico incompleto; faltan: {', '.join(sorted(missing))}")
    if not catalog["programs"] or not catalog["semesters"]:
        raise ValueError("El catálogo académico debe incluir programas y semestres.")
    program_ids = [program["program_id"] for program in catalog["programs"]]
    if len(program_ids) != len(set(program_ids)):
        raise ValueError("El catálogo académico contiene identificadores de programa repetidos.")
    area_ids = [area["area_id"] for area in catalog["areas"]]
    if len(area_ids) != len(set(area_ids)):
        raise ValueError("El catálogo académico contiene identificadores de área repetidos.")
    unknown_areas = {program["area_id"] for program in catalog["programs"]}.difference(area_ids)
    if unknown_areas:
        raise ValueError(f"Hay programas asociados a áreas inexistentes: {', '.join(sorted(unknown_areas))}")
    return catalog


def area_options() -> dict[str, str]:
    """Devuelve escuela/área -> id en el orden publicado por el catálogo."""
    return {area["label"]: area["area_id"] for area in load_academic_catalog()["areas"]}


def program_options(area_id: str | None = None) -> dict[str, str]:
    """Devuelve carrera -> id; si hay área, limita el menú a esa escuela."""
    programs = load_academic_catalog()["programs"]
    if area_id is not None:
        programs = [program for program in programs if program["area_id"] == area_id]
    return {program["label"]: program["program_id"] for program in programs}


def semester_options() -> dict[str, int]:
    return {
        details["label"]: int(semester)
        for semester, details in load_academic_catalog()["semesters"].items()
    }


def validate_academic_selection(program_id: str | None, semester: int | None) -> dict[str, str]:
    errors: dict[str, str] = {}
    valid_programs = set(program_options().values())
    valid_semesters = set(semester_options().values())
    if not program_id or program_id not in valid_programs:
        errors["academic_program"] = "Selecciona la carrera o el caso transversal que corresponda."
    if semester not in valid_semesters:
        errors["academic_semester"] = "Selecciona uno de los semestres disponibles para el piloto."
    return errors


def build_academic_profile(program_id: str, semester: int) -> dict[str, Any]:
    errors = validate_academic_selection(program_id, semester)
    if errors:
        raise ValueError("La selección académica no es válida.")
    catalog = load_academic_catalog()
    program = next(item for item in catalog["programs"] if item["program_id"] == program_id)
    area = next(item for item in catalog["areas"] if item["area_id"] == program["area_id"])
    semester_data = catalog["semesters"][str(semester)]
    return {
        "program_id": program_id,
        "program_label": program["label"],
        "area_id": area["area_id"],
        "area": area["label"],
        "semester": semester,
        "semester_label": semester_data["label"],
        "complexity_label": semester_data["complexity_label"],
        "catalog_version": catalog["catalog_version"],
    }


def build_case_for_profile(program_id: str, semester: int) -> dict[str, Any]:
    """Combina una variante disciplinar con el nivel, sin alterar la rúbrica común."""
    profile = build_academic_profile(program_id, semester)
    catalog = load_academic_catalog()
    program = next(item for item in catalog["programs"] if item["program_id"] == program_id)
    area = next(item for item in catalog["areas"] if item["area_id"] == program["area_id"])
    semester_data = catalog["semesters"][str(semester)]
    scenario = program["scenario"]
    result = deepcopy(load_demo_case())
    result.update({
        "case_id": f"CASO-{program_id.upper().replace('_', '-')}-S{semester}",
        "case_version": f"{catalog['catalog_version']}:{program_id}:S{semester}",
        "course": program["label"],
        "title": scenario["title"],
        "context": scenario["context"],
        "central_question": scenario["central_question"],
        "facts": [scenario["specific_fact"], *area["common_facts"], semester_data["additional_fact"]],
        "analysis_focus": semester_data["analysis_focus"],
        "academic_profile": profile,
    })
    result["verification"] = deepcopy(result["verification"])
    result["verification"]["claim"] = scenario.get("verification_claim", area["verification_claim"])
    return result


def legacy_academic_profile() -> dict[str, Any]:
    return {
        "program_id": "legacy_transversal",
        "program_label": "Caso transversal de una versión anterior",
        "area": "Transversal",
        "semester": 0,
        "semester_label": "Sin semestre registrado",
        "complexity_label": "Versión anterior",
        "catalog_version": "legacy-pre-6.8.2",
    }


def case_for_session(state: Mapping[str, Any]) -> dict[str, Any]:
    """Recupera el caso fijado al crear la sesión; nunca lo recalcula a mitad del recorrido."""
    snapshot = state.get("case_snapshot")
    if isinstance(snapshot, dict) and snapshot.get("case_id"):
        return deepcopy(snapshot)
    profile = state.get("academic_profile") or {}
    program_id = profile.get("program_id")
    semester = profile.get("semester")
    if program_id in set(program_options().values()) and semester in set(semester_options().values()):
        return build_case_for_profile(program_id, int(semester))
    return deepcopy(load_demo_case())
