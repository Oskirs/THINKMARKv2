"""Configuración validada desde variables de entorno o secretos de Streamlit."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


class ConfigurationError(RuntimeError):
    pass


def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value.strip()
    try:
        import streamlit as st
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def _as_bool(value: str, default: bool = False) -> bool:
    if not value:
        return default
    return value.casefold() in {"1", "true", "yes", "sí", "on"}


@dataclass(frozen=True)
class RuntimeSettings:
    persistence_mode: str
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    demo_internal_access: bool
    local_evaluator_access_code: str
    local_teacher_access_code: str

    @property
    def uses_supabase(self) -> bool:
        return self.persistence_mode == "supabase"

    def validate(self) -> None:
        if self.persistence_mode not in {"local", "supabase"}:
            raise ConfigurationError("PERSISTENCE_MODE debe ser 'local' o 'supabase'.")
        if self.uses_supabase:
            missing = [name for name, value in (
                ("SUPABASE_URL", self.supabase_url),
                ("SUPABASE_PUBLISHABLE_KEY", self.supabase_publishable_key),
                ("SUPABASE_SECRET_KEY", self.supabase_secret_key),
            ) if not value]
            if missing:
                raise ConfigurationError("Falta configuración obligatoria de Supabase: " + ", ".join(missing))
            if not self.supabase_url.startswith("https://"):
                raise ConfigurationError("SUPABASE_URL debe utilizar HTTPS.")
            if not self.supabase_publishable_key.startswith("sb_publishable_"):
                raise ConfigurationError("Configura una clave publishable vigente de Supabase.")
            if not self.supabase_secret_key.startswith("sb_secret_"):
                raise ConfigurationError("Configura una clave secret vigente; no uses service_role heredada.")
            if self.demo_internal_access:
                raise ConfigurationError("DEMO_INTERNAL_ACCESS debe estar desactivado en modo Supabase.")


def load_settings() -> RuntimeSettings:
    settings = RuntimeSettings(
        persistence_mode=_secret("PERSISTENCE_MODE", "local").casefold(),
        supabase_url=_secret("SUPABASE_URL"),
        supabase_publishable_key=_secret("SUPABASE_PUBLISHABLE_KEY"),
        supabase_secret_key=_secret("SUPABASE_SECRET_KEY"),
        demo_internal_access=_as_bool(_secret("DEMO_INTERNAL_ACCESS", "true"), True),
        local_evaluator_access_code=_secret("LOCAL_EVALUATOR_ACCESS_CODE", "EV-DEMO-2026"),
        local_teacher_access_code=_secret("LOCAL_TEACHER_ACCESS_CODE", "DOC-DEMO-2026"),
    )
    settings.validate()
    return settings
