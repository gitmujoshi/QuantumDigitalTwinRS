"""
Materials & Logistics — real-world customer demos (Streamlit multipage).

Appears in the sidebar when you run: streamlit run app/twin_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
_PYTHON_DIR = _ROOT / "python"
_APP_DIR = _ROOT / "app"
# Insert app first, then python so python wins on import (Streamlit multipage).
for p in (_APP_DIR, _PYTHON_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from lab_sidebar import (  # noqa: E402
    render_execution_mode_block,
    render_materials_logistics_solver_sidebar,
    render_navigation_guide,
)
from materials_logistics_ui import render_materials_logistics_panel  # noqa: E402

st.set_page_config(page_title="Materials & Logistics", layout="wide", page_icon="📦")

with st.sidebar:
    render_navigation_guide(current="materials")
    st.divider()
    render_execution_mode_block()
    st.divider()
    render_materials_logistics_solver_sidebar(use_container=True)
    st.divider()
    with st.expander("💡 This page", expanded=True):
        st.markdown(
            "1. Review **Sample test data** on the main panel.\n"
            "2. Set **Real-world** above for live optimizers.\n"
            "3. Click **Run Example 1** (battery) or **Run Example 2** (fleet).\n\n"
            "Switch to **TwinSentry Lab** in the page list above for pulse simulations."
        )

render_materials_logistics_panel()
