"""Registro único de las doce pantallas del MVP."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from importlib import import_module
from typing import Any, Callable


Renderer = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class Screen:
    screen_id: str
    label: str
    group: str
    step: int
    renderer_path: str

    @cached_property
    def renderer(self) -> Renderer:
        """Importa la vista sólo cuando Streamlit realmente la necesita."""
        module_name, function_name = self.renderer_path.split(":", maxsplit=1)
        module = import_module(module_name)
        return getattr(module, function_name)


SCREENS: tuple[Screen, ...] = (
    Screen("E01", "Inicio y consentimiento", "Recorrido del estudiante", 1, "src.screens.student:render_e01"),
    Screen("E02", "Caso y posición inicial", "Recorrido del estudiante", 2, "src.screens.student:render_e02"),
    Screen("E03", "AI Coach", "Recorrido del estudiante", 3, "src.screens.student:render_e03"),
    Screen("E04", "Verify", "Recorrido del estudiante", 4, "src.screens.student:render_e04"),
    Screen("E05", "Challenge", "Recorrido del estudiante", 5, "src.screens.student:render_e05"),
    Screen("E06", "Decide", "Recorrido del estudiante", 6, "src.screens.student:render_e06"),
    Screen("E07", "Reflect", "Recorrido del estudiante", 7, "src.screens.student:render_e07"),
    Screen("V01", "Validación de rúbrica", "Evaluación", 8, "src.screens.evaluator:render_v01"),
    Screen("E08", "Reasoning Delta", "Resultados del estudiante", 9, "src.screens.student:render_e08"),
    Screen("E09", "ThinkMark", "Resultados del estudiante", 10, "src.screens.student:render_e09"),
    Screen("E10", "Feedback y cierre", "Resultados del estudiante", 11, "src.screens.student:render_e10"),
    Screen("D01", "Dashboard docente", "Vista docente", 12, "src.screens.faculty:render_d01"),
)

_BY_ID = {screen.screen_id: screen for screen in SCREENS}


def get_screen(screen_id: str) -> Screen:
    return _BY_ID[screen_id]


def screen_exists(screen_id: str) -> bool:
    return screen_id in _BY_ID


def navigation_groups() -> dict[str, list[Screen]]:
    groups: dict[str, list[Screen]] = {}
    for screen in SCREENS:
        groups.setdefault(screen.group, []).append(screen)
    return groups
