from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import yaml


BackendName = Literal["pennylane_amd", "qiskit_ibm"]


@dataclass(frozen=True)
class KernelConfig:
    backend: BackendName
    pennylane_amd: dict[str, Any]
    qiskit_ibm: dict[str, Any]


def _load_config(path: str | Path) -> KernelConfig:
    p = Path(path)
    data = yaml.safe_load(p.read_text()) or {}

    backend = data.get("backend", "pennylane_amd")
    if backend not in ("pennylane_amd", "qiskit_ibm"):
        raise ValueError(f"Unsupported backend {backend!r}. Expected 'pennylane_amd' or 'qiskit_ibm'.")

    return KernelConfig(
        backend=backend,
        pennylane_amd=dict(data.get("pennylane_amd") or {}),
        qiskit_ibm=dict(data.get("qiskit_ibm") or {}),
    )


class AeroQKernel:
    """
    Hardware-agnostic kernel router.

    MVP note:
    - `solve_linear_system(A, b)` currently performs a classical solve by default.
    - The backend routing and dependency wiring is the foundation for plugging in
      QSVT (PennyLane/Catalyst) and IBM Runtime primitives (Qiskit).
    """

    def __init__(self, config_path: str | Path = "config.yaml") -> None:
        self.config_path = Path(config_path)
        self.cfg = _load_config(self.config_path)

    @property
    def backend(self) -> BackendName:
        return self.cfg.backend

    def solve_linear_system(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Solve Ax=b using the configured backend route.

        Parameters
        - A: square matrix
        - b: vector or matrix of RHS
        """
        A = np.asarray(A, dtype=float)
        b = np.asarray(b, dtype=float)

        if A.ndim != 2 or A.shape[0] != A.shape[1]:
            raise ValueError(f"A must be a square 2D array; got shape {A.shape}.")
        if b.ndim not in (1, 2) or b.shape[0] != A.shape[0]:
            raise ValueError(f"b must have shape ({A.shape[0]},) or ({A.shape[0]}, k); got {b.shape}.")

        if self.backend == "pennylane_amd":
            return self._solve_linear_system_pennylane_amd(A, b)
        if self.backend == "qiskit_ibm":
            return self._solve_linear_system_qiskit_ibm(A, b)
        raise AssertionError(f"Unhandled backend {self.backend!r}.")

    def _solve_linear_system_pennylane_amd(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        PennyLane route.

        Intended future: QSVT block-encoding + polynomial transform with catalyst.jit.
        Current MVP: classical solve; validates PennyLane device availability if installed.
        """
        try:
            import pennylane as qml  # type: ignore
        except Exception:
            # Keep the MVP runnable without quantum deps.
            return np.linalg.solve(A, b)

        device_name = str(self.cfg.pennylane_amd.get("device") or "lightning.gpu")
        wires = int(self.cfg.pennylane_amd.get("wires") or 8)
        shots = self.cfg.pennylane_amd.get("shots", None)

        # Best-effort device init: if lightning.gpu is unavailable, fall back to default.qubit.
        try:
            _ = qml.device(device_name, wires=wires, shots=shots)
        except Exception:
            _ = qml.device("default.qubit", wires=min(wires, 8), shots=shots)

        return np.linalg.solve(A, b)

    def _solve_linear_system_qiskit_ibm(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Qiskit IBM Runtime route (Primitive V2 era).

        Intended future: construct circuits for linear-system routines and run via Sampler/Estimator V2.
        Current MVP: classical solve; performs a lightweight import check for runtime client.
        """
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService  # type: ignore
        except Exception:
            return np.linalg.solve(A, b)

        # Lazy-create service to validate env without forcing login during unit tests.
        # Users can provide tokens via env or saved account.
        try:
            _ = QiskitRuntimeService(
                instance=self.cfg.qiskit_ibm.get("instance", None),
            )
        except Exception:
            # If account isn't configured, still allow local MVP behavior.
            pass

        return np.linalg.solve(A, b)

