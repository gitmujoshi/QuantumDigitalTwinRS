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

    tab1, tab2 = st.tabs(["Linear solve (kernel)", "OSSLBM (one-step LBM circuit)"])

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
        st.caption(
            "One-step simplified LBM circuit: amplitude-encode f0 → collision unitary → streaming permutation. "
            "D2Q9 is embedded via nv=16 padding. Uses `AeroQ/.venv` so you don't need PennyLane in the root env."
        )

        nx = st.selectbox("Grid nx", [2, 4], index=0, key="osslbm_nx")
        ny = st.selectbox("Grid ny", [2, 4], index=0, key="osslbm_ny")
        velocity_set = st.selectbox("Velocity set", ["D2Q4", "D2Q9"], index=1, key="osslbm_vs")
        nv = 4 if velocity_set == "D2Q4" else 16
        theta = st.slider("Collision θ", min_value=0.0, max_value=1.2, value=0.35, step=0.05, key="osslbm_theta")
        st.info("Streaming is now implemented as a **gate-level structured permutation network** (controlled modular shifts).")

        if st.button("Run one-step OSSLBM", type="primary", key="osslbm_run"):
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


def _twinsentry_panel() -> None:
    st.subheader("TwinSentry — Digital twin (intent → policy → simulation)")
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
        cloud_backend = st.selectbox("Cloud backend (optional)", [None, "local_aer", "ibm_quantum"], index=0)

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
            st.json(out)
        except Exception:
            st.error("TwinSentry run failed.")
            st.code(traceback.format_exc())


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
    aeroq_prd = _ROOT / "docs" / "prd" / "AeroQ-Consolidated-PRD-v3.0.md"
    pqc_prd = _ROOT / "docs" / "prd" / "Post-Quantum-Crypto-Project-PRD.md"
    twinsentry_prd = _ROOT / "docs" / "prd" / "TwinSentry-Digital-Twin-PRD.md"

    tab1, tab2, tab3 = st.tabs(["TwinSentry PRD", "AeroQ PRD", "PQC PRD"])
    with tab1:
        st.markdown(_read_text(twinsentry_prd))
    with tab2:
        st.markdown(_read_text(aeroq_prd))
    with tab3:
        st.markdown(_read_text(pqc_prd))


def main() -> None:
    st.set_page_config(page_title="Projects Lab", layout="wide")
    st.title("Projects Lab")
    st.caption("Lightweight UI to test AeroQ and Post-Quantum Crypto workstreams.")

    project = st.sidebar.radio("Choose a project", ["TwinSentry", "AeroQ", "Post-Quantum Crypto", "PRDs"], index=0)

    if project == "TwinSentry":
        _twinsentry_panel()
    elif project == "AeroQ":
        _aeroq_panel()
    elif project == "Post-Quantum Crypto":
        _pqc_panel()
    else:
        _prd_panel()


if __name__ == "__main__":
    main()

