"""
Projects Lab — Streamlit UI to exercise sandbox projects.

Run from repository root:
  pip install streamlit numpy pyyaml
  streamlit run app/projects_lab.py
"""

from __future__ import annotations

import json
import sys
import traceback
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import streamlit as st

# Repo root: app/projects_lab.py -> parent.parent
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Make AeroQ importable without installing it into this env.
_AEROQ_SRC = _ROOT / "AeroQ" / "src"
if _AEROQ_SRC.exists() and str(_AEROQ_SRC) not in sys.path:
    sys.path.insert(0, str(_AEROQ_SRC))

# Make PQC readiness demo importable without installing it.
_PYTHON_DIR = _ROOT / "python"
if _PYTHON_DIR.exists() and str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

from portfolio_mode import (  # noqa: E402
    MODE_MOCK,
    MODE_REAL,
    cloud_backend_selectbox,
    get_execution_mode,
    require_mock_mode,
    mode_banner,
    WEATHER_MOCK_BACKENDS,
    WEATHER_REAL_BACKENDS,
)

_APP_SIDEBAR = _ROOT / "app"
if str(_APP_SIDEBAR) not in sys.path:
    sys.path.insert(0, str(_APP_SIDEBAR))
from lab_sidebar import (  # noqa: E402
    render_execution_mode_block,
    render_materials_logistics_solver_sidebar,
    render_navigation_guide,
    render_project_picker,
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except Exception as e:
        return f"Could not read `{path}`: {e}"


def _parse_json_array(name: str, text: str) -> np.ndarray:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{name} must be valid JSON (e.g. [[1,0],[0,1]]). Error: {e}") from e
    return np.asarray(obj, dtype=float)


def _aeroq_panel() -> None:
    st.subheader("AeroQ — Use cases")
    mode_banner()

    try:
        from aeroq import AeroQKernel  # type: ignore
    except Exception:
        st.error(
            "Could not import AeroQ. Expected `AeroQ/src` to exist. "
            "If you moved it, update the path logic in `app/projects_lab.py`."
        )
        st.code(traceback.format_exc())
        return

    cfg_path = _ROOT / "AeroQ" / "config.yaml"

    mode = get_execution_mode()
    tab_labels = ["Linear solve (kernel)", "OSSLBM (one-step LBM circuit)"]
    if mode == MODE_MOCK:
        tab_labels.append("Regional forecast (mock NWP)")
    tabs = st.tabs(tab_labels)
    tab1, tab2 = tabs[0], tabs[1]

    with tab1:
        colA, colB = st.columns([1, 1])
        with colA:
            backend = st.selectbox("Backend", ["pennylane_amd", "qiskit_ibm"], index=0)
        with colB:
            use_repo_config = st.checkbox("Use `AeroQ/config.yaml`", value=True)

        default_A = [[3.0, 1.0], [1.0, 2.0]]
        default_b = [9.0, 8.0]

        A_text = st.text_area("Matrix A (JSON)", value=json.dumps(default_A), key="aeroq_A")
        b_text = st.text_area("Vector/Matrix b (JSON)", value=json.dumps(default_b), key="aeroq_b")

        if st.button("Solve Ax=b", type="primary", key="aeroq_solve"):
            try:
                A = _parse_json_array("A", A_text)
                b = _parse_json_array("b", b_text)
                if b.ndim == 1:
                    b = b.reshape((-1,))
            except Exception as e:
                st.error(str(e))
                return

            try:
                if use_repo_config and cfg_path.exists():
                    k = AeroQKernel(config_path=cfg_path)
                    try:
                        object.__setattr__(k.cfg, "backend", backend)
                    except Exception:
                        pass
                else:
                    tmp_cfg = _ROOT / ".aeroq_tmp_config.yaml"
                    tmp_cfg.write_text(
                        "\n".join(
                            [
                                f"backend: {backend}",
                                "pennylane_amd: {}",
                                "qiskit_ibm: {}",
                                "",
                            ]
                        )
                    )
                    k = AeroQKernel(config_path=tmp_cfg)

                x = k.solve_linear_system(A, b)
                resid = A @ x - b
                st.success(f"Solved using backend route: `{backend}`")
                st.write("x:")
                st.code(np.array2string(x, precision=6, floatmode="fixed"))
                st.write("Residual ‖Ax-b‖₂:")
                st.code(f"{float(np.linalg.norm(resid)):.6e}")
            except Exception:
                st.error("Solve failed.")
                st.code(traceback.format_exc())

    with tab2:
        if mode == MODE_MOCK:
            st.caption(
                "Switch **Execution mode** to **Real-world** to run OSSLBM with PennyLane in `AeroQ/.venv`, "
                "or use Linear solve / Regional forecast mocks in Mock mode."
            )
        else:
            st.caption(
                "One-step simplified LBM circuit (PennyLane in `AeroQ/.venv`). "
                "D2Q9 embedded via nv=16 padding."
            )

        nx = st.selectbox("Grid nx", [2, 4], index=0, key="osslbm_nx")
        ny = st.selectbox("Grid ny", [2, 4], index=0, key="osslbm_ny")
        velocity_set = st.selectbox("Velocity set", ["D2Q4", "D2Q9"], index=1, key="osslbm_vs")
        nv = 4 if velocity_set == "D2Q4" else 16
        theta = st.slider("Collision θ", min_value=0.0, max_value=1.2, value=0.35, step=0.05, key="osslbm_theta")
        st.info("Streaming is now implemented as a **gate-level structured permutation network** (controlled modular shifts).")

        if mode == MODE_MOCK:
            st.warning("OSSLBM is disabled in **Mock** mode. Select **Real-world** in the sidebar.")
        elif st.button("Run one-step OSSLBM", type="primary", key="osslbm_run"):
            aeroq_py = _ROOT / "AeroQ" / ".venv" / "bin" / "python"
            if not aeroq_py.exists():
                st.error("Missing `AeroQ/.venv`. Create it and install deps in `AeroQ/` first.")
                return

            code = (
                "import json, numpy as np\n"
                "from aeroq.osslbm import OsslBmSpec, build_osslbm_one_step_qnode\n"
                f"nx={int(nx)}; ny={int(ny)}; nv={int(nv)}\n"
                "f0=np.zeros((ny,nx,nv), dtype=float)\n"
                + ("f0[0,0,0]=1.0\n" if velocity_set == "D2Q4" else "f0[0,0,1]=1.0\n")
                + f"spec=OsslBmSpec(nx=nx, ny=ny, nv=nv, velocity_set='{velocity_set}', collision_theta={float(theta)}, device='lightning.gpu')\n"
                "qnode=build_osslbm_one_step_qnode(spec=spec, f0=f0, jit=True)\n"
                "out=qnode()\n"
                "probs=(np.abs(out)**2).tolist()\n"
                "print(json.dumps({'nx':nx,'ny':ny,'nv':nv,'velocity_set':spec.velocity_set,'probs':probs}))\n"
            )

            try:
                proc = subprocess.run(
                    [str(aeroq_py), "-c", code],
                    capture_output=True,
                    text=True,
                    cwd=str(_ROOT / "AeroQ"),
                    timeout=180,
                    check=True,
                )
                payload = json.loads(proc.stdout.strip() or "{}")
                st.success("OSSLBM step completed.")
                st.json({k: payload[k] for k in payload if k != "probs"})
                probs = np.asarray(payload.get("probs", []), dtype=float)
                if probs.size:
                    st.write("Top basis-state probabilities:")
                    topk = np.argsort(-probs)[: min(12, probs.size)]
                    st.code("\n".join([f"{int(i)}: {probs[int(i)]:.6f}" for i in topk]))
            except subprocess.CalledProcessError as e:
                st.error("OSSLBM run failed.")
                st.code(e.stdout)
                st.code(e.stderr)
            except Exception:
                st.error("OSSLBM run failed.")
                st.code(traceback.format_exc())

    if mode == MODE_MOCK:
        with tabs[2]:
            _weather_mock_tab()


def _weather_mock_tab() -> None:
    st.caption(
        "Toy regional weather workflow: grid → backend routing (classical / QSVT / QPU stub) → "
        "synthetic forecast metrics. Not a real NWP model."
    )
    try:
        from domain_mocks.weather import WeatherRunRequest, run_regional_forecast_mock
    except Exception:
        st.error("Could not import `python/domain_mocks`.")
        st.code(traceback.format_exc())
        return

    region = st.text_input("Region id", value="us-east-conus", key="wx_region")
    horizon = st.slider("Horizon (hours)", 6, 72, 24, key="wx_horizon")
    backend = st.selectbox(
        "Acceleration backend",
        list(WEATHER_MOCK_BACKENDS),
        key="wx_backend",
    )
    c1, c2 = st.columns(2)
    with c1:
        nx = st.selectbox("Grid nx", [16, 32, 64], index=1, key="wx_nx")
    with c2:
        ny = st.selectbox("Grid ny", [16, 32, 64], index=1, key="wx_ny")

    if st.button("Run regional forecast (mock)", type="primary", key="wx_run"):
        req = WeatherRunRequest(
            region=region,
            horizon_hours=int(horizon),
            grid_nx=int(nx),
            grid_ny=int(ny),
            backend=backend,  # type: ignore[arg-type]
        )
        st.json(run_regional_forecast_mock(req))


def _drug_discovery_panel() -> None:
    st.subheader("Drug discovery — Pipeline mock")
    mode_banner()
    if not require_mock_mode(
        real_message=(
            "**Real-world** drug pipelines (OpenMM, PySCF, cloud chemistry) are not bundled. "
            "Switch sidebar to **Mock (sandbox)** for the staged demo."
        ),
    ):
        return

    st.caption(
        "Classical docking → optional VQE chemistry stub → ML surrogate. "
        "Replace stubs with OpenMM / PySCF / real QPUs for production."
    )
    try:
        from domain_mocks.drug_discovery import DrugPipelineRequest, run_drug_pipeline_mock
    except Exception:
        st.error("Could not import `python/domain_mocks`.")
        st.code(traceback.format_exc())
        return

    mol = st.text_input("Molecule id", value="cmpd-2026-0142", key="drug_mol")
    target = st.text_input("Target protein", value="Kinase-X", key="drug_target")
    backend = st.selectbox(
        "Pipeline backend",
        ["hybrid_vqe", "classical_only", "surrogate_ml"],
        key="drug_backend",
    )

    if st.button("Run discovery pipeline (mock)", type="primary", key="drug_run"):
        req = DrugPipelineRequest(
            molecule_id=mol,
            target_protein=target,
            backend=backend,  # type: ignore[arg-type]
        )
        out = run_drug_pipeline_mock(req)
        if out.get("lead_candidate"):
            st.success("Mock lead candidate (passes toy thresholds).")
        else:
            st.warning("Mock result: does not pass toy lead thresholds.")
        st.json(out)


def _twinsentry_panel() -> None:
    st.subheader("TwinSentry — Digital twin (intent → policy → simulation)")
    mode_banner()
    st.caption(
        "Runs the TwinSentry control plane. For full visualization, use `streamlit run app/twin_lab.py`."
    )

    try:
        from twin_sentry.controller import run_twin_pipeline  # type: ignore
        from twin_sentry.sample_prompts import SAMPLE_PROMPTS, SIDEBAR_PRESETS  # type: ignore
    except Exception:
        st.error(
            "Could not import TwinSentry modules. If the native extension isn't built yet, run:\n"
            "`pip install maturin && maturin develop --features python`"
        )
        st.code(traceback.format_exc())
        return

    preset_names = list(SIDEBAR_PRESETS.keys())
    preset_name = st.selectbox("Preset", ["(custom)"] + preset_names, index=0)

    if preset_name != "(custom)":
        default_intent = str(SIDEBAR_PRESETS[preset_name])
    else:
        default_intent = str(SAMPLE_PROMPTS[0]) if SAMPLE_PROMPTS else "Apply a safe Hadamard-like pulse."

    intent = st.text_area("User intent", value=default_intent, height=120)

    col1, col2, col3 = st.columns(3)
    with col1:
        n_steps = st.slider("RK4 steps", min_value=16, max_value=512, value=128, step=16)
    with col2:
        dt = st.number_input("dt (seconds)", value=2e-12, format="%.2e")
    with col3:
        cb = cloud_backend_selectbox(key="projects_cloud_backend")
    cloud_backend = None if cb == "off" else cb

    cloud_shots = st.slider("Cloud shots", min_value=128, max_value=8192, value=1024, step=128)

    if st.button("Run TwinSentry pipeline", type="primary"):
        try:
            out = run_twin_pipeline(
                intent,
                n_steps=int(n_steps),
                dt=float(dt),
                cloud_backend=cloud_backend,
                cloud_shots=int(cloud_shots),
            )
            fid = out.get("fidelity", None)
            if fid is not None:
                st.success(f"Run complete. Fidelity proxy: **{float(fid):.6f}**")
            else:
                st.success("Run complete.")
            sp = out.get("simulation_payload")
            if sp:
                with st.expander("Simulation contract (MatrixQ-aligned)", expanded=False):
                    st.json(sp)
            st.json(out)
        except Exception:
            st.error("TwinSentry run failed.")
            st.code(traceback.format_exc())


def _materials_logistics_panel() -> None:
    _APP_DIR = _ROOT / "app"
    if str(_APP_DIR) not in sys.path:
        sys.path.insert(0, str(_APP_DIR))
    from materials_logistics_ui import render_materials_logistics_panel

    render_materials_logistics_panel()


def _pqc_panel() -> None:
    st.subheader("Post-Quantum Crypto — Readiness sandbox")

    prd_path = _ROOT / "docs" / "prd" / "Post-Quantum-Crypto-Project-PRD.md"
    st.markdown("#### PRD")
    st.markdown(_read_text(prd_path))

    st.markdown("---")
    st.markdown("#### Toy impact calculator (education)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Grover (symmetric search) rough rule-of-thumb**")
        key_bits = st.slider("Symmetric key size (bits)", min_value=64, max_value=512, value=256, step=32)
        effective = key_bits / 2.0
        st.write(f"Approx. effective security under Grover: **~{effective:.0f} bits**")
        st.caption("This is a coarse heuristic; real security depends on construction and attack model.")

    with col2:
        st.markdown("**Shor (public-key break)**")
        st.write("- RSA / ECC are not considered post-quantum safe under Shor on a large fault-tolerant QPU.")
        st.write("- PQC migration prioritizes long-lived secrets (harvest-now, decrypt-later).")

    st.markdown("---")
    st.markdown("#### Interactive demos (engineering)")

    try:
        from pqc_readiness.demo import kem_demo, signature_demo  # type: ignore
    except Exception:
        st.error("Could not import `python/pqc_readiness`. Verify it exists in this repo.")
        st.code(traceback.format_exc())
        return

    tab_kem, tab_sig, tab_agility = st.tabs(["KEM / handshake", "Signatures", "Crypto-agility"])

    with tab_kem:
        mode = st.selectbox("Mode", ["hybrid", "classical", "pqc_stub"], index=0)
        st.caption(
            "Hybrid demo combines a classical shared secret (X25519) with a PQC placeholder KEM. "
            "Replace the stub with ML-KEM once a PQC library is added."
        )
        if st.button("Run KEM demo"):
            res = kem_demo(mode=mode)  # type: ignore[arg-type]
            if res.ok:
                st.success("Handshake successful (client/server derived the same key material).")
            else:
                st.error("Handshake failed.")
            st.json(res.details)

    with tab_sig:
        mode = st.selectbox("Signature mode", ["hybrid", "classical", "pqc_stub"], index=0)
        msg = st.text_input("Message to sign", value="hello, pqc")
        if st.button("Run signature demo"):
            res = signature_demo(mode=mode, message=msg)  # type: ignore[arg-type]
            if res.ok:
                st.success("Signature verification succeeded.")
            else:
                st.error("Signature verification failed.")
            st.json(res.details)

    with tab_agility:
        st.markdown("**Config-driven algorithm selection (demo)**")
        st.caption(
            "This shows the core readiness idea: protocols should be able to switch algorithms by config, "
            "support hybrid periods, and record what was used."
        )
        alg = st.selectbox("Handshake policy", ["classical-only", "hybrid-preferred", "pqc-only (future)"], index=1)
        st.code(
            "\n".join(
                [
                    "policy:",
                    f"  handshake: {alg}",
                    "  classical_kem: x25519",
                    "  pqc_kem: ml-kem-768   # (future; demo uses stub today)",
                    "  classical_sig: ed25519",
                    "  pqc_sig: ml-dsa-65    # (future; demo uses stub today)",
                    "  record_transcripts: true",
                ]
            )
        )


def _prd_panel() -> None:
    st.subheader("PRDs")
    consolidated = _ROOT / "docs" / "prd" / "Portfolio-Consolidated-PRD.md"
    aeroq_prd = _ROOT / "docs" / "prd" / "AeroQ-Consolidated-PRD-v3.0.md"
    pqc_prd = _ROOT / "docs" / "prd" / "Post-Quantum-Crypto-Project-PRD.md"
    twinsentry_prd = _ROOT / "docs" / "prd" / "TwinSentry-Digital-Twin-PRD.md"
    matrixq_prd = _ROOT / "docs" / "prd" / "MatrixQ-Sandbox-Platform-PRD.md"
    matrixq_cmp = _ROOT / "docs" / "prd" / "MatrixQ-vs-Portfolio-Comparison.md"
    matrixq_design = _ROOT / "docs" / "DESIGN_DOC_Master.md"

    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Portfolio (canonical)",
            "TwinSentry",
            "AeroQ",
            "PQC",
            "MatrixQ PRD",
            "MatrixQ design",
            "MatrixQ comparison",
        ]
    )
    with tab0:
        st.markdown(_read_text(consolidated))
    with tab1:
        st.markdown(_read_text(twinsentry_prd))
    with tab2:
        st.markdown(_read_text(aeroq_prd))
    with tab3:
        st.markdown(_read_text(pqc_prd))
    with tab4:
        st.markdown(_read_text(matrixq_prd))
    with tab5:
        st.markdown(_read_text(matrixq_design))
    with tab6:
        st.markdown(_read_text(matrixq_cmp))


def main() -> None:
    st.set_page_config(page_title="Projects Lab", layout="wide")
    st.title("Projects Lab")
    st.caption(
        "Portfolio: TwinSentry, AeroQ, Materials & Logistics (mock/real), drug mock, PQC, PRDs."
    )

    with st.sidebar:
        render_navigation_guide(current="projects")
        st.divider()
        render_execution_mode_block()
        st.divider()
        project = render_project_picker()
        if project == "Materials & Logistics":
            st.divider()
            render_materials_logistics_solver_sidebar(use_container=True)

    if project == "TwinSentry":
        _twinsentry_panel()
    elif project == "AeroQ":
        _aeroq_panel()
    elif project == "Materials & Logistics":
        _materials_logistics_panel()
    elif project == "Drug discovery (mock)":
        _drug_discovery_panel()
    elif project == "Post-Quantum Crypto":
        _pqc_panel()
    else:
        _prd_panel()


if __name__ == "__main__":
    main()

