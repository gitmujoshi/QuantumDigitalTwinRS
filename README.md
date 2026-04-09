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

## TwinSentry Lab (Streamlit UI)

Interactive R&D console: natural-language commands, presets (Hadamard, π-pulse, noise, safety demo), dual **Bloch spheres** (reduced ρ for each qubit), metrics, and audit tabs.

```bash
pip install -e .   # or: pip install streamlit plotly numpy
maturin develop --features python
streamlit run app/twin_lab.py
```

Open the local URL shown in the terminal (default `http://localhost:8501`).

## Docs

- [Training guide](docs/training/TwinSentry-Training-Guide.md) — quantum & software tracks  
- Infrastructure: `docker-compose.yaml` (Langfuse), `cloudbuild.yaml` (CI)

## License

MIT OR Apache-2.0 (see `Cargo.toml`).
