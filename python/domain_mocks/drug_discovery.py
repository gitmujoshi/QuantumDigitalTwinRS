"""
Drug-discovery pipeline mock (not real docking or VQE on hardware).

Stages: classical docking → optional quantum chemistry stub → ML surrogate scoring.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Literal

BackendName = Literal["classical_only", "hybrid_vqe", "surrogate_ml"]


@dataclass(frozen=True)
class DrugPipelineRequest:
    molecule_id: str
    target_protein: str = "Kinase-X"
    backend: BackendName = "hybrid_vqe"
    conformer_count: int = 8


def _mol_seed(molecule_id: str) -> int:
    return int.from_bytes(hashlib.sha256(molecule_id.encode()).digest()[:4], "big")


def run_drug_pipeline_mock(req: DrugPipelineRequest) -> dict[str, Any]:
    """Return staged mock results for portfolio demos."""
    t0 = time.perf_counter()
    seed = _mol_seed(req.molecule_id)
    rng = (seed % 10_000) / 10_000.0

    stages: list[dict[str, Any]] = []

    dock_score = 7.2 + (rng - 0.5) * 1.5
    stages.append(
        {
            "stage": "classical_docking",
            "backend": "gpu_docking_stub",
            "binding_affinity_kcal_mol": round(dock_score, 2),
            "poses_screened": int(req.conformer_count) * 120,
            "duration_s": round(0.4 + rng * 0.2, 3),
        }
    )

    ground_energy_hartree = -42.0 - rng * 3.0
    if req.backend in ("hybrid_vqe", "surrogate_ml"):
        vqe_energy = ground_energy_hartree - 0.08 - rng * 0.05
        stages.append(
            {
                "stage": "vqe_active_space_stub",
                "backend": "mock_qpu_chemistry",
                "qubits_used": 12,
                "energy_hartree": round(vqe_energy, 4),
                "delta_vs_classical_hf": round(vqe_energy - ground_energy_hartree, 4),
                "job_id": f"chem-mock-{req.molecule_id[:8]}",
                "duration_s": round(3.0 + rng * 2.0, 3),
            }
        )
        ground_energy_hartree = vqe_energy

    admet_score = min(0.95, 0.55 + rng * 0.35)
    if req.backend == "surrogate_ml":
        stages.append(
            {
                "stage": "ml_surrogate_ranking",
                "backend": "classical_gnn_stub",
                "admet_score": round(admet_score, 3),
                "duration_s": round(0.15, 3),
            }
        )

    lead_ok = dock_score < 8.0 and admet_score > 0.6

    return {
        "ok": True,
        "mock": True,
        "molecule_id": req.molecule_id,
        "target_protein": req.target_protein,
        "backend": req.backend,
        "lead_candidate": lead_ok,
        "stages": stages,
        "summary": {
            "best_binding_kcal_mol": round(dock_score, 2),
            "final_energy_hartree": round(ground_energy_hartree, 4),
            "admet_score": round(admet_score, 3),
            "wall_time_s": round(time.perf_counter() - t0, 3),
        },
        "notes": (
            "Mock only: replace stubs with RDKit/OpenMM, PySCF, and real VQE providers "
            "for production drug-discovery integration."
        ),
    }
