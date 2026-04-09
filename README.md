# TwinSentry-RS

Digital twin control plane for quantum pulses: **BAML** policy, **Rust** simulation (2-qubit TDSE + RK4), **Langfuse** audit, **PyO3** bridge, and **GCP** CI.

## Quick start

**Rust**

```bash
cargo test --all-features
```

**Python extension** (requires Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop --features python
```

Set `GOOGLE_API_KEY` for BAML/Gemini and optional `LANGFUSE_*` keys for tracing.

## Docs

- [Training guide](docs/training/TwinSentry-Training-Guide.md) — quantum & software tracks  
- Infrastructure: `docker-compose.yaml` (Langfuse), `cloudbuild.yaml` (CI)

## License

MIT OR Apache-2.0 (see `Cargo.toml`).
