"""Autenticación interna separada del código pseudónimo estudiantil."""

from __future__ import annotations

from dataclasses import dataclass
import hmac

from src.infrastructure.settings import RuntimeSettings, load_settings


@dataclass(frozen=True)
class AuthIdentity:
    user_id: str
    role: str
    email: str
    mode: str


class InternalAuthService:
    def __init__(self, settings: RuntimeSettings | None = None) -> None:
        self.settings = settings or load_settings()

    def sign_in(self, requested_role: str, identifier: str, password: str) -> AuthIdentity:
        if requested_role not in {"evaluator", "teacher"}:
            raise ValueError("El rol interno solicitado no es válido.")
        if not self.settings.uses_supabase:
            if not self.settings.demo_internal_access:
                raise ValueError("El acceso interno local está desactivado.")
            expected = (
                self.settings.local_evaluator_access_code
                if requested_role == "evaluator"
                else self.settings.local_teacher_access_code
            )
            if not hmac.compare_digest(password.strip(), expected):
                raise ValueError("Código interno incorrecto.")
            return AuthIdentity(f"local-{requested_role}", requested_role, "", "demo")

        from supabase import create_client
        client = create_client(self.settings.supabase_url, self.settings.supabase_publishable_key)
        response = client.auth.sign_in_with_password({"email": identifier.strip(), "password": password})
        user = response.user
        if user is None:
            raise ValueError("No fue posible verificar la cuenta.")
        profile_response = (
            client.table("profiles")
            .select("role,active")
            .eq("id", str(user.id))
            .limit(1)
            .execute()
        )
        if not profile_response.data:
            client.auth.sign_out()
            raise ValueError("La cuenta no tiene un perfil interno autorizado.")
        profile = profile_response.data[0]
        if not profile.get("active") or profile.get("role") != requested_role:
            client.auth.sign_out()
            raise ValueError("La cuenta no está autorizada para el rol seleccionado.")
        return AuthIdentity(str(user.id), requested_role, identifier.strip(), "supabase")
