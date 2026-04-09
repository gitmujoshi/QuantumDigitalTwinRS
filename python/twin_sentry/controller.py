"""
TwinSentry control plane: NL intent → BAML `QuantumPulse` → Rust `TwinEngine` → fidelity score,
with Langfuse tracing (intent, schema, noise metadata, simulation output).
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


def run_twin_pipeline(
    user_intent: str,
    *,
    n_steps: int = 128,
    dt: float = 2e-12,
) -> dict[str, Any]:
    lf = _langfuse_client()
    if lf is None:
        return _simulate_only(user_intent, n_steps=n_steps, dt=dt, trace_id=None)

    try:
        with lf.start_as_current_observation(
            as_type="span",
            name="TwinSentry Pipeline",
            input={"intent": user_intent},
            metadata={"component": "controller"},
        ) as root:
            trace_id: str | None = getattr(root, "trace_id", None)

            with lf.start_as_current_observation(as_type="span", name="baml_parse") as baml_span:
                pulse, baml_error = _parse_pulse_with_baml(user_intent)
                gate_val = None
                if pulse is not None:
                    gate_val = pulse.gate_type.value
                baml_span.update(
                    output={
                        "ok": pulse is not None,
                        "error": baml_error,
                        "gate_type": gate_val,
                    },
                )

            if pulse is not None:
                cmd = quantum_pulse_to_command(pulse)
                noise_meta = _noise_metadata(pulse)
            else:
                cmd = _heuristic_pulse_command(user_intent)
                noise_meta = {}

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

            result_body = {
                "trace_id": trace_id,
                "baml_error": baml_error,
                "noise": noise_meta,
                "pulse_command": {
                    "amplitude": cmd.amplitude,
                    "frequency_hz": cmd.frequency_hz,
                    "duration_s": cmd.duration_s,
                    "qubit0_split_hz": cmd.qubit0_split_hz,
                    "qubit1_split_hz": cmd.qubit1_split_hz,
                    "rabi_ref_hz": cmd.rabi_ref_hz,
                },
                "fidelity": fid,
                "state": engine.state(),
                "final_time": t,
            }
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
        return _simulate_only(user_intent, n_steps=n_steps, dt=dt, trace_id=None)


def _simulate_only(
    user_intent: str,
    *,
    n_steps: int,
    dt: float,
    trace_id: str | None,
) -> dict[str, Any]:
    pulse, baml_error = _parse_pulse_with_baml(user_intent)
    if pulse is not None:
        cmd = quantum_pulse_to_command(pulse)
        noise_meta = _noise_metadata(pulse)
    else:
        cmd = _heuristic_pulse_command(user_intent)
        noise_meta = {}
    tx, rx = pulse_queue(64)
    try:
        tx.send(cmd)
    except Exception:
        pass
    engine = TwinEngine()
    engine.drain(rx)
    t = 0.0
    for _ in range(n_steps):
        engine.step(t, dt)
        t += dt
    engine.renormalize()
    fid = float(engine.fidelity_ground())
    return {
        "trace_id": trace_id,
        "baml_error": baml_error,
        "noise": noise_meta,
        "pulse_command": {
            "amplitude": cmd.amplitude,
            "frequency_hz": cmd.frequency_hz,
            "duration_s": cmd.duration_s,
            "qubit0_split_hz": cmd.qubit0_split_hz,
            "qubit1_split_hz": cmd.qubit1_split_hz,
            "rabi_ref_hz": cmd.rabi_ref_hz,
        },
        "fidelity": fid,
        "state": engine.state(),
        "final_time": t,
    }
