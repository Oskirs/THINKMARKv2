"""Selecciona persistencia sin permitir fallback silencioso en producción."""

from __future__ import annotations

from src.infrastructure.settings import RuntimeSettings, load_settings
from src.repositories.contracts import LearningOpportunityRepository, SessionRepository
from src.repositories.local_learning_opportunities import LocalLearningOpportunityRepository
from src.repositories.local_sessions import LocalSessionRepository


def get_session_repository(settings: RuntimeSettings | None = None) -> SessionRepository:
    settings = settings or load_settings()
    if not settings.uses_supabase:
        return LocalSessionRepository()
    from src.repositories.supabase_sessions import SupabaseSessionRepository
    return SupabaseSessionRepository(settings.supabase_url, settings.supabase_secret_key)


def get_learning_opportunity_repository(settings: RuntimeSettings | None = None) -> LearningOpportunityRepository:
    settings = settings or load_settings()
    if not settings.uses_supabase:
        return LocalLearningOpportunityRepository()
    from src.repositories.supabase_sessions import SupabaseLearningOpportunityRepository
    return SupabaseLearningOpportunityRepository(settings.supabase_url, settings.supabase_secret_key)
