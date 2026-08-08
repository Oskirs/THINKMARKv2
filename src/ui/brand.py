"""Marca configurable sin dependencias con la lógica del MVP."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_brand() -> dict[str, Any]:
    with (ROOT / "config" / "brand.json").open(encoding="utf-8") as config:
        return json.load(config)


def apply_brand() -> None:
    brand = get_brand()
    st.markdown(
        f"""
        <style>
          :root {{
            --tm-primary: {brand['primary']};
            --tm-primary-dark: {brand['primary_dark']};
            --tm-accent: {brand['accent']};
            --tm-ink: {brand['ink']};
            --tm-muted: {brand['muted']};
            --tm-surface: {brand['surface']};
            --tm-canvas: {brand['canvas']};
            --tm-border: {brand['border']};
          }}
          html, body, [class*="css"] {{ font-family: {brand['font_family']}; }}
          .stApp {{ background: var(--tm-canvas); color: var(--tm-ink); }}
          [data-testid="stSidebar"] {{ background: #ffffff; border-right: 1px solid var(--tm-border); }}
          .tm-header {{ display:flex; align-items:center; gap:1rem; margin:.2rem 0 1.25rem; }}
          .tm-header img {{ width: 190px; max-height: 58px; object-fit: contain; object-position:left center; }}
          .tm-tagline {{ color:var(--tm-muted); font-size:.9rem; margin-top:.1rem; }}
          .tm-eyebrow {{ color:var(--tm-primary); font-size:.78rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }}
          .tm-card {{ background:var(--tm-surface); border:1px solid var(--tm-border); border-radius:16px; padding:1.15rem 1.25rem; margin:.65rem 0; box-shadow:0 3px 14px rgba(24,32,51,.04); }}
          .tm-question {{ background:#EFEDFF; border-left:4px solid var(--tm-primary); border-radius:10px; padding:1rem 1.15rem; font-size:1.05rem; }}
          .tm-opportunity {{ background:#EAF9F6; border:1px solid #BCE8DF; border-radius:16px; padding:1rem 1.15rem; }}
          .tm-badge {{ display:inline-block; padding:.25rem .55rem; border-radius:999px; background:#EFEDFF; color:var(--tm-primary-dark); font-size:.76rem; font-weight:700; }}
          .tm-muted {{ color:var(--tm-muted); }}
          div[data-testid="stButton"] > button {{ border-radius:10px; font-weight:650; }}
          div[data-testid="stMetric"] {{ background:#fff; border:1px solid var(--tm-border); padding:.75rem; border-radius:14px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header(*, compact: bool = False) -> None:
    brand = get_brand()
    logo = ROOT / brand["logo_path"]
    if compact:
        if logo.exists():
            st.image(str(logo), width=180)
        else:
            st.markdown(f"### {brand['app_name']}")
        st.caption(brand["tagline"])
        return

    left, right = st.columns([3, 1], vertical_alignment="center")
    with left:
        if logo.exists():
            st.image(str(logo), width=220)
        else:
            st.title(brand["app_name"])
        st.markdown(f"<div class='tm-tagline'>{brand['tagline']}</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div style='text-align:right'><span class='tm-badge'>MODO DEMOSTRACIÓN</span></div>", unsafe_allow_html=True)
