"""Ollama / BAML environment defaults and optional `.env` loading."""

from __future__ import annotations

__all__ = ["configure_ollama_for_baml", "configure_app_env", "langfuse_status", "ollama_status"]

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def configure_app_env(repo_root: Path | None = None) -> None:
    """Load `.env` and apply defaults for Ollama, BAML logs, and Langfuse host."""
    root = repo_root or Path(__file__).resolve().parents[2]
    _load_dotenv(root / ".env")

    os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    os.environ.setdefault("OLLAMA_MODEL", "llama3.1:latest")
    os.environ.setdefault("OLLAMA_API_KEY", "ollama")
    os.environ.setdefault("LANGFUSE_HOST", "http://localhost:3000")

    os.environ.setdefault("BAML_LOG", "INFO")
    os.environ.setdefault("BAML_LOG_SAVE", "true")


def configure_ollama_for_baml(repo_root: Path | None = None) -> None:
    """Backward-compatible alias for ``configure_app_env``."""
    configure_app_env(repo_root)


def langfuse_status() -> dict[str, str | bool]:
    """Check whether Langfuse tracing can run (keys + reachable host)."""
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000").rstrip("/")
    if not pk or not sk:
        return {
            "ok": False,
            "host": host,
            "error": "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env (see .env.example)",
        }
    try:
        with urllib.request.urlopen(f"{host}/api/public/health", timeout=2.0) as resp:
            code = resp.status
            healthy = code == 200
        return {
            "ok": healthy,
            "host": host,
            "keys_set": True,
            "error": None if healthy else f"Langfuse at {host} returned HTTP {code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {
            "ok": False,
            "host": host,
            "keys_set": True,
            "error": f"Cannot reach Langfuse at {host}: {e}",
        }


def ollama_status() -> dict[str, str | bool]:
    """Quick health check for the sidebar (does not load models)."""
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    root = base.removesuffix("/v1") if base.endswith("/v1") else base
    model = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")
    try:
        with urllib.request.urlopen(f"{root}/api/tags", timeout=2.0) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        names = {m.get("name", "") for m in payload.get("models", [])}
        has_model = model in names or any(n.startswith(model.split(":")[0]) for n in names)
        return {
            "ok": True,
            "base_url": base,
            "model": model,
            "model_ready": has_model,
            "models": ", ".join(sorted(names)[:4]) + ("…" if len(names) > 4 else ""),
        }
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "base_url": base, "model": model, "error": str(e)}
