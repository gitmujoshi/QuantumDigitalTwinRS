from __future__ import annotations

import numpy as np

from aeroq import AeroQKernel


def main() -> None:
    k = AeroQKernel(config_path="config.yaml")
    A = np.array([[3.0, 1.0], [1.0, 2.0]])
    b = np.array([9.0, 8.0])
    x = k.solve_linear_system(A, b)
    print("backend:", k.backend)
    print("x:", x)
    assert np.allclose(A @ x, b)


if __name__ == "__main__":
    main()

