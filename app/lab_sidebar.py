"""
Shared left-sidebar navigation and help tips for Twin Lab & Projects Lab.
"""

from __future__ import annotations

from typing import Literal

import streamlit as st

from portfolio_mode import (
    LOGISTICS_SOLVER_MOCK,
    LOGISTICS_SOLVER_REAL_FALLBACK,
    LOGISTICS_SOLVER_REAL_ORTOOLS,
    MATERIALS_SOLVER_MOCK,
    MATERIALS_SOLVER_REAL,
    MODE_MOCK,
    MODE_REAL,
    get_execution_mode,
    render_execution_mode_sidebar,
)

LabPage = Literal["twin", "materials", "projects"]

# --- Menu copy (shown in sidebar expander) ---

PAGE_GUIDE: dict[str, str] = {
    "twin": (
        "**TwinSentry Lab** — Natural-language pulse commands → BAML policy → Rust 2-qubit "
        "simulation → Bloch spheres. Use for quantum control / digital-twin demos."
    ),
    "materials": (
        "**Materials & Logistics** — Sales-friendly customer scenarios: Li₂S battery lab "
        "(Example 1) and pharma fleet routing (Example 2). Open sample test data first, "
        "then **Run Example 1 / 2** in Real-world mode."
    ),
    "projects": (
        "**Projects Lab** — Full portfolio in one app: TwinSentry, AeroQ CFD, Materials & "
        "Logistics, PQC readiness, PRDs. Pick a **workspace** below."
    ),
}

PROJECT_GUIDE: dict[str, str] = {
    "TwinSentry": (
        "Same pipeline as Twin Lab: intent → policy → Rust twin. Good for pulse engineers "
        "and quick API-style runs without the full Twin Lab chrome."
    ),
    "AeroQ": (
        "Hybrid CFD scaffold: linear solve (PennyLane/Qiskit), OSSLBM one-step (Real-world + "
        "`AeroQ/.venv`), regional weather mock (Mock mode tab)."
    ),
    "Materials & Logistics": (
        "Flagship **Example 1** (Li₂S / Aurora) and **Example 2** (MedRoute pharma routes). "
        "Sidebar shows **Demo: Quantum narrative (mock)** vs **Solver: Classical (OR-Tools)** — "
        "use Mock for keynotes, Real-world for the same manifests with OR-Tools."
    ),
    "Drug discovery (mock)": (
        "Staged docking → VQE stub → ML ranking. **Mock mode only** — not a real chemistry pipeline."
    ),
    "Post-Quantum Crypto": (
        "Education: Grover/Shor impact, hybrid KEM/signature toy demos. Orthogonal to the twin."
    ),
    "PRDs": (
        "Read consolidated product requirements (TwinSentry, AeroQ, MatrixQ, PQC) in-browser."
    ),
}

EXECUTION_MODE_HELP = """
| Mode | Use when |
|------|----------|
| **Mock (sandbox)** | Keynotes, repeatable numbers, no IBM token, synthetic QPU/NWP/drug |
| **Real-world** | Live Qiskit Aer, IBM Quantum (token), AeroQ OSSLBM, classical VQE/VRP |
"""


def render_navigation_guide(*, current: LabPage) -> None:
    """Top-of-sidebar: where you are + how to switch pages."""
    st.sidebar.markdown("### Portfolio Lab")
    with st.sidebar.expander("📖 Menu guide", expanded=False):
        st.markdown(PAGE_GUIDE["twin"])
        st.markdown("---")
        st.markdown(PAGE_GUIDE["materials"])
        st.markdown("---")
        st.markdown(PAGE_GUIDE.get("projects", ""))
        st.markdown("---")
        st.markdown(EXECUTION_MODE_HELP)
        st.caption("Twin Lab: use the **app page list** at the top of this sidebar to switch pages.")

    labels = {
        "twin": "You are on: **TwinSentry Lab**",
        "materials": "You are on: **Materials & Logistics**",
        "projects": "You are on: **Projects Lab**",
    }
    st.sidebar.info(labels.get(current, ""))


def render_execution_mode_block() -> None:
    """Execution mode with extra help (call inside `with st.sidebar:`)."""
    # st.sidebar.* works correctly even inside `with st.sidebar:` — no use_container kwarg needed.
    render_execution_mode_sidebar()


