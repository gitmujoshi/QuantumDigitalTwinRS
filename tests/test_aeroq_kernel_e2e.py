from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def test_aeroq_kernel_solve_linear_system_e2e(tmp_path: Path) -> None:
    """
    E2E-ish check that matches what the UI does:
    - make AeroQ importable from AeroQ/src
    - instantiate AeroQKernel with a config
    - solve a small linear system
    """
    repo_root = Path(__file__).resolve().parents[1]
    aeroq_src = repo_root / "AeroQ" / "src"
    assert aeroq_src.exists()
    sys.path.insert(0, str(aeroq_src))

    from aeroq import AeroQKernel  # type: ignore

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "backend: pennylane_amd",
                "pennylane_amd: {}",
                "qiskit_ibm: {}",
                "",
            ]
        )
    )

    k = AeroQKernel(config_path=cfg)
    A = np.array([[3.0, 1.0], [1.0, 2.0]])
    b = np.array([9.0, 8.0])
    x = k.solve_linear_system(A, b)
    assert np.allclose(A @ x, b)

