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

**Optional — real / cloud simulators:** after policy + twin, you can map the approved pulse to a **gate circuit** and run it with **Qiskit Aer** (local) or **IBM Quantum** (account token). Install `pip install 'twinsentry-rs[quantum-cloud]'` or `'twinsentry-rs[ibm-quantum]'` and see [Quantum cloud backends](docs/quantum-cloud-backends.md).

## TwinSentry Lab (Streamlit UI)

Interactive R&D console: natural-language commands, presets (Hadamard, π-pulse, noise, safety demo), extra **sample prompts** in the sidebar (`python/twin_sentry/sample_prompts.py`), dual **Bloch spheres** (reduced ρ for each qubit), metrics, and audit tabs.

```bash
pip install -e .   # or: pip install streamlit plotly numpy
maturin develop --features python
streamlit run app/twin_lab.py
```

Open the local URL shown in the terminal (default `http://localhost:8501`).

## Docs

- [Quantum engineering fundamentals](docs/training/Quantum-Engineering-Fundamentals.md) — background for quantum engineers (states, gates, noise, control, link to TwinSentry)  
- [Training guide](docs/training/TwinSentry-Training-Guide.md) — quantum & software tracks  
- [Sample quantum prompts](docs/sample-quantum-prompts.md) — every preset and test intent (copy-paste reference)  
- [Quantum cloud backends](docs/quantum-cloud-backends.md) — Aer + IBM Quantum (optional gate-circuit path)  
- Infrastructure: `docker-compose.yaml` (Langfuse), `cloudbuild.yaml` (CI)

## License

MIT OR Apache-2.0 (see `Cargo.toml`).
