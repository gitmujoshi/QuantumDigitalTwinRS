"""
TwinSentry Lab — Streamlit UI for quantum engineers (digital twin R&D).

Run from repository root:
  pip install streamlit plotly numpy  # plus: maturin develop --features python
  streamlit run app/twin_lab.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Repo root: app/twin_lab.py -> parent.parent
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(_ROOT / "python"))

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from twin_sentry.controller import run_twin_pipeline
from twin_sentry.quantum_viz import (
    bloch_purity,
    bloch_vector,
    partial_trace_qubit0,
    partial_trace_qubit1,
    state_vector_from_tuples,
)

# --- Presets (natural-language intents for BAML / heuristics) ---
PRESETS: dict[str, str] = {
    "Hadamard": (
        "Apply a Hadamard-style superposition pulse on qubit 0 with moderate amplitude "
        "and 5 GHz drive, duration 80 nanoseconds, ideal (no noise)."
    ),
    "Pi pulse": (
        "Apply a pi pulse on qubit 0 for a bit-flip style rotation, amplitude about 0.45, "
        "5 GHz, 80 ns duration."
    ),
    "Noise stress test": (
        "Stress test with elevated digital-twin noise: T2 dephasing relative 0.08 and "
        "thermal jitter relative 0.07, amplitude 0.3, 5 GHz."
    ),
    "Safety violation (demo)": (
        "Unsafe operating point: request amplitude 1.5 on the drive (policy stress test)."
    ),
}


def _bloch_sphere_mesh(n_u: int = 28, n_v: int = 14) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    u = np.linspace(0, 2 * np.pi, n_u)
    v = np.linspace(0, np.pi, n_v)
    xs = np.outer(np.cos(u), np.sin(v))
    ys = np.outer(np.sin(u), np.sin(v))
    zs = np.outer(np.ones_like(u), np.cos(v))
    return xs, ys, zs


def _bloch_figure(
    bx0: float,
    by0: float,
    bz0: float,
    bx1: float,
    by1: float,
    bz1: float,
) -> go.Figure:
    xs, ys, zs = _bloch_sphere_mesh()
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "scatter3d"}, {"type": "scatter3d"}]],
        subplot_titles=("Qubit 0 (reduced ρ)", "Qubit 1 (reduced ρ)"),
    )
    for col, (bx, by, bz) in enumerate([(bx0, by0, bz0), (bx1, by1, bz1)], start=1):
        fig.add_trace(
            go.Surface(
                x=xs,
                y=ys,
                z=zs,
                opacity=0.22,
                showscale=False,
                colorscale="Tealrose",
                hoverinfo="skip",
            ),
            row=1,
            col=col,
        )
        r = float(np.sqrt(bx * bx + by * by + bz * bz))
        if r < 1e-12:
            fig.add_trace(
                go.Scatter3d(
                    x=[0],
                    y=[0],
                    z=[0],
                    mode="markers",
                    marker=dict(size=8, color="#ff6b6b"),
                    showlegend=False,
                ),
                row=1,
                col=col,
            )
        else:
            fig.add_trace(
                go.Scatter3d(
                    x=[0, bx],
                    y=[0, by],
                    z=[0, bz],
                    mode="lines+markers",
                    line=dict(color="#ffd93d", width=10),
                    marker=dict(size=[2, 12], color=["#666", "#ff6b6b"]),
                    showlegend=False,
                ),
                row=1,
                col=col,
            )
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=48, b=0),
        paper_bgcolor="#0e1117",
        font=dict(color="#eaeaea"),
        scene=dict(
            xaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            yaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            zaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            aspectmode="cube",
        ),
        scene2=dict(
            xaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            yaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            zaxis=dict(range=[-1.15, 1.15], showbackground=False, gridcolor="#2a2a3a"),
            aspectmode="cube",
        ),
    )
    return fig


def main() -> None:
    st.set_page_config(
        page_title="TwinSentry Lab",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp { background-color: #0e1117; }
        h1 { color: #7ee0c5; letter-spacing: -0.02em; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("TwinSentry Lab")
    st.caption(
        "R&D console for the **digital twin**: BAML policy, Rust TDSE simulation, "
        "Bloch-sphere views of reduced states, Langfuse-friendly audit."
    )

    if "intent_box" not in st.session_state:
        st.session_state.intent_box = PRESETS["Hadamard"]

    with st.sidebar:
        st.header("Simulation")
        n_steps = st.slider("RK4 steps", min_value=16, max_value=2048, value=256, step=16)
        dt_exp = st.slider("log₁₀(dt / s)", min_value=-14.0, max_value=-9.0, value=-11.5, step=0.5)
        dt = float(10**dt_exp)
        st.caption(f"dt = {dt:.3e} s")

        st.divider()
        st.header("Quick presets")
        for name in PRESETS:
            if st.button(name, use_container_width=True, key=f"preset_{name}"):
                st.session_state.intent_box = PRESETS[name]
                st.rerun()

        st.divider()
        st.subheader("Environment")
        st.caption("`GOOGLE_API_KEY` → BAML/Gemini · `LANGFUSE_*` → traces")
        lf_host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
        st.code(lf_host, language=None)

    col_a, col_b = st.columns((1.1, 0.9))
    with col_a:
        intent = st.text_area(
            "Command (natural language)",
            key="intent_box",
            height=170,
            placeholder="Describe pulse intent or use presets…",
        )
    with col_b:
        st.subheader("Run pipeline")
        run = st.button("▶ Run digital twin", type="primary", use_container_width=True)

    if run and intent.strip():
        with st.spinner("BAML → Rust twin…"):
            try:
                result = run_twin_pipeline(intent.strip(), n_steps=n_steps, dt=dt)
                st.session_state["last_result"] = result
            except Exception as e:
                st.error(f"Pipeline failed: {e}")
                st.session_state["last_result"] = None

    result = st.session_state.get("last_result")
    if result:
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Fidelity |⟨00|ψ⟩|²", f"{result.get('fidelity', float('nan')):.6f}")
        pc = result.get("pulse_command") or {}
        m2.metric("Amplitude", f"{pc.get('amplitude', float('nan')):.4f}")
        m3.metric("f_drive (Hz)", f"{pc.get('frequency_hz', 0):.3e}")
        m4.metric("Final t (s)", f"{result.get('final_time', 0):.3e}")

        st.subheader("Reduced-state Bloch spheres")
        state = result.get("state") or []
        if len(state) == 4:
            psi = state_vector_from_tuples(state)
            rho0 = partial_trace_qubit0(psi)
            rho1 = partial_trace_qubit1(psi)
            x0, y0, z0 = bloch_vector(rho0)
            x1, y1, z1 = bloch_vector(rho1)
            p0 = bloch_purity(rho0)
            p1 = bloch_purity(rho1)
            c1, c2 = st.columns(2)
            c1.caption(f"Qubit 0 — purity Tr(ρ²) = {p0:.5f}")
            c2.caption(f"Qubit 1 — purity Tr(ρ²) = {p1:.5f}")
            fig = _bloch_figure(x0, y0, z0, x1, y1, z1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("State vector length is not 4; cannot plot Bloch spheres.")

        tab_a, tab_b, tab_c = st.tabs(["Pulse & policy", "Audit & traces", "Raw JSON"])
        with tab_a:
            st.json(
                {
                    "pulse_command": pc,
                    "noise_metadata": result.get("noise"),
                    "baml_error": result.get("baml_error"),
                }
            )
            if result.get("baml_error"):
                st.info("LLM/BAML path reported an issue; heuristic or fallback may be in use.")
        with tab_b:
            tid = result.get("trace_id")
            st.write("**Trace ID:**", tid or "(none — add Langfuse keys to env)")
            host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000").rstrip("/")
            st.markdown(f"[Langfuse UI]({host})")
        with tab_c:
            st.code(json.dumps(result, indent=2), language="json")

    st.divider()
    st.caption(
        "TwinSentry-RS · Rust core is network-isolated; pulses arrive via the control plane only."
    )


if __name__ == "__main__":
    main()
