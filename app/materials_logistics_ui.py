"""Materials & Logistics UI — shared by Projects Lab and Streamlit multipage."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = _ROOT / "app"
_PYTHON_DIR = _ROOT / "python"
for p in (_ROOT, _APP_DIR, _PYTHON_DIR):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from portfolio_mode import (  # noqa: E402
    MODE_MOCK,
    MODE_REAL,
    domain_solver_banner,
    get_execution_mode,
    mode_banner,
)

# Flagship real-world demos (sales)
FLAGSHIP_MATERIALS_ID = "li2s_ev_fast_charge"
FLAGSHIP_LOGISTICS_ID = "northeast_pharma_cold_chain"


def render_materials_logistics_panel() -> None:
    from sales_demo_views import (
        render_logistics_result,
        render_logistics_story,
        render_materials_result,
        render_materials_story,
    )

    mode = get_execution_mode()
    st.title("Materials & Logistics")
    mode_banner()
    domain_solver_banner()

    st.markdown(
        """
        **Two real-world customer examples** (MatrixQ PRD). Switch sidebar to
        **Real-world (configured deps)** then use the buttons below — no quantum background needed.
        """
    )

    if mode == MODE_MOCK:
        st.warning(
            "You are in **Mock** mode — logistics uses a **quantum narrative demo** (not OR-Tools). "
            "For classical routing on the same manifests, select **Real-world** in the sidebar."
        )
    else:
        st.success(
            "**Real-world mode** — logistics runs **classical OR-Tools VRP** on the customer manifest "
            "(materials uses classical SPSA / optional Aer)."
        )

    from sales_demo_views import render_flagship_test_data_panel

    render_flagship_test_data_panel()

    st.markdown("### Real-world flagship examples")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Example 1 — Materials")
        st.markdown("**Li₂S EV fast-charge** · Aurora Cell Works")
        st.caption("3-week HPC queue → safe voltage cap (e.g. 4.12 V) + bond length · test data above")
        if st.button("▶ Run Example 1 (Materials)", type="primary", use_container_width=True, key="flagship_mat"):
            _run_flagship_materials(mode)
    with c2:
        st.markdown("#### Example 2 — Logistics")
        st.markdown("**Northeast pharma cold-chain** · MedRoute 3PL")
        st.caption("14 hospitals/pharmacies · route map · fuel savings · test data above")
        if st.button("▶ Run Example 2 (Logistics)", type="primary", use_container_width=True, key="flagship_log"):
            _run_flagship_logistics(mode)

    if st.session_state.get("flagship_materials_result"):
        st.divider()
        st.markdown("### Example 1 — Results")
        render_materials_result(st.session_state["flagship_materials_result"])

    if st.session_state.get("flagship_logistics_result"):
        st.divider()
        st.markdown("### Example 2 — Results")
        from domain_mocks.sales_demos import get_logistics_scenario

        render_logistics_result(
            st.session_state["flagship_logistics_result"],
            get_logistics_scenario(FLAGSHIP_LOGISTICS_ID),
        )

    st.divider()
    st.caption("More scenarios · `docs/sales-demo-guide.md`")
    tab_vqe, tab_qaoa = st.tabs(["All materials scenarios", "All logistics scenarios"])

    with tab_vqe:
        _materials_tab(mode, render_materials_story, render_materials_result)
    with tab_qaoa:
        _logistics_tab(mode, render_logistics_story, render_logistics_result)


def _run_flagship_materials(mode: str) -> None:
    try:
        from domain_mocks.sales_demos import get_materials_scenario
        from domain_mocks.vqe_materials import run_vqe_materials

        s = get_materials_scenario(FLAGSHIP_MATERIALS_ID)
        st.session_state["sales_mat_scenario"] = FLAGSHIP_MATERIALS_ID
        st.session_state["flagship_materials_result"] = run_vqe_materials(
            s.request,
            real=(mode == MODE_REAL),
            scenario_id=FLAGSHIP_MATERIALS_ID,
        )
        st.rerun()
    except Exception:
        st.error("Example 1 failed.")
        st.code(traceback.format_exc())


def _run_flagship_logistics(mode: str) -> None:
    try:
        from domain_mocks.sales_demos import get_logistics_scenario
        from domain_mocks.logistics_qaoa import run_logistics_qaoa

        s = get_logistics_scenario(FLAGSHIP_LOGISTICS_ID)
        st.session_state["sales_log_scenario"] = FLAGSHIP_LOGISTICS_ID
        st.session_state["flagship_logistics_result"] = run_logistics_qaoa(
            s.request,
            real=(mode == MODE_REAL),
            scenario_id=FLAGSHIP_LOGISTICS_ID,
        )
        st.rerun()
    except Exception:
        st.error("Example 2 failed.")
        st.code(traceback.format_exc())


def _materials_tab(mode, render_story, render_result) -> None:
    try:
        from domain_mocks.sales_demos import list_materials_scenarios
        from domain_mocks.vqe_materials import run_vqe_materials
    except Exception:
        st.error("Could not import materials demo modules.")
        st.code(traceback.format_exc())
        return

    scenarios = list_materials_scenarios()
    labels = {s.id: s.title for s in scenarios}
    sid = st.selectbox(
        "Customer scenario",
        options=list(labels.keys()),
        format_func=lambda k: labels[k],
        key="sales_mat_scenario",
    )
    scenario = next(s for s in scenarios if s.id == sid)
    render_story(scenario)

    btn = "Run analysis (real compute)" if mode == MODE_REAL else "Run analysis (demo dataset)"
    if st.button(btn, type="primary", key="mq_vqe_run"):
        st.session_state["sales_materials_result"] = run_vqe_materials(
            scenario.request,
            real=(mode == MODE_REAL),
            scenario_id=sid,
        )
        st.rerun()

    out = st.session_state.get("sales_materials_result")
    if out and (out.get("sales_demo") or {}).get("scenario_id") == sid:
        render_result(out)
        with st.expander("Technical JSON (optional)", expanded=False):
            st.json(out)


def _logistics_tab(mode, render_story, render_result) -> None:
    try:
        from domain_mocks.sales_demos import list_logistics_scenarios
        from domain_mocks.logistics_qaoa import run_logistics_qaoa
    except Exception:
        st.error("Could not import logistics demo modules.")
        st.code(traceback.format_exc())
        return

    scenarios = list_logistics_scenarios()
    labels = {s.id: s.title for s in scenarios}
    sid = st.selectbox(
        "Customer scenario",
        options=list(labels.keys()),
        format_func=lambda k: labels[k],
        key="sales_log_scenario",
    )
    scenario = next(s for s in scenarios if s.id == sid)
    render_story(scenario)

    btn = "Optimize routes (real compute)" if mode == MODE_REAL else "Optimize routes (demo dataset)"
    if st.button(btn, type="primary", key="mq_log_run"):
        st.session_state["sales_logistics_result"] = run_logistics_qaoa(
            scenario.request,
            real=(mode == MODE_REAL),
            scenario_id=sid,
        )
        st.rerun()

    out = st.session_state.get("sales_logistics_result")
    if out and (out.get("sales_demo") or {}).get("scenario_id") == sid:
        render_result(out, scenario)
        with st.expander("Technical JSON (optional)", expanded=False):
            st.json(out)
