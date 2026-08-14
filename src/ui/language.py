"""Ayudas de lenguaje claro para el recorrido estudiantil."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "language.json"


@lru_cache(maxsize=1)
def load_language_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_term_guide(*keys: str, title: str = "Palabras útiles para esta etapa") -> None:
    config = load_language_config()
    terms = config["terms"]
    selected = [terms[key] for key in keys if key in terms]
    if not selected:
        return
    with st.expander(title, expanded=False):
        for item in selected:
            st.markdown(f"**{item['term']}:** {item['plain']}")
        st.caption(f"Guía de lenguaje: {config['policy_version']}")
