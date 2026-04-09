"""Visualization helpers: reduced density matrices and Bloch vectors for a 2-qubit pure state."""

from __future__ import annotations

from typing import Sequence

import numpy as np

# Pauli matrices
_SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
_SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
_SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)


def state_vector_from_tuples(coeffs: Sequence[tuple[float, float]]) -> np.ndarray:
    """Coeffs as (re, im) per basis state |00⟩…|11⟩."""
    return np.array([complex(re, im) for re, im in coeffs], dtype=np.complex128)


def partial_trace_qubit0(psi: np.ndarray) -> np.ndarray:
    """Trace out qubit 1; return 2×2 density matrix for qubit 0."""
    c = psi.ravel()
    assert c.shape[0] == 4
    r00 = np.abs(c[0]) ** 2 + np.abs(c[1]) ** 2
    r01 = c[0] * np.conj(c[2]) + c[1] * np.conj(c[3])
    r10 = np.conj(r01)
    r11 = np.abs(c[2]) ** 2 + np.abs(c[3]) ** 2
    return np.array([[r00, r01], [r10, r11]], dtype=np.complex128)


def partial_trace_qubit1(psi: np.ndarray) -> np.ndarray:
    """Trace out qubit 0; return 2×2 density matrix for qubit 1."""
    c = psi.ravel()
    assert c.shape[0] == 4
    r00 = np.abs(c[0]) ** 2 + np.abs(c[2]) ** 2
    r01 = c[0] * np.conj(c[1]) + c[2] * np.conj(c[3])
    r10 = np.conj(r01)
    r11 = np.abs(c[1]) ** 2 + np.abs(c[3]) ** 2
    return np.array([[r00, r01], [r10, r11]], dtype=np.complex128)


def bloch_vector(rho: np.ndarray) -> tuple[float, float, float]:
    """Bloch coordinates (x, y, z) from a 2×2 density matrix."""
    x = float(np.real(np.trace(rho @ _SX)))
    y = float(np.real(np.trace(rho @ _SY)))
    z = float(np.real(np.trace(rho @ _SZ)))
    return x, y, z


def bloch_purity(rho: np.ndarray) -> float:
    """Tr(ρ²) — 1 for pure, <1 for mixed."""
    return float(np.real(np.trace(rho @ rho)))
