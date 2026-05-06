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
    st.subheader("AeroQ — Linear system sandbox")

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
    colA, colB = st.columns([1, 1])
    with colA:
        backend = st.selectbox("Backend", ["pennylane_amd", "qiskit_ibm"], index=0)
    with colB:
        use_repo_config = st.checkbox("Use `AeroQ/config.yaml`", value=True)

    # Default inputs
    default_A = [[3.0, 1.0], [1.0, 2.0]]
    default_b = [9.0, 8.0]

    A_text = st.text_area("Matrix A (JSON)", value=json.dumps(default_A))
    b_text = st.text_area("Vector/Matrix b (JSON)", value=json.dumps(default_b))

    if st.button("Solve Ax=b", type="primary"):
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
                # Override backend for this run (without rewriting config.yaml).
                try:
                    object.__setattr__(k.cfg, "backend", backend)
                except Exception:
                    pass
            else:
                # Create a minimal in-memory config by writing a temporary file.
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


def _prd_panel() -> None:
    st.subheader("PRDs")
    aeroq_prd = _ROOT / "docs" / "prd" / "AeroQ-Consolidated-PRD-v3.0.md"
    pqc_prd = _ROOT / "docs" / "prd" / "Post-Quantum-Crypto-Project-PRD.md"

    tab1, tab2 = st.tabs(["AeroQ PRD", "PQC PRD"])
    with tab1:
        st.markdown(_read_text(aeroq_prd))
    with tab2:
        st.markdown(_read_text(pqc_prd))


def main() -> None:
    st.set_page_config(page_title="Projects Lab", layout="wide")
    st.title("Projects Lab")
    st.caption("Lightweight UI to test AeroQ and Post-Quantum Crypto workstreams.")

    project = st.sidebar.radio("Choose a project", ["AeroQ", "Post-Quantum Crypto", "PRDs"], index=0)

    if project == "AeroQ":
        _aeroq_panel()
    elif project == "Post-Quantum Crypto":
        _pqc_panel()
    else:
        _prd_panel()


if __name__ == "__main__":
    main()

