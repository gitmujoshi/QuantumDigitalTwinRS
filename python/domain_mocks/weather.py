"""
Regional weather / NWP workflow mock (not a real ECMWF/NOAA solver).

Demonstrates: grid setup → linear/LBM subroutine routing → synthetic forecast metrics.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

BackendName = Literal["classical_hpc", "hybrid_qsvt", "qpu_accelerator_stub"]


@dataclass(frozen=True)
class WeatherRunRequest:
    region: str
    horizon_hours: int = 24
    grid_nx: int = 32
    grid_ny: int = 32
    dt_minutes: int = 15
    backend: BackendName = "hybrid_qsvt"


def _seed(region: str, horizon_hours: int) -> int:
    h = hashlib.sha256(f"{region}:{horizon_hours}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def run_regional_forecast_mock(req: WeatherRunRequest) -> dict[str, Any]:
    """
    Mock regional forecast: synthetic 2D temperature anomaly field + workflow metadata.

    ``hybrid_qsvt`` pretends a quantum-accelerated linear solve; ``qpu_accelerator_stub``
    adds queue latency; ``classical_hpc`` is fastest in this toy model.
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(_seed(req.region, req.horizon_hours))

    nx, ny = int(req.grid_nx), int(req.grid_ny)
    steps = max(1, int(req.horizon_hours) * 60 // max(1, int(req.dt_minutes)))

    # Synthetic "initial conditions" + one prognostic step (toy, not Navier–Stokes)
    lat = np.linspace(25.0, 55.0, ny)
    lon = np.linspace(-130.0, -65.0, nx)
    base_t = 15.0 + 10.0 * np.sin(np.pi * lat / 55.0)[:, None]
    anomaly = rng.normal(0, 1.2, (ny, nx))
    field_k = base_t + anomaly

    subroutine = "classical_lu"
    queue_wait_s = 0.0
    if req.backend == "hybrid_qsvt":
        subroutine = "qsvt_linear_solve_stub"
        # Toy: QSVT path slightly better RMSE, more "compute" time
        field_k += rng.normal(0, 0.15, (ny, nx))
    elif req.backend == "qpu_accelerator_stub":
        subroutine = "qpu_queued_linear_stub"
        queue_wait_s = 2.5 + rng.uniform(0, 1.5)
        field_k += rng.normal(0, 0.25, (ny, nx))

    # Mock verification vs "analysis" (deterministic target from seed)
    target = base_t + rng.normal(0, 1.0, (ny, nx))
    rmse_k = float(np.sqrt(np.mean((field_k - target) ** 2)))
    wall_s = time.perf_counter() - t0 + queue_wait_s

    speedup_claim = {
        "classical_hpc": 1.0,
        "hybrid_qsvt": 1.35,
        "qpu_accelerator_stub": 1.15,
    }[req.backend]

    return {
        "ok": True,
        "mock": True,
        "region": req.region,
        "backend": req.backend,
        "subroutine": subroutine,
        "grid": {"nx": nx, "ny": ny, "dt_minutes": req.dt_minutes, "steps": steps},
        "metrics": {
            "rmse_vs_analysis_k": round(rmse_k, 4),
            "mean_temp_k": round(float(field_k.mean()), 3),
            "max_anomaly_k": round(float(np.max(np.abs(field_k - base_t))), 3),
            "wall_time_s": round(wall_s, 3),
            "queue_wait_s": round(queue_wait_s, 3),
            "claimed_speedup_vs_classical": speedup_claim,
        },
        "field_summary": {
            "shape": [ny, nx],
            "sample_corner_c": field_k[0, 0],
            "sample_center_c": field_k[ny // 2, nx // 2],
        },
        "notes": (
            "Mock only: no real NWP dynamics. Shows how AeroQ-style backend routing "
            "would attach to a regional forecast pipeline."
        ),
    }
