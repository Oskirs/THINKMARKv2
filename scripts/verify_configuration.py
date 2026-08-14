"""Verifica configuración y conectividad sin imprimir secretos."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.infrastructure.settings import ConfigurationError, load_settings
from src.repositories.factory import get_session_repository


def main() -> int:
    try:
        settings = load_settings()
        records = get_session_repository(settings).list_all()
    except ConfigurationError as exc:
        print(f"CONFIGURACIÓN INVÁLIDA: {exc}")
        return 2
    except Exception as exc:
        print(f"CONEXIÓN NO DISPONIBLE: {type(exc).__name__}: {exc}")
        return 3
    mode = "Supabase multiusuario" if settings.uses_supabase else "local de demostración"
    print(f"OK · modo {mode} · {len(records)} sesión(es) accesibles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
