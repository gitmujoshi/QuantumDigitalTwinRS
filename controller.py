"""PRD entrypoint: re-exports `python/twin_sentry/controller.py` after fixing `sys.path`."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "python"))

from twin_sentry.controller import quantum_pulse_to_command, run_twin_pipeline  # noqa: E402

__all__ = ["run_twin_pipeline", "quantum_pulse_to_command"]
