"""Regresiones de contraste móvil y lenguaje claro del paso 6.8.1."""

from pathlib import Path

from src.domain.thinkmark import THINKMARK_LABELS
from src.ui.brand import build_brand_css, get_brand, runtime_status_label
from src.ui.layout import role_uses_session_context
from src.ui.language import load_language_config


ROOT = Path(__file__).resolve().parents[1]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.removeprefix("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _luminance(hex_color: str) -> float:
    channels = []
    for value in _rgb(hex_color):
        normalized = value / 255
        channels.append(normalized / 12.92 if normalized <= 0.04045 else ((normalized + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(first: str, second: str) -> float:
    light, dark = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_brand_has_explicit_light_inputs_and_mobile_layout() -> None:
    brand = get_brand()
    css = build_brand_css(brand)
    assert "color-scheme: light !important" in css
    assert ".stTextArea textarea" in css
    assert "-webkit-text-fill-color: var(--tm-ink) !important" in css
    assert "caret-color: var(--tm-primary) !important" in css
    assert "@media (max-width: 768px)" in css
    assert "min-height: 48px" in css
    assert "font-size: 16px !important" in css
    assert "min-height: 44px !important" in css
    assert "min-width: 100%" in css


def test_brand_text_contrast_exceeds_normal_text_requirement() -> None:
    brand = get_brand()
    assert _contrast(brand["surface"], brand["ink"]) >= 4.5
    assert _contrast(brand["canvas"], brand["ink"]) >= 4.5


def test_plain_language_policy_targets_undergraduates_and_defines_terms() -> None:
    config = load_language_config()
    assert config["policy_version"] == "plain-language-undergraduate-v2"
    assert "1.er, 5.º y 7.º semestre" in config["audience"]
    assert {"evidence", "assumption", "counterargument", "tradeoff", "uncertainty", "reasoning_delta", "thinkmark"}.issubset(config["terms"])
    assert all(item["plain"].strip() for item in config["terms"].values())


def test_student_interface_removed_unexplained_advanced_phrases() -> None:
    source = (ROOT / "src/screens/student.py").read_text(encoding="utf-8")
    forbidden = (
        "preguntas socráticas",
        "trade-off que tú incorporaste",
        "¿Qué incertidumbre permanece?",
        "Problema reformulado",
        "Captura una línea base",
        "awaiting_review",
        "Human Reasoning Signature",
    )
    assert not any(phrase in source for phrase in forbidden)


def test_thinkmark_labels_use_clear_student_facing_language() -> None:
    assert THINKMARK_LABELS["tm_problem_reframed"] == "Cómo entiendes el problema al final"
    assert THINKMARK_LABELS["tm_remaining_limits"] == "Lo que todavía falta saber"


def test_runtime_status_distinguishes_pilot_from_local_demo() -> None:
    assert runtime_status_label(True) == "PILOTO CONTROLADO"
    assert runtime_status_label(False) == "MODO DEMOSTRACIÓN"


def test_teacher_sidebar_does_not_show_student_session_context() -> None:
    assert role_uses_session_context("student")
    assert role_uses_session_context("evaluator")
    assert not role_uses_session_context("teacher")


def test_faculty_dashboard_title_is_consistently_in_spanish() -> None:
    source = (ROOT / "src/screens/faculty.py").read_text(encoding="utf-8")
    assert "Dashboard docente de aprendizaje" in source
    assert "Faculty Learning Dashboard" not in source
