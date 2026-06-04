#!/usr/bin/env bash
# Start self-hosted Langfuse and write TwinSentry .env keys (headless init).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
INIT_ENV="$ROOT/docker/langfuse.init.env"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required (Docker Desktop)."
  exit 1
fi

if [[ ! -f "$INIT_ENV" ]]; then
  echo "Missing $INIT_ENV"
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$INIT_ENV"
set +a

echo "Starting Langfuse stack (first boot may take 1–2 min)…"
docker compose --env-file "$INIT_ENV" up -d

HOST="${LANGFUSE_HOST:-http://localhost:3000}"
HEALTH_URL="${HOST%/}/api/public/health"
echo "Waiting for Langfuse at $HEALTH_URL …"
for i in $(seq 1 60); do
  if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    echo "Langfuse is up."
    break
  fi
  if [[ "$i" -eq 60 ]]; then
    echo "Timed out. Check: docker compose --env-file docker/langfuse.init.env logs langfuse-web"
    exit 1
  fi
  sleep 3
done

# Write LANGFUSE_* into repo .env for TwinSentry / Streamlit
ENV_FILE="$ROOT/.env"
PK="${LANGFUSE_INIT_PROJECT_PUBLIC_KEY}"
SK="${LANGFUSE_INIT_PROJECT_SECRET_KEY}"

_write_env() {
  local key=$1 val=$2 file=$3
  if [[ -f "$file" ]] && grep -q "^${key}=" "$file" 2>/dev/null; then
    if sed --version 2>/dev/null | grep -q GNU; then
      sed -i "s|^${key}=.*|${key}=${val}|" "$file"
    else
      sed -i '' "s|^${key}=.*|${key}=${val}|" "$file"
    fi
  else
    echo "${key}=${val}" >>"$file"
  fi
}

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ROOT/.env.example" "$ENV_FILE" 2>/dev/null || touch "$ENV_FILE"
fi

_write_env LANGFUSE_HOST "http://localhost:3000" "$ENV_FILE"
_write_env LANGFUSE_PUBLIC_KEY "$PK" "$ENV_FILE"
_write_env LANGFUSE_SECRET_KEY "$SK" "$ENV_FILE"

echo ""
echo "Langfuse UI:  http://localhost:3000"
echo "Login:        ${LANGFUSE_INIT_USER_EMAIL} / ${LANGFUSE_INIT_USER_PASSWORD}"
echo ""
echo "TwinSentry .env updated:"
echo "  LANGFUSE_PUBLIC_KEY=${PK}"
echo "  LANGFUSE_SECRET_KEY=${SK}"
echo ""
echo "Restart the lab: ./scripts/run_twin_lab.sh"
