# PRD — TwinSentry Digital Twin Control Plane (v0.1)

**Status:** Draft  
**Scope:** TwinSentry-RS (this repo)  
**Last updated:** 2026-05-05

---

## 1. Executive summary

TwinSentry-RS is a **digital twin control plane for quantum pulses**. It converts **natural-language intent** into **structured pulse parameters** using **BAML** (typed policy + validation), executes those parameters in a **deterministic Rust 2‑qubit simulator** (TDSE integration via RK4), and records end-to-end **audit traces** in **Langfuse**.

The product is intentionally engineered as a **safe integration sandbox**: policy and orchestration are exercised without requiring real hardware access, while remaining structured enough to later connect to vendor SDKs.

---

## 2. Problem statement

Quantum control workflows commonly suffer from:

- **Unstructured intent → unsafe parameters**: free-form prompting can yield pulses outside lab safety bounds.
- **Low reproducibility**: interactive tuning without deterministic execution makes debugging hard.
- **Weak auditability**: it’s hard to prove what intent produced which parameters, which run, and which score.

TwinSentry-RS addresses this by making **policy the enforcement point**, **simulation deterministic**, and **tracing first-class**.

---

## 3. Goals

| ID | Goal |
|---|---|
| G1 | Convert NL intent to a **typed pulse contract** with hard validation gates (BAML asserts). |
| G2 | Execute approved pulses in a **deterministic Rust twin** (2 qubits, TDSE + RK4). |
| G3 | Produce **interpretable outputs**: fidelity proxy, state snapshots, noise metadata (if supplied). |
| G4 | Provide **auditability**: trace intent → schema → execution → score in Langfuse. |
| G5 | Provide an **interactive UI** (Streamlit) for demos, presets, and review meetings. |
| G6 | Keep a clean path to optional **cloud backends** (gate-circuit mapping) for integration testing. |

---

## 4. Non-goals

- **Full device physics**: calibration pipelines, cross-talk models, measurement models, and pulse-level vendor execution are out of scope for the current twin.
- **Large‑N simulation**: the current simulator targets a **2‑qubit** state.
- **Networked simulation core**: the Rust twin is intentionally isolated; it consumes inputs from an in-process queue.
- **Security productization**: secrets management, multi-tenant auth, and hardened deployment are not primary MVP goals.

---

## 5. Primary users

- **Quantum control / hardware engineers**: test pulse envelopes, interpret state evolution, sanity-check metrics.
- **Software/control-plane engineers**: integrate policy, tracing, CI, and (later) hardware adapters.

---

## 6. User experience / workflows

### 6.1 “Intent to run” (happy path)

1. User enters **natural-language intent** (UI or API).
2. **BAML** produces a structured **`QuantumPulse`** (policy asserts enforce safe ranges).
3. Python maps validated pulse to Rust **`PulseCommand`** and attaches optional noise metadata.
4. Rust **`TwinEngine`** simulates evolution over \(n\) steps of size \(\Delta t\).
5. The pipeline outputs a **fidelity proxy** and state snapshots; Langfuse records spans + score when configured.

### 6.2 “Policy rejection / fallback” (demo mode)

- If BAML is not configured (no key) or parsing fails, the demo pipeline may fall back to a heuristic pulse generator (useful for UI demos), while still surfacing the BAML error.

---

## 7. Functional requirements

### 7.1 Policy / contract (BAML)

- Provide BAML schemas for pulses, including:
  - amplitude, frequency, duration, gate_type
  - optional noise profile fields (relative scales) with caps
- Support **hard enforcement** via asserts and **dashboard-friendly checks**.
- Generated client code is version-pinned and reproducible.

### 7.2 Simulation (Rust digital twin)

- Deterministic 2‑qubit TDSE integration:
  - RK4 stepping over a time-varying Hamiltonian template
  - periodic renormalization to limit numerical drift
- Produce output metrics:
  - fidelity proxy (currently population of \(|00\rangle\))
  - state vector snapshots usable for visualization/post-processing

### 7.3 Orchestration (Python)

- Provide a single entrypoint function for end-to-end runs (intent → result payload).
- Attach Langfuse traces/spans/scores when `LANGFUSE_*` keys exist.
- Keep cloud submission optional and failure-tolerant (never block simulation output).

### 7.4 UI (Streamlit)

- Interactive lab console:
  - text intent input + presets
  - controls for RK4 step count and dt
  - visualization of reduced-state Bloch spheres (per qubit)
  - inspection of pulse/noise/BAML error JSON
  - trace IDs when available

---

## 8. Observability and audit

- Langfuse spans should cover at minimum:
  - BAML parse/validation
  - Rust twin execution
  - optional cloud backend submission (if enabled)
- Key output artifacts:
  - trace_id, inputs (intent), validated pulse fields, execution params, score(s)

---

## 9. Performance & reliability targets (MVP)

- Deterministic simulation runs suitable for CI and demos.
- Target performance directionally: **sub‑10 µs per RK4 step** in release builds on representative developer hardware (benchmark-guided).

---

## 10. Success criteria (demo-ready)

- Given a set of sample prompts/presets, the system can:
  - produce structured pulses (or clearly show policy rejection),
  - simulate and return a fidelity proxy + state,
  - display results in the Streamlit lab,
  - optionally emit Langfuse traces when configured.

---

## 11. Architecture (current)

| Layer | Implementation | Location |
|---|---|---|
| Policy / LLM contract | BAML schemas + client config | `baml_src/*.baml` |
| Generated policy client | Python generated code | `baml_client/` |
| Data plane simulation | Rust 2‑qubit twin + RK4 | `src/` |
| Bridge | PyO3 extension module | `src/bridge.rs` (feature `python`) |
| Control plane | Orchestration + tracing | `python/twin_sentry/controller.py` |
| UI | Streamlit Lab | `app/twin_lab.py` |
| Observability | Langfuse (self-hosted) | `docker-compose.yaml` |

---

## 12. Future work (explicitly out of MVP)

- Extend metrics beyond `fidelity_ground` (target overlap, process metrics, RB-style evaluation).
- More expressive Hamiltonians / couplings, additional qubits.
- Hardware-grade export paths: calibration-aware transpilation, OpenPulse/pulse-level backends.
- Stronger safety framework: policy versioning, signed configs, environment separation by default.