def render_materials_logistics_solver_sidebar(*, use_container: bool = False) -> None:
    """Sidebar labels so sales never conflates quantum demo vs classical solvers."""
    box = st if use_container else st.sidebar
    mode = get_execution_mode()
    box.markdown("### What runs on this page")
    if mode == MODE_MOCK:
        box.info(f"**Logistics:** {LOGISTICS_SOLVER_MOCK}")
        box.caption(f"**Materials:** {MATERIALS_SOLVER_MOCK}")
    else:
        try:
            from routing.ortools_vrp import ORTOOLS_AVAILABLE
        except ImportError:
            ORTOOLS_AVAILABLE = False
        if ORTOOLS_AVAILABLE:
            box.success(f"**Logistics:** {LOGISTICS_SOLVER_REAL_ORTOOLS}")
        else:
            box.warning(
                f"**Logistics:** {LOGISTICS_SOLVER_REAL_FALLBACK} "
                "(install `pip install ortools` for OR-Tools)"
            )
        box.caption(f"**Materials:** {MATERIALS_SOLVER_REAL}")


def render_project_picker() -> str:
    """Projects Lab workspace selector with dynamic help tip."""
    st.sidebar.markdown("### Workspace")
    projects = [
        "TwinSentry",
        "AeroQ",
        "Materials & Logistics",
        "Post-Quantum Crypto",
        "PRDs",
    ]
    if get_execution_mode() == MODE_MOCK:
        projects.insert(3, "Drug discovery (mock)")

    project = st.sidebar.radio(
        "Choose a project",
        projects,
        index=0,
        key="projects_lab_workspace",
        help="Each workspace is a different product line in the portfolio. "
        "Details appear below after you select one.",
    )
    tip = PROJECT_GUIDE.get(project, "")
    if tip:
        st.sidebar.caption(f"💡 {tip}")
    return project


def render_twin_lab_sidebar(
    *,
    llm_env: object,
    sample_prompts: list,
    sidebar_presets: dict[str, str],
    cloud_backend_selectbox_fn,
) -> tuple[int, float, str | None, int]:
    """
    Twin Lab controls. Returns (n_steps, dt, cloud_backend, cloud_shots).
    Call inside `with st.sidebar:` after navigation + execution mode.
    """
    st.markdown("### Twin controls")

    n_steps = st.slider(
        "RK4 steps",
        min_value=16,
        max_value=2048,
        value=64,
        step=16,
        key="rk4_steps",
        help="Time steps for the Rust TDSE integrator. Higher = smoother evolution, slower run.",
    )
    dt_exp = st.slider(
        "log₁₀(dt / s)",
        min_value=-14.0,
        max_value=-9.0,
        value=-11.5,
        step=0.5,
        key="dt_exp_slider",
        help="Simulation timestep in seconds (log scale). Default ≈ 3×10⁻¹² s.",
    )
    dt = float(10**dt_exp)
    st.caption(f"dt = {dt:.3e} s")

    st.divider()
    st.markdown("### Quick presets")
    st.caption("Loads a sample intent into the command box.")
    for name in sidebar_presets:
        if st.button(name, use_container_width=True, key=f"preset_{name}"):
            st.session_state.intent_text = sidebar_presets[name]
            st.rerun()

    st.markdown("### Sample prompts")
    labels = [label for label, _ in sample_prompts]
    pick = st.selectbox(
        "Catalog",
        options=["(choose…)"] + labels,
        key="sample_prompt_picker",
        help="Full list from docs/sample-quantum-prompts.md",
    )
    if st.button("Insert into command box", use_container_width=True, key="insert_sample"):
        if pick and pick != "(choose…)":
            for label, text in sample_prompts:
                if label == pick:
                    st.session_state.intent_text = text
                    st.rerun()

    st.divider()
    st.markdown("### Quantum cloud (optional)")
    st.caption(
        "Gate circuit after the twin (not the analog Rust pulse). "
        "Options follow **Execution mode**: Off, mock vendors, or Aer/IBM."
    )
    cloud_backend = cloud_backend_selectbox_fn(key="cloud_backend_select")
    cloud_shots = st.slider(
        "Cloud shots",
        min_value=256,
        max_value=4096,
        value=1024,
        step=256,
        key="cloud_shots",
        help="Shots for Qiskit Aer / IBM / mock vendor submit.",
    )

    st.divider()
    st.markdown("### Health")
    oll = llm_env.ollama_status()
    if oll.get("ok"):
        if oll.get("model_ready"):
            st.success(f"Ollama · `{oll['model']}`")
        else:
            st.warning(f"Ollama up — pull `{oll['model']}`")
    else:
        st.error("Ollama down · run `ollama serve`")

    lf = llm_env.langfuse_status()
    if lf.get("ok"):
        st.success("Langfuse OK")
    elif lf.get("keys_set"):
        st.error("Langfuse keys set · server down")
    else:
        st.caption("Langfuse off (optional traces)")

    return n_steps, dt, None if cloud_backend == "off" else cloud_backend, cloud_shots
