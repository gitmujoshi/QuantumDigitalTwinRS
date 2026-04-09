"""TwinSentry-RS Python package: PyO3 `_native` extension + control-plane helpers.

Native symbols load lazily so submodules like ``quantum_viz`` and ``sample_prompts`` work
without building the extension (e.g. lightweight tests).
"""

from __future__ import annotations

__all__ = [
    "PulseCommand",
    "PulseReceiver",
    "PulseSender",
    "TwinEngine",
    "pulse_queue",
]


def __getattr__(name: str):
    if name in __all__:
        from twin_sentry import _native

        return getattr(_native, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
