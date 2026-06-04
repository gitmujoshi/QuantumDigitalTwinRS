"""Map BAML ``gate_type`` to analog-twin initial states and pulse envelopes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from twin_sentry import PulseCommand


@dataclass(frozen=True)
class TwinSetup:
    cmd: PulseCommand
    initial_state: list[tuple[float, float]] | None
    description: str


def _state(
    c00: complex,
    c01: complex,
    c10: complex,
    c11: complex,
) -> list[tuple[float, float]]:
    return [(z.real, z.imag) for z in (c00, c01, c10, c11)]


def _ground() -> list[tuple[float, float]]:
    return _state(1.0 + 0j, 0j, 0j, 0j)


def _plus_q0() -> list[tuple[float, float]]:
    s = 1.0 / math.sqrt(2.0)
    return _state(s + 0j, 0j, s + 0j, 0j)


def _plus_q1() -> list[tuple[float, float]]:
    s = 1.0 / math.sqrt(2.0)
    return _state(s + 0j, s + 0j, 0j, 0j)


def _one_q0() -> list[tuple[float, float]]:
    return _state(0j, 0j, 1.0 + 0j, 0j)


def apply_gate_mapping(cmd: PulseCommand, gate_type: str | None) -> TwinSetup:
    """
    Adjust ``PulseCommand`` and optional initial |ψ⟩ for the Rust TDSE twin.

    The analog twin has a transverse drive on qubit 0; gates are approximated via
    resonance / detuning / π-pulse amplitudes and selected initial states.
    """
    gt = (gate_type or "ROTATION").upper()
    fq = float(cmd.frequency_hz)
    amp = float(cmd.amplitude)

    if gt == "HADAMARD":
        return TwinSetup(
            cmd=_replace(
                cmd,
                amplitude=max(amp, 0.5),
                qubit0_split_hz=fq,
            ),
            initial_state=_plus_q0(),
            description="HADAMARD → |+⟩₀ initial + resonant drive on q0",
        )

    if gt == "X":
        return TwinSetup(
            cmd=_replace(cmd, amplitude=min(1.0, max(amp, 0.88)), qubit0_split_hz=fq),
            initial_state=_ground(),
            description="X → resonant π-pulse on q0 (bit-flip target)",
        )

    if gt == "Y":
        return TwinSetup(
            cmd=_replace(cmd, amplitude=min(1.0, max(amp, 0.85)), qubit0_split_hz=fq),
            initial_state=_plus_q0(),
            description="Y → drive from |+⟩₀ initial state (Y approximated in lab frame)",
        )

    if gt in ("Z", "PHASE"):
        return TwinSetup(
            cmd=_replace(
                cmd,
                amplitude=min(amp, 0.12),
                qubit0_split_hz=fq + 40e6,
            ),
            initial_state=_ground(),
            description=f"{gt} → detuned weak drive (phase accumulation on q0)",
        )

    if gt == "CNOT":
        return TwinSetup(
            cmd=_replace(cmd, amplitude=min(1.0, max(amp, 0.75)), qubit0_split_hz=fq),
            initial_state=_one_q0(),
            description="CNOT (demo) → |10⟩ initial + strong q0 drive (2Q toy; not full CX)",
        )

    if gt == "CUSTOM":
        return TwinSetup(
            cmd=cmd,
            initial_state=None,
            description="CUSTOM → pulse as parsed (no gate preset)",
        )

    # ROTATION and unknown
    return TwinSetup(
        cmd=_replace(cmd, amplitude=amp, qubit0_split_hz=fq),
        initial_state=None,
        description="ROTATION → resonant drive, |00⟩ initial",
    )


def _replace(cmd: PulseCommand, **kwargs: Any) -> PulseCommand:
    return PulseCommand(
        amplitude=kwargs.get("amplitude", cmd.amplitude),
        frequency_hz=kwargs.get("frequency_hz", cmd.frequency_hz),
        duration_s=kwargs.get("duration_s", cmd.duration_s),
        qubit0_split_hz=kwargs.get("qubit0_split_hz", cmd.qubit0_split_hz),
        qubit1_split_hz=kwargs.get("qubit1_split_hz", cmd.qubit1_split_hz),
        rabi_ref_hz=kwargs.get("rabi_ref_hz", cmd.rabi_ref_hz),
    )
