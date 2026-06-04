"""
MatrixQ §4.1 VQE materials — mock (sandbox) and real-world classical + optional Aer.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from twin_sentry.simulation_contract import build_simulation_payload

PresetName = Literal["li2s", "custom"]
MappingName = Literal["jordan_wigner", "bravyi_kitaev"]
AnsatzName = Literal["uccsd_stub", "hardware_efficient"]


@dataclass(frozen=True)
class VqeMaterialsRequest:
    preset: PresetName = "li2s"
    mapping: MappingName = "jordan_wigner"
    ansatz: AnsatzName = "uccsd_stub"
    qubits: int = 12
    shots: int = 8192
    spsa_iterations: int = 4


def _seed(preset: str) -> float:
    h = hashlib.sha256(preset.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def run_vqe_materials_mock(req: VqeMaterialsRequest) -> dict[str, Any]:
    """Hybrid VQE loop mock: SPSA stages + MatrixQ-shaped payload + lab telemetry."""
    t0 = time.perf_counter()
    rng = _seed(req.preset)
    qubits = min(30, max(4, int(req.qubits)))

    stages: list[dict[str, Any]] = []
    energy = -42.5 - rng * 2.0
    for i in range(req.spsa_iterations):
        energy -= 0.02 + rng * 0.01
        stages.append(
            {
                "iteration": i + 1,
                "optimizer": "SPSA",
                "energy_hartree": round(energy, 5),
                "theta": round(0.35 + i * 0.08 + rng * 0.05, 4),
                "cloud_job": f"vqe-mock-{req.preset}-{i}",
                "duration_s": round(0.8 + rng * 0.3, 3),
            }
        )

    dominant = "1" * min(8, qubits)
    counts = {dominant: int(req.shots * (0.82 + rng * 0.1)), "0" * len(dominant): int(req.shots * 0.05)}
    remainder = req.shots - sum(counts.values())
    if remainder > 0:
        counts[dominant[:-1] + "0"] = remainder

    bond_angstrom = 2.14 + rng * 0.08 if req.preset == "li2s" else 1.9 + rng * 0.2
    max_voltage = round(4.12 - rng * 0.15, 2)

    business = {
        "domain": "vqe_materials",
        "preset": req.preset,
        "mapping": req.mapping,
        "ansatz": req.ansatz,
        "ground_state_energy_hartree": round(energy, 5),
        "optimal_bond_length_angstrom": round(bond_angstrom, 3),
        "max_safe_voltage_v": max_voltage,
        "kpi_narrative": "Mock: 3 weeks classical → under 4 minutes (portfolio target)",
    }

    duration_ms = (time.perf_counter() - t0) * 1000.0 + 110.0
    simulation_payload = build_simulation_payload(
        success=True,
        cloud={"ok": True, "backend": "mock_vqe_cloud", "counts": counts},
        shots=req.shots,
        gate_type="ROTATION",
        business_telemetry=business,
        duration_ms=duration_ms,
    )
    simulation_payload["quantum_metadata"]["allocated_qubits"] = qubits
    simulation_payload["quantum_metadata"]["optimized_gate_depth"] = 32

    return {
        "ok": True,
        "mock": True,
        "workflow": "[INPUT MOLECULAR GEOMETRY] → [HYBRID VQE LOOP] → [ACTIONABLE LAB TELEMETRY]",
        "request": {
            "preset": req.preset,
            "mapping": req.mapping,
            "ansatz": req.ansatz,
            "qubits": qubits,
        },
        "stages": stages,
        "simulation_payload": simulation_payload,
        "summary": {
            "max_safe_voltage_v": max_voltage,
            "bond_length_angstrom": round(bond_angstrom, 3),
            "wall_time_s": round(time.perf_counter() - t0, 3),
        },
    }


def _li2s_energy(params: np.ndarray) -> float:
    """Toy Li₂S PES: bond length r (Å) and ansatz angle θ (rad)."""
    r, theta = float(params[0]), float(params[1])
    re, de, a = 2.14, 0.45, 1.8
    morse = de * (1.0 - math.exp(-a * (r - re))) ** 2
    torsion = 0.08 * math.sin(theta) ** 2
    return morse + torsion - 0.52


def _spsa_minimize(
    x0: np.ndarray,
    energy_fn,
    *,
    iterations: int,
    seed: float,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    rng = np.random.default_rng(int(seed * 1e6) % (2**32))
    x = x0.copy()
    stages: list[dict[str, Any]] = []
    a, c = 0.602, 0.101
    A = 10
    for k in range(iterations):
        ak = a / ((k + 1) + A) ** 0.602
        ck = c / (k + 1) ** 0.101
        delta = rng.choice([-1.0, 1.0], size=x.shape)
        e_plus = energy_fn(x + ck * delta)
        e_minus = energy_fn(x - ck * delta)
        ghat = (e_plus - e_minus) / (2 * ck) * delta
        x = x - ak * ghat
        stages.append(
            {
                "iteration": k + 1,
                "optimizer": "SPSA",
                "energy_hartree": round(float(energy_fn(x)), 5),
                "bond_length_angstrom": round(float(x[0]), 4),
                "theta_rad": round(float(x[1]), 4),
                "duration_s": round(0.05 + seed * 0.01, 3),
            }
        )
    return x, stages


def _optional_aer_counts(shots: int, theta: float) -> dict[str, int] | None:
    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
    except ImportError:
        return None
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(theta, 0)
    qc.measure([0, 1], [0, 1])
    job = AerSimulator().run(qc, shots=shots)
    raw = job.result().get_counts()
    return {str(k).replace(" ", ""): int(v) for k, v in raw.items()}


def run_vqe_materials_real(req: VqeMaterialsRequest) -> dict[str, Any]:
    """Real-world path: classical SPSA on Li₂S toy PES; optional local Aer shots."""
    t0 = time.perf_counter()
    seed = _seed(req.preset)
    x0 = np.array([2.35, 0.2] if req.preset == "li2s" else [2.0, 0.0])
    x_opt, stages = _spsa_minimize(
        x0,
        _li2s_energy,
        iterations=max(4, req.spsa_iterations),
        seed=seed,
    )
    energy = float(_li2s_energy(x_opt))
    bond = float(x_opt[0])
    # Nernst-style toy: higher bond → slightly higher safe charge voltage cap
    max_voltage = round(min(4.35, max(3.85, 3.95 + 0.08 * (bond - 2.14))), 2)

    counts = _optional_aer_counts(req.shots, float(x_opt[1]))
    cloud_backend = "local_aer"
    if counts is None:
        cloud_backend = "classical_spsa"
        p0 = max(0.0, min(1.0, 0.5 + 0.35 * math.cos(float(x_opt[1]))))
        n0 = int(round(req.shots * p0))
        counts = {"00": n0, "11": req.shots - n0}

    business = {
        "domain": "vqe_materials",
        "execution": "real_world",
        "preset": req.preset,
        "mapping": req.mapping,
        "ansatz": req.ansatz,
        "ground_state_energy_hartree": round(energy, 5),
        "optimal_bond_length_angstrom": round(bond, 3),
        "max_safe_voltage_v": max_voltage,
        "use_case": "Li₂S cell chemistry — classical SPSA + optional Qiskit Aer",
        "kpi_note": "Classical optimization on toy PES; swap in PySCF/OpenMM for production.",
    }

    duration_ms = (time.perf_counter() - t0) * 1000.0
    simulation_payload = build_simulation_payload(
        success=True,
        cloud={"ok": True, "backend": cloud_backend, "counts": counts},
        shots=req.shots,
        gate_type="ROTATION",
        business_telemetry=business,
        duration_ms=duration_ms,
    )

    return {
        "ok": True,
        "mock": False,
        "execution": "real_world",
        "workflow": "[INPUT MOLECULAR GEOMETRY] → [HYBRID VQE LOOP] → [ACTIONABLE LAB TELEMETRY]",
        "request": {
            "preset": req.preset,
            "mapping": req.mapping,
            "ansatz": req.ansatz,
            "optimizer": "SPSA (numpy)",
            "quantum_backend": cloud_backend,
        },
        "stages": stages,
        "simulation_payload": simulation_payload,
        "summary": {
            "max_safe_voltage_v": max_voltage,
            "bond_length_angstrom": round(bond, 3),
            "energy_hartree": round(energy, 5),
            "wall_time_s": round(time.perf_counter() - t0, 3),
        },
    }


def _apply_materials_mock_sales(out: dict[str, Any], mock: dict[str, Any]) -> dict[str, Any]:
    out = dict(out)
    summ = dict(out.get("summary") or {})
    summ.update(
        {
            "max_safe_voltage_v": mock["max_safe_voltage_v"],
            "bond_length_angstrom": mock["bond_length_angstrom"],
            "energy_hartree": mock.get("ground_state_energy_hartree"),
            "runtime_label": mock.get("runtime_label"),
            "vs_classical": mock.get("vs_classical"),
        }
    )
    out["summary"] = summ
    sp = dict(out.get("simulation_payload") or {})
    bt = dict(sp.get("business_telemetry") or {})
    bt.update(
        {
            "max_safe_voltage_v": mock["max_safe_voltage_v"],
            "optimal_bond_length_angstrom": mock["bond_length_angstrom"],
            "ground_state_energy_hartree": mock.get("ground_state_energy_hartree"),
            "vs_classical": mock.get("vs_classical"),
        }
    )
    sp["business_telemetry"] = bt
    out["simulation_payload"] = sp
    return out


def run_vqe_materials(
    req: VqeMaterialsRequest,
    *,
    real: bool = False,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    scenario = None
    if scenario_id:
        from domain_mocks.sales_demos import (
            attach_sales_narrative_materials,
            get_materials_scenario,
        )

        scenario = get_materials_scenario(scenario_id)
        req = scenario.request

    if real:
        out = run_vqe_materials_real(req)
    else:
        out = run_vqe_materials_mock(req)
        if scenario is not None:
            out = _apply_materials_mock_sales(out, scenario.mock_outcome)

    if scenario is not None:
        from domain_mocks.sales_demos import attach_sales_narrative_materials

        out = attach_sales_narrative_materials(out, scenario)
    return out
