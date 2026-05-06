from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True)
class QsvtSpec:
    """
    Lightweight container for a QSVT-based linear-solve plan.

    Notes:
    - This module is an *MVP scaffold* and intentionally avoids claiming a full
      production QSVT implementation without the right dependencies and validation.
    - The key deliverables here are:
      - a block-encoding entrypoint compatible with PennyLane
      - a polynomial approximation utility for 1/x
      - an execution hook where catalyst.jit can be applied
    """

    alpha: float
    poly_coeffs: np.ndarray
    domain: tuple[float, float]
    kappa: float


def chebyshev_fit_inverse(
    *,
    degree: int,
    kappa: float,
    grid_size: int = 4096,
) -> tuple[np.ndarray, tuple[float, float]]:
    """
    Fit a Chebyshev polynomial approximation to f(x)=1/x on [1/kappa, 1].

    Returns (coeffs, domain) where coeffs are in the Chebyshev basis (T_0..T_degree).

    This is a practical numeric utility you can plug into a QSVT construction.
    """
    if degree < 1:
        raise ValueError("degree must be >= 1")
    if kappa <= 1.0:
        raise ValueError("kappa must be > 1")
    if grid_size < 128:
        raise ValueError("grid_size too small")

    a = 1.0 / float(kappa)
    b = 1.0
    xs = np.linspace(a, b, grid_size)
    ys = 1.0 / xs

    # Map x in [a,b] to t in [-1,1] for Chebyshev fitting.
    ts = (2.0 * xs - (b + a)) / (b - a)
    coeffs = np.polynomial.chebyshev.chebfit(ts, ys, deg=degree)
    return coeffs.astype(float), (a, b)


def block_encode_sparse_matrix(
    A: Any,
    *,
    wires: list[int],
    alpha: float | None = None,
) -> Callable[[], None]:
    """
    Return a PennyLane operation factory that applies a block-encoding of A/alpha.

    Intended usage (inside a qnode):

        op = block_encode_sparse_matrix(A, wires=[...])
        op()

    Requirements / expectations:
    - A should be 256x256 (or generally 2^n x 2^n) for this MVP.
    - This uses PennyLane's `qml.BlockEncode` if available.

    alpha:
    - scaling factor s.t. ||A/alpha|| <= 1, needed for block-encoding.
    - if None, uses a conservative Frobenius-norm-based alpha.
    """
    try:
        import pennylane as qml  # type: ignore
    except Exception as e:
        raise ImportError("PennyLane is required for block encoding. Install `aeroq[qsvt]`.") from e

    # Accept numpy arrays or scipy sparse matrices without importing scipy explicitly.
    if hasattr(A, "toarray"):
        A_dense = np.asarray(A.toarray(), dtype=float)
    else:
        A_dense = np.asarray(A, dtype=float)

    if A_dense.ndim != 2 or A_dense.shape[0] != A_dense.shape[1]:
        raise ValueError(f"A must be square; got {A_dense.shape}")

    n = A_dense.shape[0]
    # MVP expectation: power of two.
    if n & (n - 1) != 0:
        raise ValueError("A dimension must be a power of 2 for this block-encoding scaffold.")

    if alpha is None:
        # Conservative: ensure scaling <= 1. In practice you may use ||A||_1 or a tighter bound.
        alpha = float(np.linalg.norm(A_dense, ord="fro"))
        if alpha == 0.0:
            alpha = 1.0

    scaled = A_dense / float(alpha)

    def _op() -> None:
        qml.BlockEncode(scaled, wires=wires)

    return _op


def build_qsvt_linear_solve_spec(
    *,
    degree: int,
    kappa: float,
    alpha: float,
) -> QsvtSpec:
    coeffs, domain = chebyshev_fit_inverse(degree=degree, kappa=kappa)
    return QsvtSpec(alpha=float(alpha), poly_coeffs=coeffs, domain=domain, kappa=float(kappa))


def catalyst_jit_if_available(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a function with catalyst.jit if Catalyst is installed, otherwise return fn unchanged.
    """
    try:
        from catalyst import jit  # type: ignore
    except Exception:
        return fn
    return jit(fn)

