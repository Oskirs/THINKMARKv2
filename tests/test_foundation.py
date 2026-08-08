"""Pruebas de la estructura navegable y de los fixtures."""

from src.navigation import SCREENS, get_screen, navigation_groups, screen_exists
from src.services.fixtures import load_demo_case


def test_registry_has_twelve_unique_screens() -> None:
    ids = [screen.screen_id for screen in SCREENS]
    assert len(ids) == 12
    assert len(set(ids)) == 12
    assert ids == ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "V01", "E08", "E09", "E10", "D01"]


def test_registry_lookup_and_groups() -> None:
    assert screen_exists("E09")
    assert not screen_exists("X99")
    assert get_screen("D01").label == "Dashboard docente"
    assert sum(len(items) for items in navigation_groups().values()) == 12


def test_demo_fixture_contains_complete_journey() -> None:
    data = load_demo_case()
    expected = {"initial", "coach", "verification", "challenge", "decision", "final", "delta", "thinkmark", "dashboard"}
    assert expected.issubset(data)
    assert data["participant"]["mode"] == "Demostración"
