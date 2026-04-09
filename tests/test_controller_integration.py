"""End-to-end controller + native twin (requires maturin-built extension)."""

from __future__ import annotations

import pytest

pytest.importorskip("twin_sentry._native")

from twin_sentry.controller import run_twin_pipeline


def test_run_twin_pipeline_heuristic_short() -> None:
    """When BAML is unavailable or fails, heuristic pulse still drives the twin."""
    out = run_twin_pipeline(
        "Apply a Hadamard-style pulse on qubit 0, 5 GHz, 80 ns, ideal.",
        n_steps=32,
        dt=1e-12,
        cloud_backend=None,
    )
    assert "fidelity" in out
    assert "pulse_command" in out
    assert "state" in out
    assert len(out["state"]) == 4
    assert out["pulse_command"]["frequency_hz"] > 0
