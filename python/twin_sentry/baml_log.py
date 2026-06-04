"""Persist structured BAML / LLM call logs (Collector API) to disk."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import baml_py.baml_py as baml_py


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    raw = os.environ.get("BAML_LOG_DIR", "logs/baml")
    p = Path(raw)
    return p if p.is_absolute() else root / p


def save_enabled() -> bool:
    v = os.environ.get("BAML_LOG_SAVE", "true").strip().lower()
    return v not in ("0", "false", "no", "off")


def configure_baml_console_logging() -> None:
    """Mirror BAML runtime logs to stderr (prompt, reply, timing)."""
    os.environ.setdefault("BAML_LOG", "INFO")


def new_collector(name: str = "twin_sentry") -> baml_py.Collector:
    return baml_py.Collector(name)


def _http_body_dict(body: Any) -> dict[str, Any] | str | None:
    if body is None:
        return None
    text = getattr(body, "text", None)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _http_part(http: Any) -> dict[str, Any] | None:
    if http is None:
        return None
    headers = getattr(http, "headers", None)
    if isinstance(headers, str):
        try:
            headers = json.loads(headers)
        except json.JSONDecodeError:
            pass
    return {
        "id": getattr(http, "id", None),
        "url": getattr(http, "url", None),
        "method": getattr(http, "method", None),
        "status": getattr(http, "status", None),
        "headers": headers,
        "body": _http_body_dict(getattr(http, "body", None)),
    }


def _usage_dict(usage: Any) -> dict[str, Any] | None:
    if usage is None:
        return None
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "cached_input_tokens": getattr(usage, "cached_input_tokens", None),
    }


def _timing_dict(timing: Any) -> dict[str, Any] | None:
    if timing is None:
        return None
    return {
        "start_time_utc_ms": getattr(timing, "start_time_utc_ms", None),
        "duration_ms": getattr(timing, "duration_ms", None),
    }


def _llm_call_dict(call: Any) -> dict[str, Any]:
    return {
        "provider": getattr(call, "provider", None),
        "client_name": getattr(call, "client_name", None),
        "selected": getattr(call, "selected", None),
        "usage": _usage_dict(getattr(call, "usage", None)),
        "timing": _timing_dict(getattr(call, "timing", None)),
        "http_request": _http_part(getattr(call, "http_request", None)),
        "http_response": _http_part(getattr(call, "http_response", None)),
    }


def function_log_record(
    log: Any,
    *,
    user_intent: str,
    ok: bool,
    error: str | None = None,
) -> dict[str, Any]:
    calls = [_llm_call_dict(c) for c in getattr(log, "calls", []) or []]
    selected = getattr(log, "selected_call", None)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "error": error,
        "user_intent": user_intent,
        "function_name": getattr(log, "function_name", None),
        "function_log_id": getattr(log, "id", None),
        "log_type": getattr(log, "log_type", None),
        "metadata": dict(getattr(log, "metadata", None) or {}),
        "raw_llm_response": getattr(log, "raw_llm_response", None),
        "timing": _timing_dict(getattr(log, "timing", None)),
        "usage": _usage_dict(getattr(log, "usage", None)),
        "selected_call": _llm_call_dict(selected) if selected is not None else None,
        "calls": calls,
    }


def persist_collector(
    collector: baml_py.Collector | None,
    user_intent: str,
    *,
    ok: bool,
    error: str | None = None,
    repo_root: Path | None = None,
) -> str | None:
    """
    Append one JSON line per function log and write a pretty JSON snapshot for the last call.

    Returns path to the per-call JSON file, or None if logging disabled / empty.
    """
    if collector is None or not save_enabled():
        return None

    logs = list(getattr(collector, "logs", []) or [])
    if not logs and collector.last is None:
        return None

    out_dir = log_dir(repo_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = out_dir / "baml_calls.jsonl"
    last_file: Path | None = None

    for log in logs:
        record = function_log_record(log, user_intent=user_intent, ok=ok, error=error)
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

        fid = record.get("function_log_id") or "unknown"
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        last_file = out_dir / f"{ts}_{fid}.json"
        last_file.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")

    return str(last_file) if last_file else str(jsonl_path)
