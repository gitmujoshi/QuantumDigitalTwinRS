# TwinSentry-RS — Training Guide

**Audience:** Quantum hardware / control researchers **and** software engineers building the control plane.  
**Version:** 0.1 (aligned with repo milestones 1–4)

---

## 1. Purpose of this document

This guide orients two groups on the same system:

| Audience | You will learn |
|----------|----------------|
| **Quantum developers** | What the digital twin simulates, which approximations apply, how pulses map to Hamiltonians, and how to interpret fidelity and noise fields. |
| **Software developers** | Repository layout, Rust vs Python boundaries, BAML policy contracts, Langfuse audit hooks, PyO3 FFI, and how to build and deploy. |

A short **joint** section ties language, policy, and execution together so both sides can review traces and safety outcomes.

---

## 2. Product overview (everyone)

**TwinSentry-RS** is an open digital twin for **quantum control**: natural-language intent is turned into structured pulses, validated by policy, and executed in a **deterministic Rust** simulator, with **full traceability** in Langfuse.

**Core value**

- **Safety:** Type-safe prompting and validation via **BAML** (policy enforcement point for pulse parameters).
- **Fidelity:** Fast, deterministic **2-qubit** dynamics in Rust (TDSE integration with RK4; SIMD-friendly linear algebra).
- **Auditability:** **Langfuse** (self-hosted) records intent → schema → execution → scores.

**Non-goals (current codebase)**

- Replacing full device physics (TLS, cross-talk, full calibration) — the twin is a **controlled** model for integration and policy testing.
- Network access inside the Rust simulation core — it only consumes parameters from a **queue** (SPSC-style ingress).

---

## Part A — For quantum developers

### A.1 State space and basis

- The engine tracks a **2-qubit** state in the **computational basis** with four complex amplitudes:
  - Indexing: \(\lvert b_1 b_0 \rangle\) with states \(\lvert 00 \rangle \ldots \lvert 11 \rangle\) (see `StateVector4` in `src/state.rs`).
- **Normalization:** Physical kets satisfy \(\sum_i |a_i|^2 = 1\); the twin can call **renormalize** after long runs to limit drift.

### A.2 Time evolution (what “the twin” solves)

- Dynamics follow the **Schrödinger equation** (units with \(\hbar = 1\) in code):  
  \(\mathrm{d}\psi/\mathrm{d}t = -\mathrm{i}\, H(t)\,\psi\).
- **RK4** (4th-order Runge–Kutta) advances the state over small time steps; mid-point sampling of \(H(t)\) is used in the implementation (see `src/rk4.rs`).
- **“Trotter step”** in the PRD sense here means **one RK4 sub-step** over a small \(\Delta t\), not necessarily a product-formula Trotter decomposition of a large Hamiltonian.

### A.3 Hamiltonian model (high level)

- The codebase builds a **4×4 Hermitian** \(H\) from **single-qubit** rotating-frame blocks and **tensor products** (Kronecker products of \(2\times 2\) blocks — see `src/hamiltonian.rs`).
- **Drive on qubit 0:** Rabi-style terms (detuning \(\Delta\), Rabi \(\Omega\)) scaled by **amplitude** and a reference Rabi scale (`rabi_ref_hz` in `PulseCommand`).
- **Splits / lab-frame scales:** `qubit0_split_hz`, `qubit1_split_hz` enter as Zeeman-style terms; **drive frequency** `frequency_hz` sets the rotating-frame detuning relative to those scales.
- **Not modeled in full detail:** correlated noise across gates, measurement back-action, and arbitrary multi-qubit pulses beyond the current template — extend `hamiltonian.rs` if you need richer physics.

### A.4 Pulses vs policy (BAML)

- **`QuantumPulse`** (BAML) includes: **amplitude**, **frequency_hz**, **duration_s**, **gate_type**, optional **`NoiseProfile`** (T2 / thermal as **relative** noise scales with policy caps).
- **Asserts** in BAML **reject** invalid structured outputs (hard stop).
- **Checks** record policy bands **without** always raising — useful for dashboards; **asserts** are what enforce “do not execute” in the strict sense.
- When integrating with hardware, treat BAML as the **contract**; the Rust twin consumes **`PulseCommand`** fields that the Python layer maps from approved pulses.

### A.5 Fidelity (as implemented)

- **`fidelity_ground`** in the twin is the **population of \(\lvert 00 \rangle\)**: \(|a_0|^2\). It is a **simple proxy**, not full process tomography.
- For gate benchmarking, you would extend metrics (e.g., target state overlap, RB-style sequences) in Rust or post-process in Python.

### A.6 Performance expectations

- PRD target: **sub-10 µs per RK4 step** in release builds on representative hardware — see ignored benchmark in `src/rk4.rs`. Actual numbers depend on CPU and compiler flags.

---

## Part B — For software developers

### B.1 Repository map (conceptual)

| Area | Location | Role |
|------|----------|------|
| Policy / LLM contract | `baml_src/*.baml` | Schemas, clients, `ParsePulseFromIntent` |
| Generated Python client | `baml_client/` | `baml-cli generate` — do not hand-edit |
| Rust twin (data plane) | `src/*.rs`, `Cargo.toml` | Physics, RK4, SIMD helpers, SPSC |
| PyO3 bridge | `src/bridge.rs` (feature `python`) | `TwinEngine`, `PulseCommand`, queues |
| Python package | `python/twin_sentry/` | Imports `_native`; `controller.py` orchestration |
| Entry shim | `controller.py` (repo root) | Path setup + re-exports |
| Observability stack | `docker-compose.yaml` | Self-hosted **Langfuse** + deps |
| CI | `cloudbuild.yaml` | Compose check, Rust + Python checks |

