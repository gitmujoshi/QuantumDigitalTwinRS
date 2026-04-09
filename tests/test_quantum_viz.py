"""Pure NumPy tests for Bloch / partial trace helpers (no PyO3)."""

from __future__ import annotations

import numpy as np

from twin_sentry.quantum_viz import (
    bloch_purity,
    bloch_vector,
    partial_trace_qubit0,
    partial_trace_qubit1,
    state_vector_from_tuples,
)


def test_state_vector_from_tuples_normalization() -> None:
    psi = state_vector_from_tuples([(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)])
    assert np.isclose(np.linalg.norm(psi), 1.0)


def test_bell_state_bloch_vectors_zero_xy() -> None:
    """|Φ+⟩ = (|00⟩+|11⟩)/√2: reduced states are maximally mixed → Bloch origin (x,y,z)=0."""
    s2 = 1.0 / np.sqrt(2.0)
    psi = np.array([s2, 0.0, 0.0, s2], dtype=np.complex128)
    rho0 = partial_trace_qubit0(psi)
    rho1 = partial_trace_qubit1(psi)
    x0, y0, z0 = bloch_vector(rho0)
    x1, y1, z1 = bloch_vector(rho1)
    assert np.isclose(x0, 0.0) and np.isclose(y0, 0.0) and np.isclose(z0, 0.0)
    assert np.isclose(x1, 0.0) and np.isclose(y1, 0.0) and np.isclose(z1, 0.0)
    assert np.isclose(bloch_purity(rho0), 0.5)
    assert np.isclose(bloch_purity(rho1), 0.5)


def test_product_00() -> None:
    psi = state_vector_from_tuples([(1.0, 0.0), (0.0, 0.0), (0.0, 0.0), (0.0, 0.0)])
    rho0 = partial_trace_qubit0(psi)
    x, y, z = bloch_vector(rho0)
    assert np.isclose(z, 1.0) and np.isclose(x, 0.0) and np.isclose(y, 0.0)
    assert np.isclose(bloch_purity(rho0), 1.0)
