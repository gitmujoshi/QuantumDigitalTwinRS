"""
Production-style QPU vendor mocks (IBM / IonQ / Rigetti-shaped APIs).

No real hardware calls — simulates calibration, queue, policy gate, and job results.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from twin_sentry import PulseCommand
from twin_sentry.quantum_cloud import pulse_command_to_circuit

VendorName = Literal["mock_ibm", "mock_ionq", "mock_rigetti"]


@dataclass(frozen=True)
class VendorCalibration:
    vendor: str
    backend_name: str
    t1_us: float
    t2_us: float
    readout_error: float
    max_duration_ns: float
    operational: bool


_VENDORS: dict[str, dict[str, float | str | bool]] = {
    "mock_ibm": {
        "backend_name": "ibm_mock_torino",
        "t1_us": 80.0,
        "t2_us": 65.0,
        "readout_error": 0.012,
        "max_duration_ns": 800.0,
    },
    "mock_ionq": {
        "backend_name": "ionq_mock_aria",
        "t1_us": 120.0,
        "t2_us": 95.0,
        "readout_error": 0.008,
        "max_duration_ns": 600.0,
    },
    "mock_rigetti": {
        "backend_name": "rigetti_mock_aspen",
        "t1_us": 55.0,
        "t2_us": 48.0,
        "readout_error": 0.018,
        "max_duration_ns": 500.0,
    },
}


def get_calibration_mock(vendor: VendorName) -> VendorCalibration:
    spec = _VENDORS[vendor]
    return VendorCalibration(
        vendor=vendor,
        backend_name=str(spec["backend_name"]),
        t1_us=float(spec["t1_us"]),
        t2_us=float(spec["t2_us"]),
        readout_error=float(spec["readout_error"]),
        max_duration_ns=float(spec["max_duration_ns"]),
        operational=True,
    )


def _mock_counts(cmd: PulseCommand, gate_type: str | None, shots: int) -> dict[str, int]:
    """Deterministic pseudo-distribution from pulse + gate."""
    key = f"{cmd.amplitude}:{cmd.frequency_hz}:{gate_type}:{shots}"
    h = hashlib.sha256(key.encode()).hexdigest()
    a = int(h[:8], 16) % shots
    b = shots - a
    gt = (gate_type or "ROTATION").upper()
    if gt == "HADAMARD":
        return {"0": a, "1": b}
    if gt == "X":
        return {"1": a, "0": b}
    return {"00": b // 2, "11": a // 2, "01": b - b // 2, "10": a - a // 2}


def submit_pulse_vendor_mock(
    cmd: PulseCommand,
    gate_type: str | None,
    *,
    vendor: VendorName,
    shots: int,
    policy_approved: bool = True,
    pulse_duration_s: float | None = None,
) -> dict[str, Any]:
    """
    Mock production control path: policy → calibration check → queue → job → counts.
    """
    if not policy_approved:
        return {
            "ok": False,
            "backend": vendor,
            "error": "Policy rejected pulse (mock safety interlock).",
            "stage": "policy_gate",
        }

    cal = get_calibration_mock(vendor)
    dur_ns = (pulse_duration_s if pulse_duration_s is not None else cmd.duration_s) * 1e9
    if dur_ns > cal.max_duration_ns:
        return {
            "ok": False,
            "backend": vendor,
            "error": (
                f"Pulse duration {dur_ns:.0f} ns exceeds mock limit {cal.max_duration_ns:.0f} ns "
                f"on {cal.backend_name}"
            ),
            "stage": "calibration_check",
            "calibration": cal.__dict__,
        }

    if not cal.operational:
        return {
            "ok": False,
            "backend": vendor,
            "error": "Backend not operational (mock maintenance window).",
            "stage": "queue",
        }

    t0 = time.perf_counter()
    queue_depth = (int(hashlib.sha256(vendor.encode()).hexdigest()[:4], 16) % 5) + 1
    time.sleep(min(0.05 * queue_depth, 0.25))

    job_id = f"{vendor}-{uuid.uuid4().hex[:12]}"
    try:
        circuit = pulse_command_to_circuit(cmd, gate_type)
        n_qubits = getattr(circuit, "num_qubits", 1)
        depth_fn = getattr(circuit, "depth", None)
        depth = depth_fn() if callable(depth_fn) else None
    except ImportError:
        circuit = None
        n_qubits = 1
        depth = None

    counts = _mock_counts(cmd, gate_type, shots)
    wall_s = time.perf_counter() - t0

    return {
        "ok": True,
        "mock": True,
        "backend": vendor,
        "backend_name": cal.backend_name,
        "job_id": job_id,
        "shots": shots,
        "counts": counts,
        "queue_depth_at_submit": queue_depth,
        "wall_time_s": round(wall_s, 3),
        "calibration_snapshot": {
            "t1_us": cal.t1_us,
            "t2_us": cal.t2_us,
            "readout_error": cal.readout_error,
        },
        "circuit_meta": {
            "num_qubits": n_qubits,
            "depth": depth,
            "gate_type": gate_type,
        },
        "control_plane": {
            "policy_approved": policy_approved,
            "pulse_amplitude": cmd.amplitude,
            "pulse_frequency_hz": cmd.frequency_hz,
            "pulse_duration_s": cmd.duration_s,
        },
        "notes": "Mock vendor — replace with Qiskit IBM Runtime / IonQ / Rigetti SDKs for production.",
    }
