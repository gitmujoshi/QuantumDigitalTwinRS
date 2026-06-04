# Langfuse — local tracing for TwinSentry

TwinSentry sends **traces** (intent → BAML → Rust twin → fidelity score) to [Langfuse](https://langfuse.com/) when API keys are set.

## Quick start (one command)

```bash
./scripts/start_langfuse.sh
./scripts/run_twin_lab.sh
```

1. Starts the Docker stack (`docker-compose.yaml`).
2. Auto-creates org/project/user via **headless init** (`docker/langfuse.init.env`).
3. Writes `LANGFUSE_*` keys into repo `.env`.
4. Open **http://localhost:3000** (login in init file) or run from the Lab sidebar.

## What you should see

- **Twin Lab sidebar:** “Langfuse OK — traces will include a trace ID”
- After **Run digital twin:** Audit tab shows `trace_id`; link opens Langfuse UI
- **Langfuse UI:** Traces named `TwinSentry Pipeline` with spans `baml_parse`, `rust_twin`

## Environment variables

| Variable | Purpose |
|----------|---------|
| `LANGFUSE_HOST` | Default `http://localhost:3000` |
| `LANGFUSE_PUBLIC_KEY` | Project public key |
| `LANGFUSE_SECRET_KEY` | Project secret key |

Loaded from `.env` automatically (`python/twin_sentry/llm_env.py`).

## Manual setup (no headless init)

```bash
docker compose up -d
```

Create keys in the UI → Project → Settings → API Keys → add to `.env` → restart Streamlit.

## Stop / reset

```bash
docker compose down
# Full reset (deletes trace DB):
docker compose down -v
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No trace ID in UI | Keys missing → run `./scripts/start_langfuse.sh` or set `.env` |
| Sidebar: server unreachable | `docker compose ps` — wait for `langfuse-web` healthy |
| Traces never appear in UI | Restart lab after `.env` update; run pipeline once; check `docker compose logs langfuse-web` |

Default dev login (headless init only): see `docker/langfuse.init.env`.
