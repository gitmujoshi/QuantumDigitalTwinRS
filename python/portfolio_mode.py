"""Shared Mock vs Real-world execution mode for Streamlit lab UIs."""

from __future__ import annotations

from typing import Literal

import streamlit as st

ExecutionMode = Literal["mock", "real"]

MODE_MOCK: ExecutionMode = "mock"
MODE_REAL: ExecutionMode = "real"

# Quantum cloud / QPU submission (after Rust twin)
CLOUD_OFF = "off"
CLOUD_MOCK_OPTIONS = ("mock_ibm", "mock_ionq", "mock_rigetti")
CLOUD_REAL_OPTIONS = ("local_aer", "ibm_quantum")

CLOUD_LABELS: dict[str, str] = {
    "off": "Off (Rust twin only)",
    "mock_ibm": "Mock IBM Quantum",
    "mock_ionq": "Mock IonQ",
    "mock_rigetti": "Mock Rigetti",
    "local_aer": "Qiskit Aer (local sim)",
    "ibm_quantum": "IBM Quantum (token required)",
}

# AeroQ regional forecast
WEATHER_MOCK_BACKENDS = ("hybrid_qsvt", "classical_hpc", "qpu_accelerator_stub")
WEATHER_REAL_BACKENDS = ("classical_hpc",)  # closest bundled "real" baseline


def get_execution_mode() -> ExecutionMode:
    return st.session_state.get("execution_mode", MODE_MOCK)


def render_execution_mode_sidebar(*, use_container: bool = False) -> ExecutionMode:
    """Sidebar control; returns ``mock`` or ``real``.

    Pass ``use_container=True`` when already inside ``with st.sidebar:``.
    """
    box = st if use_container else st.sidebar
    box.markdown("### Execution mode")
    prev = st.session_state.get("execution_mode", MODE_MOCK)
    choice = box.radio(
        "Run against",
        ["Mock (sandbox)", "Real-world (configured deps)"],
        index=0 if prev == MODE_MOCK else 1,
        key="execution_mode_radio",
        help=(
            "**Mock** — repeatable demo data: mock IBM/IonQ/Rigetti, synthetic weather/drug, "
            "fixed sales numbers for VQE/VRP.\n\n"
            "**Real-world** — live stacks: Qiskit Aer, IBM token, AeroQ OSSLBM, "
            "classical optimizers on real customer test data."
        ),
    )
    mode: ExecutionMode = MODE_MOCK if choice.startswith("Mock") else MODE_REAL
    st.session_state["execution_mode"] = mode
    if mode == MODE_MOCK:
        box.caption("💡 Keynotes & sales: stay on Mock unless you need live Aer/IBM.")
    else:
        box.caption("💡 Needs deps: `qiskit-aer`, optional IBM token, `AeroQ/.venv` for OSSLBM.")
    return mode


def cloud_backend_options(mode: ExecutionMode | None = None) -> tuple[str, ...]:
    m = mode or get_execution_mode()
    if m == MODE_MOCK:
        return (CLOUD_OFF, *CLOUD_MOCK_OPTIONS)
    return (CLOUD_OFF, *CLOUD_REAL_OPTIONS)


def cloud_backend_selectbox(
    *,
    key: str = "cloud_backend_select",
    label: str = "Submit circuit after twin",
    help: str | None = None,
) -> str:
    mode = get_execution_mode()
    opts = list(cloud_backend_options(mode))
    default_help = (
        "After the Rust twin runs, optionally map the pulse to a **gate circuit** and submit. "
        "**Off** = twin only. Mock mode → vendor stubs; Real → Aer or IBM."
    )
    return st.selectbox(
        label,
        options=opts,
        format_func=lambda x: CLOUD_LABELS.get(x, x),
        key=key,
        help=help or default_help,
    )


def mode_banner(mode: ExecutionMode | None = None) -> None:
    m = mode or get_execution_mode()
    if m == MODE_MOCK:
        st.info("**Mode: Mock** — sandbox backends (no production hardware).")
    else:
        st.info("**Mode: Real-world** — uses installed SDKs/tokens where applicable.")


# Materials & Logistics — sales-facing solver labels (do not conflate mock vs classical)
LOGISTICS_SOLVER_MOCK = "Demo: Quantum narrative (mock)"
LOGISTICS_SOLVER_REAL_ORTOOLS = "Solver: Classical (OR-Tools)"
LOGISTICS_SOLVER_REAL_FALLBACK = "Solver: Classical (greedy VRP)"
MATERIALS_SOLVER_MOCK = "Demo: Quantum narrative (mock)"
MATERIALS_SOLVER_REAL = "Solver: Classical (SPSA / local Aer)"


def logistics_solver_label(*, real: bool, solver_id: str | None = None) -> str:
    if not real:
        return LOGISTICS_SOLVER_MOCK
    if solver_id == "ortools_vrp":
        return LOGISTICS_SOLVER_REAL_ORTOOLS
    return LOGISTICS_SOLVER_REAL_FALLBACK


def materials_solver_label(*, real: bool) -> str:
    return MATERIALS_SOLVER_REAL if real else MATERIALS_SOLVER_MOCK


def domain_solver_banner() -> None:
    """Main-panel mirror of sidebar solver labels."""
    mode = get_execution_mode()
    if mode == MODE_MOCK:
        st.caption(
            f"Logistics · {LOGISTICS_SOLVER_MOCK} · "
            f"Materials · {MATERIALS_SOLVER_MOCK}"
        )
    else:
        try:
            from routing.ortools_vrp import ORTOOLS_AVAILABLE
        except ImportError:
            ORTOOLS_AVAILABLE = False
        log_label = (
            LOGISTICS_SOLVER_REAL_ORTOOLS
            if ORTOOLS_AVAILABLE
            else f"{LOGISTICS_SOLVER_REAL_FALLBACK} (pip install ortools)"
        )
        st.caption(f"Logistics · {log_label} · Materials · {MATERIALS_SOLVER_REAL}")


def render_materials_logistics_solver_sidebar(*, use_container: bool = False) -> None:
    """Backward-compatible alias; implementation is in ``app.lab_sidebar``."""
    import lab_sidebar

    lab_sidebar.render_materials_logistics_solver_sidebar(use_container=use_container)


def require_mock_mode(*, real_message: str) -> bool:
    """Return True when mode is mock; otherwise show warning and return False."""
    if get_execution_mode() == MODE_MOCK:
        return True
    st.warning(real_message)
    return False
