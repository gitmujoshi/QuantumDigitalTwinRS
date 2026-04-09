"""
Optional submission of **gate-equivalent** circuits to quantum cloud / local simulators.

Public QPUs expose **gate schedules**, not the analog `PulseCommand` envelopes used by the
Rust twin. We map BAML `gate_type` + `PulseCommand.amplitude` to a small `QuantumCircuit`
(see module docstring in `docs/quantum-cloud-backends.md`).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

from twin_sentry import PulseCommand

logger = logging.getLogger(__name__)


def pulse_command_to_circuit(cmd: PulseCommand, gate_type: str | None) -> Any:
    """
    Build a measured 1- or 2-qubit circuit from policy-approved pulse parameters.

    This is a **logical** mapping for integration testing, not a calibrated OpenPulse
    waveform for a specific device.
    """
    from qiskit import QuantumCircuit

    gt = (gate_type or "ROTATION").upper()
    a = float(np.clip(cmd.amplitude, 0.0, 1.0))

    if gt == "CNOT":
        qc = QuantumCircuit(2, 2)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        return qc

    qc = QuantumCircuit(1, 1)
    if gt == "HADAMARD":
        qc.h(0)
    elif gt == "X":
        qc.x(0)
    elif gt == "Y":
        qc.y(0)
    elif gt == "Z":
        qc.z(0)
    elif gt == "PHASE":
        qc.p(a * np.pi, 0)
    elif gt in ("ROTATION", "CUSTOM"):
        qc.ry(a * np.pi, 0)
    else:
        qc.ry(a * np.pi, 0)
    qc.measure(0, 0)
    return qc


def run_local_aer(circuit: Any, shots: int) -> dict[str, Any]:
    """Run on Qiskit Aer locally (no IBM account). Requires ``qiskit`` + ``qiskit-aer``."""
    try:
        from qiskit_aer import AerSimulator
    except ImportError as e:
        return {
            "ok": False,
            "backend": "local_aer",
            "error": (
                "Install optional deps: pip install 'twinsentry-rs[quantum-cloud]' "
                f"(import error: {e})"
            ),
        }
    backend = AerSimulator()
    job = backend.run(circuit, shots=shots)
    result = job.result()
    counts = result.get_counts()
    return {
        "ok": True,
        "backend": "local_aer",
        "shots": shots,
        "counts": counts,
    }


def run_ibm_quantum(circuit: Any, shots: int) -> dict[str, Any]:
    """
    Submit to IBM Quantum (real QPU or cloud simulator), depending on env and account.

    Set ``QISKIT_IBM_TOKEN`` from https://quantum.ibm.com/ (legacy name ``IBM_QUANTUM_TOKEN``
    is also accepted).

    Optional:

    - ``IBM_QUANTUM_BACKEND`` — fixed backend name (e.g. ``ibm_torino``).
    - ``IBM_QUANTUM_PREFER_SIMULATOR`` — ``1`` / ``true`` to pick a cloud simulator when
      your account has no QPU access.
    """
    token = os.environ.get("QISKIT_IBM_TOKEN") or os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        return {
            "ok": False,
            "backend": "ibm_quantum",
            "error": "Set QISKIT_IBM_TOKEN (https://quantum.ibm.com/) for IBM Quantum.",
        }
    try:
        from qiskit import transpile
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as e:
        return {
            "ok": False,
            "backend": "ibm_quantum",
            "error": (
                "Install IBM extras: pip install 'twinsentry-rs[ibm-quantum]' "
                f"({e})"
            ),
        }

    try:
        service = QiskitRuntimeService(channel="ibm_quantum", token=token)
        fixed = os.environ.get("IBM_QUANTUM_BACKEND")
        prefer_sim = os.environ.get("IBM_QUANTUM_PREFER_SIMULATOR", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if fixed:
            backend = service.backend(fixed)
        else:
            backend = service.least_busy(operational=True, simulator=prefer_sim)
        tqc = transpile(circuit, backend=backend, optimization_level=1)
        job = backend.run(tqc, shots=shots)
        result = job.result()
        counts = result.get_counts()
        jid_attr = getattr(job, "job_id", None)
        jid = jid_attr() if callable(jid_attr) else jid_attr
        out: dict[str, Any] = {
            "ok": True,
            "backend": "ibm_quantum",
            "backend_name": getattr(backend, "name", str(backend)),
            "shots": shots,
            "counts": counts,
        }
        if jid is not None:
            out["job_id"] = jid
        return out
    except Exception as e:
        logger.exception("IBM Quantum submission failed")
        return {"ok": False, "backend": "ibm_quantum", "error": str(e)}


def submit_pulse_cloud(
    cmd: PulseCommand,
    gate_type: str | None,
    *,
    cloud_backend: str,
    shots: int,
) -> dict[str, Any]:
    """
    Build a circuit from ``cmd`` + ``gate_type`` and run on the selected backend.

    ``cloud_backend``: ``local_aer`` | ``ibm_quantum`` (aliases: ``aer``, ``ibm``).
    """
    cb = cloud_backend.strip().lower()
    if cb in ("off", "none", ""):
        return {"ok": False, "error": "cloud backend is off"}
    if cb in ("aer", "local_aer", "qiskit_aer"):
        circuit = pulse_command_to_circuit(cmd, gate_type)
        return run_local_aer(circuit, shots=shots)
    if cb in ("ibm", "ibm_quantum", "ibm_q"):
        circuit = pulse_command_to_circuit(cmd, gate_type)
        return run_ibm_quantum(circuit, shots=shots)
    return {"ok": False, "error": f"Unknown cloud_backend: {cloud_backend!r}"}
