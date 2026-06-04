#!/usr/bin/env bash
# Start TwinSentry Lab with venv, Ollama env, and native extension.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Missing .venv — create: python3 -m venv .venv && source .venv/bin/activate && pip install -e . maturin"
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434/v1}"
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.1:latest}"
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-ollama}"

if ! curl -sf "${OLLAMA_BASE_URL%/v1}/api/tags" >/dev/null 2>&1; then
  echo "Ollama not running. Start in another terminal: ollama serve"
fi

if [[ -z "${LANGFUSE_PUBLIC_KEY:-}" || -z "${LANGFUSE_SECRET_KEY:-}" ]]; then
  echo "Langfuse: off (no LANGFUSE_* in .env). Enable: ./scripts/start_langfuse.sh"
elif ! curl -sf "${LANGFUSE_HOST:-http://localhost:3000}/api/public/health" >/dev/null 2>&1; then
  echo "Langfuse keys set but server down. Run: ./scripts/start_langfuse.sh"
fi

maturin develop --features python -q
echo "TwinSentry Lab → http://localhost:8501"
echo "  Pages sidebar →「Materials and Logistics」for real-world Examples 1 & 2"
exec streamlit run app/twin_lab.py --server.port 8501
