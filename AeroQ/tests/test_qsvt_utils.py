import numpy as np

from aeroq.qsvt import chebyshev_fit_inverse


def test_chebyshev_fit_inverse_basic() -> None:
    coeffs, domain = chebyshev_fit_inverse(degree=12, kappa=50.0, grid_size=2048)
    assert coeffs.shape == (13,)
    assert domain[0] == 1.0 / 50.0
    assert domain[1] == 1.0
    assert np.isfinite(coeffs).all()

