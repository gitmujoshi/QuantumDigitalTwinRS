# QuantumDigitalTwinRS (Portfolio Repo)

This repo contains **three quantum-focused workstreams** (each with a PRD and runnable demos):

- **TwinSentry-RS**: digital twin control plane for quantum pulses (**BAML** policy, **Rust** 2‑qubit TDSE + RK4 simulation, **Langfuse** audit, **PyO3** bridge, Streamlit lab).
- **AeroQ**: hybrid quantum‑classical **CFD acceleration** scaffold (HAL routing, linear-system kernel foundation, optional BAML hooks).
- **Post‑Quantum Crypto Readiness**: PQC migration and “quantum‑safe” engineering demo (hybrid handshake/signature concepts + crypto‑agility).

If you want the fastest “try everything” path, run the **Projects Lab UI** (`app/projects_lab.py`) and pick a project in the sidebar.

## Quick start

**Rust**

```bash
cargo test --all-features
```

**Python tests** (from repo root; native extension tests need `maturin develop --features python`):

```bash
pip install pytest ruff
ruff check . && ruff format --check .
pytest -q tests/
```

**Python extension** (requires Python 3.11+)

```bash
python -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop --features python
```

Set `GOOGLE_API_KEY` for BAML/Gemini and optional `LANGFUSE_*` keys for tracing.

**Optional — real / cloud simulators:** after policy + twin, you can map the approved pulse to a **gate circuit** and run it with **Qiskit Aer** (local) or **IBM Quantum** (account token). Install `pip install 'twinsentry-rs[quantum-cloud]'` or `'twinsentry-rs[ibm-quantum]'` and see [Quantum cloud backends](docs/quantum-cloud-backends.md).

## Projects Lab (Streamlit UI)

Single UI to run the core demo use cases for **TwinSentry**, **AeroQ**, and **Post‑Quantum Crypto**.

```bash
pip install streamlit numpy pyyaml cryptography
streamlit run app/projects_lab.py
```

## TwinSentry Lab (Streamlit UI)

Interactive R&D console: natural-language commands, presets (Hadamard, π-pulse, noise, safety demo), extra **sample prompts** in the sidebar (`python/twin_sentry/sample_prompts.py`), dual **Bloch spheres** (reduced ρ for each qubit), metrics, and audit tabs.

```bash
pip install -e .   # or: pip install streamlit plotly numpy
maturin develop --features python
streamlit run app/twin_lab.py
```

Open the local URL shown in the terminal (default `http://localhost:8501`).

## AeroQ (sub-project)

The `AeroQ/` folder is a separate, installable Python project scaffold.

```bash
cd AeroQ
python -m venv .venv
./.venv/bin/pip install -U pip
./.venv/bin/pip install -e ".[dev]"
./.venv/bin/python scripts/smoke_kernel.py
./.venv/bin/python -m pytest -q
```

## Docs

- [Quantum engineering fundamentals](docs/training/Quantum-Engineering-Fundamentals.md) — background for quantum engineers (states, gates, noise, control, link to TwinSentry)  
- [Training guide](docs/training/TwinSentry-Training-Guide.md) — quantum & software tracks  
- [Sample quantum prompts](docs/sample-quantum-prompts.md) — every preset and test intent (copy-paste reference)  
- [Quantum cloud backends](docs/quantum-cloud-backends.md) — Aer + IBM Quantum (optional gate-circuit path)  
- PRDs:
  - [TwinSentry Digital Twin PRD](docs/prd/TwinSentry-Digital-Twin-PRD.md)
  - [AeroQ Consolidated PRD (v3.0)](docs/prd/AeroQ-Consolidated-PRD-v3.0.md)
  - [Post‑Quantum Crypto Readiness PRD](docs/prd/Post-Quantum-Crypto-Project-PRD.md)
- Portfolio:
  - [Quantum Resume (Portfolio)](docs/Quantum-Resume-Portfolio.md)
- Infrastructure: `docker-compose.yaml` (Langfuse), `cloudbuild.yaml` (CI)

## License

MIT OR Apache-2.0 (see `Cargo.toml`).
