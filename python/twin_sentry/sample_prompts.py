"""
Sample natural-language intents for testing BAML + the digital twin.

Use in tests, notebooks, or TwinSentry Lab (see `app/twin_lab.py`).
"""

from __future__ import annotations

# Sidebar quick actions in the Streamlit app (short labels → full intent)
SIDEBAR_PRESETS: dict[str, str] = {
    "Hadamard": (
        "Apply a Hadamard-style superposition pulse on qubit 0 with moderate amplitude "
        "and 5 GHz drive, duration 80 nanoseconds, ideal (no noise)."
    ),
    "Pi pulse": (
        "Apply a pi pulse on qubit 0 for a bit-flip style rotation, amplitude about 0.45, "
        "5 GHz, 80 ns duration."
    ),
    "Noise stress test": (
        "Stress test with elevated digital-twin noise: T2 dephasing relative 0.08 and "
        "thermal jitter relative 0.07, amplitude 0.3, 5 GHz."
    ),
    "Safety violation (demo)": (
        "Unsafe operating point: request amplitude 1.5 on the drive (policy stress test)."
    ),
}

# Extended catalog for dropdown / copy-paste testing (label → full intent)
SAMPLE_PROMPTS: list[tuple[str, str]] = [
    # --- Baseline & single-qubit style ---
    (
        "Small-angle rotation (q0)",
        "Apply a small rotation on qubit 0: amplitude 0.15, drive 5 GHz, duration 50 ns, no noise.",
    ),
    (
        "Z-like phase emphasis",
        "Prepare a pulse with amplitude 0.25, 5 GHz, 100 ns duration, gate type PHASE, ideal twin (no noise profile).",
    ),
    (
        "Pauli-X style bit-flip",
        "Execute an X-style pulse on qubit 0: amplitude 0.48, frequency 5 GHz, duration 80 ns, minimal noise.",
    ),
    # --- Noise & digital twin ---
    (
        "Mild T2 dephasing only",
        "Digital twin with T2 dephasing relative 0.03 and no thermal jitter, amplitude 0.35, 5 GHz, 80 ns.",
    ),
    (
        "Thermal jitter only",
        "Pulse with thermal jitter relative 0.05 and T2 dephasing relative 0.02, amplitude 0.4, 5 GHz.",
    ),
    (
        "High noise (under 10% caps)",
        "Noise stress: T2 dephasing relative 0.09 and thermal jitter relative 0.09, amplitude 0.25, 5 GHz drive.",
    ),
    # --- Frequency / duration wording ---
    (
        "Different drive frequency",
        "Calibrate a pulse at 4.8 GHz on qubit 0, amplitude 0.33, duration 60 nanoseconds, ideal conditions.",
    ),
    (
        "Longer envelope",
        "Use a longer 200 ns duration pulse, amplitude 0.2, 5 GHz, qubit 0, no noise.",
    ),
    # --- Policy & edge cases ---
    (
        "At-amplitude boundary",
        "Set amplitude exactly 0.95 for a 5 GHz pi-style pulse on qubit 0, 90 ns, no noise.",
    ),
    (
        "Ambiguous multi-qubit wording",
        "We need a CUSTOM gate pulse for calibration: amplitude 0.4, 5 GHz, 100 ns, optional small noise.",
    ),
    (
        "Explicit no noise",
        "Ideal unitary evolution only: amplitude 0.5, 5 GHz, 80 ns, omit noise profile entirely.",
    ),
    # --- Stress / regression ---
    (
        "Empty-sounding but valid",
        "Short pulse on q0: amplitude 0.1, 5e9 Hz, 20 ns.",
    ),
    (
        "Keywords: CNOT + rotation",
        "Describe a ROTATION class pulse for single-qubit calibration at 5 GHz, amplitude 0.38, 75 ns, low noise.",
    ),
]


def prompts_by_label() -> dict[str, str]:
    """Flat map from dropdown label to prompt text."""
    return dict(SAMPLE_PROMPTS)
