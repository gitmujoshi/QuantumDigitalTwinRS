from __future__ import annotations

from typing import Any


def draft_linear_solve_plan(intent: str) -> dict[str, Any] | None:
    """
    Optional BAML-backed helper.

    Returns a dict-like `LinearSolvePlan` if BAML is installed + generated client exists + key is set.
    Returns None if BAML isn't available (so AeroQ stays runnable without LLMs).
    """
    try:
        from baml_client import b  # type: ignore
    except Exception:
        return None

    try:
        plan = b.DraftLinearSolvePlan(intent)
    except Exception:
        return None

    # The generated type is pydantic-like; normalize to plain dict for callers.
    try:
        return plan.model_dump()  # pydantic v2
    except Exception:
        try:
            return plan.dict()  # pydantic v1 fallback
        except Exception:
            return {"plan": plan}

