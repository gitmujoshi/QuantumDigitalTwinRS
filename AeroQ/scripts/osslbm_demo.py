from __future__ import annotations

import numpy as np

from aeroq.osslbm import OsslBmSpec, build_osslbm_one_step_qnode


def main() -> None:
    # 2D grid (power-of-two sizes for this MVP)
    nx, ny, nv = 2, 2, 16

    # Initial velocity density f0[y, x, v] (non-negative).
    f0 = np.zeros((ny, nx, nv), dtype=float)
    # D2Q9 uses channel 1 as +x (E). The rest are padding channels for nv=16.
    f0[0, 0, 1] = 1.0  # a single "packet" at (0,0) moving +x

    spec = OsslBmSpec(
        nx=nx, ny=ny, nv=nv, velocity_set="D2Q9", collision_theta=0.35, device="lightning.gpu"
    )
    qnode = build_osslbm_one_step_qnode(spec=spec, f0=f0, jit=True)

    out = qnode()
    print("output state norm:", float(np.linalg.norm(out)))
    # Optional: print probabilities for each basis state
    probs = np.abs(out) ** 2
    print("probs:", probs.round(6))


if __name__ == "__main__":
    main()

