# Quantum Computing Resume (Portfolio)

**Name:** Your Name  
**Location:** Your City, State (Remote OK)  
**Email:** you@email.com · **GitHub:** github.com/your-handle · **LinkedIn:** linkedin.com/in/your-handle

---

## Summary

Builder of **hybrid quantum-classical systems** with a focus on **reproducibility, safety/policy enforcement, and developer experience**. Delivered working prototypes spanning:

- **Quantum control digital twins** (pulse policy → deterministic simulation → audit traces)
- **Quantum acceleration for CFD** (QSVT/QAOA/QML architecture + hardware abstraction)
- **Post-quantum cryptography readiness** (threat modeling, migration patterns, crypto-agility)

---

## Core skills

- **Quantum**: control concepts (pulses vs gates), Hamiltonians, TDSE simulation, fidelity/metrics, QSVT (linear systems), QAOA (partition/optimization), variational circuits, QA‑PINNs (physics-informed ML)
- **Hybrid systems**: hardware abstraction layers, simulator vs QPU routing, deterministic sandboxes for integration testing
- **Policy & safety**: typed prompting/contracts (BAML), parameter validation bands, “approved action” workflows
- **Observability**: trace-driven development, structured spans/scores (Langfuse)
- **Software**: Python, Rust, PyO3, Streamlit, CI/CD, Docker

---

## Selected projects

### TwinSentry-RS — Quantum control digital twin control plane

**What it is**: An end-to-end stack that turns **natural-language intent** into a **structured pulse contract**, validates it, simulates it in a **deterministic Rust twin**, and produces **auditable traces** and an interactive UI.

**Highlights**
- **Typed policy contract (BAML)**: structured `QuantumPulse` outputs with validation/guards for pulse parameters and noise metadata.
- **Deterministic Rust simulator**: **2‑qubit TDSE** evolution using **RK4**, designed for reproducible runs and CI.
- **Python orchestration + PyO3 bridge**: clean boundary between control plane and the simulation “data plane.”
- **Observability-first**: optional **Langfuse** tracing: intent → parse → simulation → score.
- **Streamlit Lab UI**: interactive presets, parameter controls, and per-qubit visualization (reduced state / Bloch spheres).
- **Optional cloud backends**: gate-circuit mapping path for Aer / IBM Quantum integration testing.

**Use cases enabled**
- Safety/policy rehearsal for quantum labs, parameter validation testing, reproducible control experiments, demoable audit trails.

---

### AeroQ — Hybrid quantum-classical acceleration for aerospace CFD (PRD-driven MVP)

**What it is**: A product architecture and MVP scaffold for solving the **CFD simulation wall** using hybrid compute: quantum linear solvers (QSVT), optimization (Iterative‑QAOA), and real-time surrogate modeling (QA‑PINNs).

**Highlights**
- **Hardware Abstraction Layer (HAL)**: one interface routing between **GPU simulators (PennyLane)** and **IBM Runtime (Qiskit)** backends.
- **Linear system kernel**: `solve_linear_system(A, b)` routed by configuration to support local/remote backends (MVP foundation for QSVT).
- **Planned QML dashboard**: surrogate designer concept for instant lift/drag prediction while iterating on geometry.
- **BAML-ready**: optional typed LLM interface for generating plans/configuration and keeping AI assistance auditable.

**Use cases enabled**
- Hybrid quantum-classical workflow prototyping, backend switching for demos, early-stage benchmarking hooks and dashboard iteration.

---

### Post-Quantum Crypto Readiness — PQC migration and “quantum-safe” engineering

**What it is**: A standalone PRD and engineering plan for helping teams migrate from vulnerable public-key cryptography to **post-quantum** alternatives with clear scope, threat models, and operational patterns.

**Highlights**
- **Threat model clarity**: Shor vs Grover impacts; “harvest now, decrypt later” prioritization for long-lived secrets.
- **Migration patterns**: crypto-agility, hybrid deployments, key lifecycle + algorithm/version identifiers.
- **Engineering discipline**: explicit non-goals and separation from unrelated quantum simulation workstreams.

**Use cases enabled**
- Security architecture planning, engineering enablement, PQC adoption roadmaps, and reference implementation planning.

---

## Technical stack

- **Languages**: Python, Rust
- **Frameworks/SDKs**: Streamlit, Plotly, PyO3, Qiskit (IBM Runtime), PennyLane (GPU simulator path)
- **Policy/LLM**: BAML (typed contracts)
- **Ops/CI**: Docker Compose, Cloud Build-style CI, test + lint automation
- **Observability**: Langfuse tracing (self-hosted)

---

## Metrics & “proof” artifacts (portfolio-ready)

- **Reproducible twin runs**: deterministic simulation outputs and trace IDs (when enabled).
- **Backend toggles**: simulator ↔ cloud routing patterns usable across projects.
- **Demo UIs**: Streamlit labs for interactive validation and storytelling to engineers and stakeholders.

---

## Education / publications

Add as applicable: degree(s), coursework, papers, patents, talks, open-source contributions.

