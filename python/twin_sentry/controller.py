"""
TwinSentry control plane: NL intent → BAML `QuantumPulse` → Rust `TwinEngine` → fidelity score,
with Langfuse tracing (intent, schema, noise metadata, simulation output).

Optional: map approved pulses to gate circuits and submit to Qiskit Aer or IBM Quantum
(see `quantum_cloud.py`, `docs/quantum-cloud-backends.md`).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Repo root (contains `baml_client/`): python/twin_sentry/controller.py → parents[2]
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin_sentry import PulseCommand, TwinEngine, pulse_queue  # noqa: E402

logger = logging.getLogger(__name__)


def _langfuse_client() -> Any:
    try:
        from langfuse import Langfuse
    except ImportError:
        return None
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = os.environ.get("LANGFUSE_SECRET_KEY")
    if not pk or not sk:
        return None
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
    return Langfuse(public_key=pk, secret_key=sk, host=host)


def _parse_pulse_with_baml(user_intent: str) -> tuple[Any | None, str | None]:
    try:
        from baml_client import b

        pulse = b.ParsePulseFromIntent(user_intent)
        return pulse, None
    except Exception as e:
        logger.warning("BAML parse failed (%s); using heuristic pulse", e)
        return None, str(e)


def _heuristic_pulse_command(intent: str) -> PulseCommand:
    text = intent.lower()
    amplitude = 0.35
    if "violation" in text or "unsafe" in text or "1.5" in text:
        amplitude = 0.99
    if "hadamard" in text or "h gate" in text:
        amplitude = 0.5
    if "pi" in text or "π" in text:
        amplitude = 0.45
    return PulseCommand(
        amplitude=amplitude,
        frequency_hz=5e9,
        duration_s=80e-9,
        qubit0_split_hz=5e9,
        qubit1_split_hz=4.5e9,
        rabi_ref_hz=10e6,
    )


def quantum_pulse_to_command(pulse: Any) -> PulseCommand:
    amp = pulse.amplitude.value
    fq = float(pulse.frequency_hz)
    return PulseCommand(
        amplitude=float(amp),
        frequency_hz=fq,
        duration_s=float(pulse.duration_s),
        qubit0_split_hz=fq,
        qubit1_split_hz=fq * 0.9,
        rabi_ref_hz=10e6,
    )


def _noise_metadata(pulse: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    np = getattr(pulse, "noise_profile", None)
    if np is None:
        return out
    try:
        out["t2_dephasing_relative"] = float(np.t2_dephasing_relative.value)
        out["thermal_jitter_relative"] = float(np.thermal_jitter_relative.value)
    except Exception:
        pass
    return out


def _parse_intent_all(
    user_intent: str,
) -> tuple[PulseCommand, str | None, dict[str, Any], str | None, bool]:
    """Returns ``cmd``, ``baml_error``, ``noise_meta``, ``gate_type``, ``baml_ok``."""
    pulse, baml_error = _parse_pulse_with_baml(user_intent)
    baml_ok = pulse is not None
    if pulse is not None:
        cmd = quantum_pulse_to_command(pulse)
        noise_meta = _noise_metadata(pulse)
        gate_val = pulse.gate_type.value
    else:
        cmd = _heuristic_pulse_command(user_intent)
        noise_meta = {}
        gate_val = None
    return cmd, baml_error, noise_meta, gate_val, baml_ok


def _run_rust_twin(cmd: PulseCommand, n_steps: int, dt: float) -> tuple[float, list[Any], float]:
    tx, rx = pulse_queue(64)
    try:
        tx.send(cmd)
    except Exception as e:
        logger.warning("queue send failed: %s", e)
    engine = TwinEngine()
    engine.drain(rx)
    t = 0.0
    for _ in range(n_steps):
        engine.step(t, dt)
        t += dt
    engine.renormalize()
    fid = float(engine.fidelity_ground())
    return fid, engine.state(), t


def _pulse_command_dict(cmd: PulseCommand) -> dict[str, Any]:
    return {
        "amplitude": cmd.amplitude,
        "frequency_hz": cmd.frequency_hz,
        "duration_s": cmd.duration_s,
        "qubit0_split_hz": cmd.qubit0_split_hz,
        "qubit1_split_hz": cmd.qubit1_split_hz,
        "rabi_ref_hz": cmd.rabi_ref_hz,
    }


def _run_cloud_if_requested(
    cmd: PulseCommand,
    gate_type: str | None,
    cloud_backend: str | None,
    cloud_shots: int,
) -> dict[str, Any] | None:
    if not cloud_backend or str(cloud_backend).strip().lower() in ("off", "none", ""):
        return None
    try:
        from twin_sentry.quantum_cloud import submit_pulse_cloud

        return submit_pulse_cloud(cmd, gate_type, cloud_backend=cloud_backend, shots=cloud_shots)
    except Exception as e:
        logger.warning("cloud submit failed: %s", e)
        return {"ok": False, "error": str(e)}


def _assemble_result(
    trace_id: str | None,
    baml_error: str | None,
    noise_meta: dict[str, Any],
    cmd: PulseCommand,
    gate_val: str | None,
    fid: float,
    state: list[Any],
    t: float,
    cloud_backend: str | None,
    cloud_shots: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "trace_id": trace_id,
        "baml_error": baml_error,
        "noise": noise_meta,
        "gate_type": gate_val,
        "pulse_command": _pulse_command_dict(cmd),
        "fidelity": fid,
        "state": state,
        "final_time": t,
    }
    cloud = _run_cloud_if_requested(cmd, gate_val, cloud_backend, cloud_shots)
    if cloud is not None:
        body["cloud"] = cloud
    return body


def run_twin_pipeline(
    user_intent: str,
    *,
    n_steps: int = 128,
    dt: float = 2e-12,
    cloud_backend: str | None = None,
    cloud_shots: int = 1024,
) -> dict[str, Any]:
    lf = _langfuse_client()
    if lf is None:
        return _simulate_only(
            user_intent,
            n_steps=n_steps,
            dt=dt,
            trace_id=None,
            cloud_backend=cloud_backend,
            cloud_shots=cloud_shots,
        )

    try:
        with lf.start_as_current_observation(
            as_type="span",
            name="TwinSentry Pipeline",
            input={"intent": user_intent},
            metadata={"component": "controller"},
        ) as root:
            trace_id: str | None = getattr(root, "trace_id", None)

            with lf.start_as_current_observation(as_type="span", name="baml_parse") as baml_span:
                cmd, baml_error, noise_meta, gate_val, baml_ok = _parse_intent_all(user_intent)
                baml_span.update(
                    output={
                        "ok": baml_ok,
                        "error": baml_error,
                        "gate_type": gate_val,
                    },
                )

            if noise_meta:
                root.update(metadata={"noise": noise_meta})

            tx, rx = pulse_queue(64)
            try:
                tx.send(cmd)
            except Exception as e:
                logger.warning("queue send failed: %s", e)

            engine = TwinEngine()
            engine.drain(rx)

            with lf.start_as_current_observation(
                as_type="span",
                name="rust_twin",
                metadata={
                    "n_steps": n_steps,
                    "dt": dt,
                    "pulse_amplitude": cmd.amplitude,
                    "pulse_frequency_hz": cmd.frequency_hz,
                },
            ) as rust_span:
                t = 0.0
                for _ in range(n_steps):
                    engine.step(t, dt)
                    t += dt
                engine.renormalize()
                fid = float(engine.fidelity_ground())
                rust_span.update(output={"fidelity_ground": fid, "final_t": t})

            result_body = _assemble_result(
                trace_id,
                baml_error,
                noise_meta,
                cmd,
                gate_val,
                fid,
                engine.state(),
                t,
                cloud_backend,
                cloud_shots,
            )
            root.update(output=result_body)

            if trace_id is not None:
                try:
                    lf.create_score(
                        name="fidelity_ground",
                        value=fid,
                        trace_id=trace_id,
                        data_type="NUMERIC",
                    )
                except Exception as e:
                    logger.warning("Langfuse score failed: %s", e)

            try:
                lf.flush()
            except Exception:
                pass

            return result_body
    except Exception as e:
        logger.warning("Langfuse instrumentation failed (%s); running without trace", e)
        return _simulate_only(
            user_intent,
            n_steps=n_steps,
            dt=dt,
            trace_id=None,
            cloud_backend=cloud_backend,
            cloud_shots=cloud_shots,
        )


def _simulate_only(
    user_intent: str,
    *,
    n_steps: int,
    dt: float,
    trace_id: str | None,
    cloud_backend: str | None = None,
    cloud_shots: int = 1024,
) -> dict[str, Any]:
    cmd, baml_error, noise_meta, gate_val, _baml_ok = _parse_intent_all(user_intent)
    fid, state, t = _run_rust_twin(cmd, n_steps, dt)
    return _assemble_result(
        trace_id,
        baml_error,
        noise_meta,
        cmd,
        gate_val,
        fid,
        state,
        t,
        cloud_backend,
        cloud_shots,
    )
