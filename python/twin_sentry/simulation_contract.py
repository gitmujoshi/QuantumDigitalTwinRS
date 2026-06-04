"""
MatrixQ-aligned simulation JSON contract (portfolio PRD §2.2).

Used by TwinSentry pipeline results and domain mocks for consistent UI / API consumers.
"""

from __future__ import annotations

import time
from typing import Any

from twin_sentry.quantum_viz import (
    bloch_vector,
    partial_trace_qubit0,
    partial_trace_qubit1,
    state_vector_from_tuples,
)


def _normalize_counts(raw: dict[str, Any] | None) -> dict[str, int]:
    if not raw:
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        key = str(k).replace(" ", "")
        out[key] = int(v)
    return out


def bloch_vectors_from_state(state: list[Any]) -> list[dict[str, float | int]]:
    """Build per-qubit Bloch vectors from a 4-amplitude state (2-qubit)."""
    if len(state) != 4:
        return []
    psi = state_vector_from_tuples(state)
    vectors: list[dict[str, float | int]] = []
    for qubit, rho_fn in enumerate([partial_trace_qubit0, partial_trace_qubit1]):
        x, y, z = bloch_vector(rho_fn(psi))
        vectors.append({"qubit": qubit, "x": round(float(x), 4), "y": round(float(y), 4), "z": round(float(z), 4)})
    return vectors


def _synthetic_counts_from_fidelity(fid: float, shots: int = 8192) -> dict[str, int]:
    """Demo histogram when cloud counts are absent."""
    p00 = max(0.0, min(1.0, float(fid)))
    n00 = int(round(shots * p00))
    n11 = shots - n00
    if n00 >= shots:
        return {"00": shots}
    if n11 >= shots:
        return {"11": shots}
    return {"00": n00, "11": n11}


def build_simulation_payload(
    *,
    success: bool = True,
    fidelity: float | None = None,
    state: list[Any] | None = None,
    cloud: dict[str, Any] | None = None,
    shots: int = 8192,
    gate_type: str | None = None,
    business_telemetry: dict[str, Any] | None = None,
    duration_ms: float | None = None,
) -> dict[str, Any]:
    """
    Standard envelope for quantum simulation results (MatrixQ design §5 + portfolio PRD).
    """
    counts = _normalize_counts(cloud.get("counts") if cloud and cloud.get("ok") else None)
    if not counts and fidelity is not None:
        counts = _synthetic_counts_from_fidelity(fidelity, shots=shots)

    n_qubits = 2 if gate_type == "CNOT" or (counts and max(len(k) for k in counts) >= 2) else 1
    if counts:
        max_len = max(len(k) for k in counts)
        n_qubits = max(n_qubits, max_len)

    bloch = bloch_vectors_from_state(state or [])
    depth = 4 if gate_type == "CNOT" else 3
    if gate_type in ("HADAMARD", "X", "Y", "Z"):
        depth = 2

    meta: dict[str, Any] = {
        "allocated_qubits": n_qubits,
        "optimized_gate_depth": depth,
        "execution_duration_ms": round(duration_ms if duration_ms is not None else 0.0, 2),
        "gate_type": gate_type,
        "backend": cloud.get("backend") if cloud else "rust_twin",
    }
    if cloud and cloud.get("backend_name"):
        meta["backend_name"] = cloud["backend_name"]
    if cloud and cloud.get("job_id"):
        meta["job_id"] = cloud["job_id"]

    payload: dict[str, Any] = {
        "success": success,
        "counts": counts,
        "quantum_metadata": meta,
        "bloch_vectors": bloch,
    }
    if business_telemetry:
        payload["business_telemetry"] = business_telemetry
    return payload
