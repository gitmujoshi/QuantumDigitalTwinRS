"""Optional tests for Qiskit-backed cloud path (skip if extras not installed)."""

from __future__ import annotations

import pytest

pytest.importorskip("qiskit")
pytest.importorskip("qiskit_aer")
pytest.importorskip("twin_sentry._native")

from twin_sentry import PulseCommand  # noqa: E402
from twin_sentry.quantum_cloud import (  # noqa: E402
    pulse_command_to_circuit,
    submit_pulse_cloud,
)


def test_pulse_command_to_circuit_hadamard() -> None:
    cmd = PulseCommand(0.5, 5e9, 80e-9, 5e9, 4.5e9, 10e6)
    qc = pulse_command_to_circuit(cmd, "HADAMARD")
    assert qc.num_qubits == 1


def test_submit_local_aer() -> None:
    cmd = PulseCommand(0.5, 5e9, 80e-9, 5e9, 4.5e9, 10e6)
    out = submit_pulse_cloud(cmd, "HADAMARD", cloud_backend="local_aer", shots=16)
    assert out.get("ok") is True
    assert "counts" in out
