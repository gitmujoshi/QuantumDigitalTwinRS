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
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

# Repo root (contains `baml_client/`): python/twin_sentry/controller.py → parents[2]
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from twin_sentry.llm_env import configure_ollama_for_baml  # noqa: E402

configure_ollama_for_baml(_ROOT)

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


def _baml_parse_sync(user_intent: str) -> tuple[Any, str | None]:
    from baml_client import b
    from twin_sentry.baml_log import new_collector, persist_collector, save_enabled

    collector = new_collector() if save_enabled() else None
    opts: dict[str, Any] = {"collector": collector} if collector is not None else {}
    try:
        pulse = b.ParsePulseFromIntent(user_intent, baml_options=opts)
        log_path = persist_collector(collector, user_intent, ok=True)
        return pulse, log_path
    except Exception as e:
        persist_collector(collector, user_intent, ok=False, error=str(e))
        raise


def _parse_pulse_with_baml(
    user_intent: str, *, timeout_s: float = 90.0
) -> tuple[Any | None, str | None, str | None]:
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_baml_parse_sync, user_intent)
            pulse, log_path = fut.result(timeout=timeout_s)
        return pulse, None, log_path
    except FuturesTimeoutError:
        msg = f"BAML/Ollama timed out after {timeout_s:.0f}s; using heuristic pulse"
        logger.warning(msg)
        return None, msg, None
    except Exception as e:
        logger.warning("BAML parse failed (%s); using heuristic pulse", e)
        return None, str(e), None


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
) -> tuple[
    PulseCommand,
    str | None,
    dict[str, Any],
    str | None,
    bool,
    str | None,
    list[tuple[float, float]] | None,
    str | None,
]:
    """Returns cmd, baml_error, noise_meta, gate_type, baml_ok, baml_log_path, initial_state, gate_note."""
    pulse, baml_error, baml_log_path = _parse_pulse_with_baml(user_intent)
    baml_ok = pulse is not None
    if pulse is not None:
        cmd = quantum_pulse_to_command(pulse)
        noise_meta = _noise_metadata(pulse)
        gate_val = pulse.gate_type.value
    else:
        cmd = _heuristic_pulse_command(user_intent)
        noise_meta = {}
        gate_val = _infer_gate_from_intent(user_intent)

    from twin_sentry.gate_mapping import apply_gate_mapping

    setup = apply_gate_mapping(cmd, gate_val)
    return (
        setup.cmd,
        baml_error,
        noise_meta,
        gate_val,
        baml_ok,
        baml_log_path,
        setup.initial_state,
        setup.description,
    )


def _infer_gate_from_intent(intent: str) -> str | None:
    text = intent.lower()
    if "hadamard" in text or "h gate" in text:
        return "HADAMARD"
    if "cnot" in text:
        return "CNOT"
    if " pi " in f" {text} " or "π" in text:
        return "X"
    if "phase" in text or " z " in f" {text} ":
        return "Z"
    return None


def _run_rust_twin(
    cmd: PulseCommand,
    n_steps: int,
    dt: float,
    *,
    initial_state: list[tuple[float, float]] | None = None,
) -> tuple[float, list[Any], float]:
    tx, rx = pulse_queue(64)
    try:
        tx.send(cmd)
    except Exception as e:
        logger.warning("queue send failed: %s", e)
    engine = TwinEngine()
    if initial_state is not None:
        engine.set_state(initial_state)
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
    baml_log_path: str | None = None,
    gate_mapping: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "trace_id": trace_id,
        "langfuse_enabled": trace_id is not None,
        "baml_error": baml_error,
        "baml_log_path": baml_log_path,
        "noise": noise_meta,
        "gate_type": gate_val,
        "gate_mapping": gate_mapping,
        "pulse_command": _pulse_command_dict(cmd),
        "fidelity": fid,
        "state": state,
        "final_time": t,
    }
    cloud = _run_cloud_if_requested(cmd, gate_val, cloud_backend, cloud_shots)
    if cloud is not None:
        body["cloud"] = cloud

    from twin_sentry.simulation_contract import build_simulation_payload

    body["simulation_payload"] = build_simulation_payload(
        success=True,
        fidelity=fid,
        state=state,
        cloud=cloud,
        shots=cloud_shots,
        gate_type=gate_val,
        business_telemetry={
            "domain": "twin_sentry",
            "fidelity_ground": fid,
            "final_time_s": t,
        },
    )
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
                (
                    cmd,
                    baml_error,
                    noise_meta,
                    gate_val,
                    baml_ok,
                    baml_log_path,
                    initial_state,
                    gate_note,
                ) = _parse_intent_all(user_intent)
                baml_span.update(
                    output={
                        "ok": baml_ok,
                        "error": baml_error,
                        "gate_type": gate_val,
                        "baml_log_path": baml_log_path,
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
            if initial_state is not None:
                engine.set_state(initial_state)
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
                baml_log_path,
                gate_note,
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
    (
        cmd,
        baml_error,
        noise_meta,
        gate_val,
        _baml_ok,
        baml_log_path,
        initial_state,
        gate_note,
    ) = _parse_intent_all(user_intent)
    fid, state, t = _run_rust_twin(cmd, n_steps, dt, initial_state=initial_state)
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
        baml_log_path,
        gate_note,
    )