### B.2 Build: Rust

```bash
cargo fmt
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features   # PyO3 needs Python dev headers on Linux (see CI)
```

- **Feature `python`:** compiles the `twin_sentry._native` extension. macOS uses `.cargo/config.toml` linker flags for extension modules.

### B.3 Build: Python + native extension

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install maturin
maturin develop --features python
```

- **`pyproject.toml`** pins **`baml-py`** and **`langfuse`**, and configures **maturin** (`module-name = "twin_sentry._native"`, `python-source = "python"`).

### B.4 BAML workflow

1. Edit `baml_src/*.baml`.
2. Run **`baml-cli generate`** (or save via IDE extension).
3. Commit regenerated `baml_client/` if your team tracks generated code.

### B.5 Control plane: `controller.py`

- **`run_twin_pipeline(user_intent, ...)`** (see `python/twin_sentry/controller.py`):
  - Optionally wraps work in **Langfuse** spans (`baml_parse`, `rust_twin`).
  - Calls **`b.ParsePulseFromIntent`** when the LLM is configured; on failure, uses a **heuristic** pulse for demos.
  - Maps a validated pulse to **`PulseCommand`** and runs the **Rust** `TwinEngine` via the extension.
  - Emits a **numeric score** (`fidelity_ground`) via **`create_score`** when Langfuse keys are set.

### B.6 Environment variables (typical)

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | Gemini client in BAML (`baml_src/clients.baml`) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Langfuse SDK |
| `LANGFUSE_HOST` | e.g. `http://localhost:3000` or your VPC URL |
| `PYO3_PYTHON` | CI/Linux: path to `python3` for PyO3 build |

### B.7 Docker: Langfuse

- **`docker-compose.yaml`** brings up Langfuse web, worker, Postgres, ClickHouse, Redis, MinIO.
- **Before production:** rotate all default passwords / keys; restrict network exposure (VPC / firewall).

### B.8 Cloud Build

- **`cloudbuild.yaml`**: validates Compose, runs Rust **fmt/clippy/test** with **`python3-dev`** for PyO3, runs **ruff** when `pyproject.toml` exists at `_PYTHON_DIR`.

### B.9 TwinSentry Lab (Streamlit)

- **Entry:** `app/twin_lab.py` — run `streamlit run app/twin_lab.py` from the repo root after `maturin develop --features python` and `pip install` (or `pip install -e .`) for `streamlit`, `plotly`, `numpy`.
- **Purpose:** Quantum engineers can enter **natural-language** intents, use **quick presets**, tune **RK4 steps** and **dt**, view **reduced-state Bloch spheres** for qubit 0 and qubit 1, inspect **pulse / noise / BAML error** JSON, and **trace IDs** when Langfuse is configured.
- **Visualization:** `python/twin_sentry/quantum_viz.py` computes partial traces and Bloch vectors from the 4‑amplitude simulator state.

---

## 3. Joint section — End-to-end flow (review meetings)

1. **User intent** (natural language) enters the control plane.
2. **BAML** produces a **`QuantumPulse`** (or validation fails / heuristic fallback in demos).
3. **Python** maps to **`PulseCommand`** and optional **noise metadata** for Langfuse.
4. **Rust `TwinEngine`** evolves the state; **no network** inside the core.
5. **Langfuse** trace shows spans and **fidelity** score for comparison runs.

**Review checklist**

- [ ] Are BAML **asserts** aligned with lab safety limits?
- [ ] Is the **Hamiltonian** in `hamiltonian.rs` still a valid model for your experiment line?
- [ ] Are **Langfuse** environments separated (dev/staging/prod keys)?

---

## 4. Suggested hands-on exercises

### Quantum track

1. Trace how **detuning** and **Rabi** enter `hamiltonian_at` for a flat pulse.
2. Change **time step** `dt` and **step count** in `run_twin_pipeline` and observe **fidelity_ground** stability.

### Software track

1. Run **`maturin develop --features python`** and import **`TwinEngine`** from Python.
2. Start **Langfuse** via Docker Compose and run **`run_twin_pipeline`** with keys set; open the trace UI.

### Joint

1. Inject an **out-of-range** pulse in BAML tests (or manual JSON) and confirm **assert** behavior.
2. Compare **“ideal”** vs **noise metadata** in Langfuse for the same intent string (when noise profile is populated).

---

## 5. References (in-repo)

- `baml_src/quantum.baml` — policy schema  
- `src/twin.rs`, `src/rk4.rs`, `src/hamiltonian.rs` — physics + integration  
- `python/twin_sentry/controller.py` — Langfuse + orchestration  
- `docker-compose.yaml`, `cloudbuild.yaml` — ops  

---

## 6. Slide deck (PowerPoint)

- **File:** `docs/training/TwinSentry-Training-Overview.pptx` — short overview for classroom or sprint review (same themes as this guide, slide form).
- **Regenerate** after editing talking points:
  ```bash
  pip install python-pptx
  python docs/training/build_slides.py
  ```

---

## 7. Document maintenance

When milestones change (e.g., Streamlit UI, extra qubits, new gates), update this guide and the slide deck in **`docs/training/`** together so training stays consistent with the repo.
