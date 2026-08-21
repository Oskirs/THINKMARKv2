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


def build_brand_css(brand: dict[str, Any]) -> str:
    """Devuelve estilos con contraste explícito y adaptación para celular."""
    return f"""
        <style>
          :root {{
            color-scheme: light !important;
            --tm-primary: {brand['primary']};
            --tm-primary-dark: {brand['primary_dark']};
            --tm-accent: {brand['accent']};
            --tm-ink: {brand['ink']};
            --tm-muted: {brand['muted']};
            --tm-surface: {brand['surface']};
            --tm-canvas: {brand['canvas']};
            --tm-border: {brand['border']};
            --tm-primary-soft: #F5E9EB;
            --tm-accent-soft: #FFF3E2;
            --tm-accent-border: #F3C98E;
          }}
          html, body {{
            color-scheme: light !important;
            background: var(--tm-canvas) !important;
          }}
          html, body, [class*="css"] {{ font-family: {brand['font_family']}; }}
          .stApp {{ background: var(--tm-canvas); color: var(--tm-ink); }}
          [data-testid="stSidebar"] {{ background: #ffffff; border-right: 1px solid var(--tm-border); }}
          .tm-header {{ display:flex; align-items:center; gap:1rem; margin:.2rem 0 1.25rem; }}
          .tm-header img {{ width: 190px; max-height: 58px; object-fit: contain; object-position:left center; }}
          .tm-tagline {{ color:var(--tm-muted); font-size:.9rem; margin-top:.1rem; }}
          .tm-eyebrow {{ color:var(--tm-primary); font-size:.78rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }}
          .tm-card {{ background:var(--tm-surface); border:1px solid var(--tm-border); border-radius:16px; padding:1.15rem 1.25rem; margin:.65rem 0; box-shadow:0 3px 14px rgba(24,32,51,.04); }}
          .tm-question {{ background:var(--tm-primary-soft); border-left:4px solid var(--tm-primary); border-radius:10px; padding:1rem 1.15rem; font-size:1.05rem; }}
          .tm-opportunity {{ background:var(--tm-accent-soft); border:1px solid var(--tm-accent-border); border-radius:16px; padding:1rem 1.15rem; }}
          .tm-badge {{ display:inline-block; padding:.25rem .55rem; border-radius:999px; background:var(--tm-primary-soft); color:var(--tm-primary-dark); font-size:.76rem; font-weight:700; }}
          .tm-muted {{ color:var(--tm-muted); }}
          div[data-testid="stButton"] > button {{ border-radius:10px; font-weight:650; }}
          div[data-testid="stProgress"] > div > div > div {{ background-color:var(--tm-primary); }}
          div[data-testid="stMetric"] {{ background:#fff; border:1px solid var(--tm-border); padding:.75rem; border-radius:14px; }}

          /* Controles legibles incluso si el navegador fuerza modo oscuro. */
          .stTextInput input,
          .stTextArea textarea,
          .stNumberInput input,
          .stDateInput input,
          [data-baseweb="input"] input {{
            color-scheme: light !important;
            background-color: #FFFFFF !important;
            color: var(--tm-ink) !important;
            -webkit-text-fill-color: var(--tm-ink) !important;
            caret-color: var(--tm-primary) !important;
            border-color: var(--tm-border) !important;
            opacity: 1 !important;
          }}
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder,
          [data-baseweb="input"] input::placeholder {{
            color: #6B7084 !important;
            -webkit-text-fill-color: #6B7084 !important;
            opacity: 1 !important;
          }}
          .stTextInput input:disabled,
          .stTextArea textarea:disabled,
          .stNumberInput input:disabled,
          [data-baseweb="input"] input:disabled {{
            background-color: #EEF0F3 !important;
            color: #3F4558 !important;
            -webkit-text-fill-color: #3F4558 !important;
            opacity: 1 !important;
          }}
          .stTextInput input:focus,
          .stTextArea textarea:focus,
          [data-baseweb="input"] input:focus {{
            border-color: var(--tm-primary) !important;
            box-shadow: 0 0 0 2px rgba(118, 35, 47, .18) !important;
            outline: none !important;
          }}
          [data-baseweb="select"] > div,
          [data-baseweb="select"] input {{
            color-scheme: light !important;
            background-color: #FFFFFF !important;
            color: var(--tm-ink) !important;
            -webkit-text-fill-color: var(--tm-ink) !important;
            border-color: var(--tm-border) !important;
          }}
          [data-baseweb="select"] svg {{ fill: var(--tm-ink) !important; }}
          [data-baseweb="popover"],
          [role="listbox"],
          [role="option"] {{
            color-scheme: light !important;
            background-color: #FFFFFF !important;
            color: var(--tm-ink) !important;
          }}
          [role="option"]:hover,
          [role="option"][aria-selected="true"] {{ background-color: var(--tm-primary-soft) !important; }}
          .stTextInput label,
          .stTextArea label,
          .stSelectbox label,
          .stRadio label,
          .stCheckbox label {{ color: var(--tm-ink) !important; }}

          /* Tamaño táctil mínimo y ajuste responsive. */
          div[data-testid="stButton"] > button,
          div[data-testid="stFormSubmitButton"] > button {{ min-height: 44px; }}
          @media (max-width: 768px) {{
            .block-container {{
              padding: 1rem .85rem 3.5rem !important;
              max-width: 100% !important;
            }}
            h1 {{ font-size: 1.75rem !important; line-height: 1.18 !important; }}
            h2 {{ font-size: 1.4rem !important; line-height: 1.22 !important; }}
            h3 {{ font-size: 1.16rem !important; line-height: 1.25 !important; }}
            p, label, li {{ line-height: 1.5 !important; }}
            [data-testid="stHorizontalBlock"] {{
              flex-wrap: wrap !important;
              gap: .75rem !important;
            }}
            [data-testid="column"] {{
              min-width: 100% !important;
              flex: 1 1 100% !important;
              width: 100% !important;
            }}
            .tm-card, .tm-question, .tm-opportunity {{
              padding: .9rem 1rem !important;
              border-radius: 12px !important;
            }}
            .tm-header img {{ width: 165px !important; max-width: 75vw !important; }}
            .tm-tagline {{ font-size: .84rem !important; }}
            .tm-badge {{ margin-top: .25rem; }}
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            [data-baseweb="input"] input,
            [data-baseweb="select"] input {{
              font-size: 16px !important;
            }}
            .stTextInput input,
            .stNumberInput input,
            [data-baseweb="input"] input {{ min-height: 44px !important; }}
            .stTextArea textarea {{ min-height: 118px !important; }}
            div[data-testid="stButton"] > button,
            div[data-testid="stFormSubmitButton"] > button {{
              width: 100% !important;
              min-height: 48px !important;
            }}
            div[data-testid="stMetric"] {{ padding: .65rem !important; }}
            [data-testid="stDataFrame"] {{ overflow-x: auto !important; }}
          }}

          @media (prefers-color-scheme: dark) {{
            html, body, .stApp, [data-testid="stAppViewContainer"] {{
              color-scheme: light !important;
              background-color: var(--tm-canvas) !important;
              color: var(--tm-ink) !important;
            }}
          }}
        </style>
        """


def apply_brand() -> None:
    st.markdown(build_brand_css(get_brand()), unsafe_allow_html=True)


def runtime_status_label(uses_supabase: bool) -> str:
    """Distingue visualmente una demostración local del piloto conectado."""
    return "PILOTO CONTROLADO" if uses_supabase else "MODO DEMOSTRACIÓN"


def render_brand_header(*, compact: bool = False, status_label: str = "MODO DEMOSTRACIÓN") -> None:
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
        st.markdown(
            f"<div style='text-align:right'><span class='tm-badge'>{status_label}</span></div>",
            unsafe_allow_html=True,
        )
