"""MatrixQ-aligned simulation contract (no native extension required)."""

from __future__ import annotations

import pytest

pytest.importorskip("numpy")

from twin_sentry.simulation_contract import (  # noqa: E402
    bloch_vectors_from_state,
    build_simulation_payload,
)


def test_bloch_vectors_two_qubit_ground() -> None:
    # |00>
    state = [(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
    vecs = bloch_vectors_from_state(state)
    assert len(vecs) == 2
    assert vecs[0]["z"] == pytest.approx(1.0, abs=0.01)
    assert vecs[1]["z"] == pytest.approx(1.0, abs=0.01)


def test_build_payload_with_cloud_counts() -> None:
    payload = build_simulation_payload(
        fidelity=0.9,
        state=[(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)],
        cloud={"ok": True, "backend": "local_aer", "counts": {"00": 900, "11": 124}},
        shots=1024,
        gate_type="HADAMARD",
    )
    assert payload["success"] is True
    assert payload["counts"]["00"] == 900
    assert len(payload["bloch_vectors"]) == 2
    assert payload["quantum_metadata"]["allocated_qubits"] >= 1


def test_synthetic_counts_when_no_cloud() -> None:
    payload = build_simulation_payload(fidelity=1.0, shots=100)
    assert sum(payload["counts"].values()) == 100
