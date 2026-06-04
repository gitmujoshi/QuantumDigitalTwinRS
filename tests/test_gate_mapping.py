"""Gate-type mapping for the analog twin."""

from __future__ import annotations

import pytest

pytest.importorskip("twin_sentry._native")

from twin_sentry import PulseCommand, TwinEngine, pulse_queue
from twin_sentry.controller import run_twin_pipeline
from twin_sentry.gate_mapping import apply_gate_mapping
from twin_sentry.quantum_viz import (
    bloch_vector,
    partial_trace_qubit0,
    state_vector_from_tuples,
)


def test_distinct_gates_change_bloch_vector() -> None:
    base = PulseCommand(
        amplitude=0.5,
        frequency_hz=5e9,
        duration_s=80e-9,
        qubit0_split_hz=5e9,
        qubit1_split_hz=4.5e9,
        rabi_ref_hz=10e6,
    )
    y_setup = apply_gate_mapping(base, "Y")
    cnot_setup = apply_gate_mapping(base, "CNOT")

    def run(setup):
        tx, rx = pulse_queue(8)
        tx.send(setup.cmd)
        eng = TwinEngine()
        if setup.initial_state:
            eng.set_state(setup.initial_state)
        eng.drain(rx)
        for i in range(128):
            eng.step(i * 1e-12, 1e-12)
        eng.renormalize()
        return bloch_vector(partial_trace_qubit0(state_vector_from_tuples(eng.state())))

    by = run(y_setup)
    bc = run(cnot_setup)
    assert abs(by[2] - bc[2]) > 0.5


def test_pipeline_includes_gate_mapping() -> None:
    out = run_twin_pipeline(
        "Apply a Hadamard-style pulse on qubit 0, 5 GHz, 80 ns, ideal.",
        n_steps=128,
        dt=1e-12,
    )
    assert out.get("gate_mapping")
    assert "HADAMARD" in str(out["gate_mapping"])
