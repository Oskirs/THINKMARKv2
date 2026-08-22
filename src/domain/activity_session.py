"""Reglas de las sesiones grupales del ajuste 7.3.1."""

from __future__ import annotations

import re
import secrets
from collections.abc import Collection


SESSION_CODE_PATTERN = re.compile(r"^TM-[A-Z0-9]{6}$")
SESSION_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SESSION_STATUSES = ("open", "closed", "archived")


def normalize_session_code(value: str) -> str:
    return value.strip().upper()


def validate_session_code(value: str) -> tuple[str, str | None]:
    normalized = normalize_session_code(value)
    if not SESSION_CODE_PATTERN.fullmatch(normalized):
        return normalized, "Usa el formato TM-XXXXXX con seis letras o números."
    return normalized, None


def generate_session_code(existing: Collection[str] = ()) -> str:
    used = {normalize_session_code(code) for code in existing}
    for _ in range(32):
        suffix = "".join(secrets.choice(SESSION_CODE_ALPHABET) for _ in range(6))
        candidate = f"TM-{suffix}"
        if candidate not in used:
            return candidate
    raise RuntimeError("No fue posible generar un código de sesión único.")


def validate_status_transition(current: str, requested: str) -> None:
    allowed = {
        "open": {"open", "closed"},
        "closed": {"open", "closed", "archived"},
        "archived": {"archived"},
    }
    if current not in SESSION_STATUSES or requested not in allowed[current]:
        raise ValueError(f"Transición de sesión no permitida: {current} → {requested}.")


def participant_may_enter(status: str, already_joined: bool) -> bool:
    if status == "open":
        return True
    if status == "closed":
        return already_joined
    return False
