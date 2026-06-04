# MatrixQ vs Portfolio PRDs — Comparison

**Purpose:** Position the imported **MatrixQ Sandbox Platform** PRD (v1.0.0) against the PRDs already represented in **QuantumDigitalTwinRS** (TwinSentry, AeroQ, PQC).  
**Audience:** Product, R&D leads, and engineers deciding what to build in this repo vs a separate MatrixQ line.  
**Last updated:** 2026-05-20 (includes FR-4.1.x / FR-4.2.x and design doc)

---

## 1. At a glance

| Dimension | **MatrixQ** (imported) | **TwinSentry** (this repo) | **AeroQ** (sandbox in repo) | **PQC readiness** (demo in repo) |
|-----------|------------------------|----------------------------|-----------------------------|----------------------------------|
| **Primary job** | Serverless QASM verification + industrial HPC sandboxes | NL → safe pulses → deterministic twin + audit | Hybrid CFD / mesh / QSVT acceleration | Crypto migration education + agility patterns |
| **Core artifact** | OpenQASM 3.0 circuits, noise maps | `QuantumPulse` + Rust TDSE state | Linear systems, OSSLBM, QSVT narrative | KEM/signature hybrids, transcripts |
| **Hero persona** | Materials scientist + supply-chain VP | Control-plane / pulse engineers | Aerospace CFD + platform engineers | Security / platform engineers |
| **Local LLM mandate** | Explicit (Ollama, zero-cost prototyping) | Implemented (`llm_env.py`, Ollama → BAML) | Not central to PRD | Not central |
| **UI paradigm** | Workspace + web routes (implied) | Streamlit Twin Lab / Projects Lab | Streamlit AeroQ tabs | Streamlit PQC panel |
| **Hardware stance** | Hardware-agnostic, serverless scale-out | 2-qubit twin; optional mock/real cloud gates | HAL: PennyLane AMD vs IBM | Classical + PQC libs (future) |
| **Maturity in repo** | Reference PRD + design doc | **Shipping** (Rust + BAML + UI) | Scaffold + OSSLBM demo | Readiness demo + PRD |
| **Target KPI** | VQE: 3 weeks → &lt;4 min; QAOA: hours → sub-minute | Demo fidelity + trace audit | CFD speedup narrative (PRD) | Migration clarity |

---

## 2. Vision overlap and divergence

### Overlap (same portfolio thesis)

- **Sandbox before production spend:** MatrixQ’s “zero-cost prototyping” and TwinSentry’s mock backends / deterministic twin both defer expensive hardware until logic is validated.
- **Hybrid quantum–classical:** MatrixQ VQE materials block and AeroQ’s QSVT/QA-PINN both assume classical orchestration around quantum kernels.
- **AI-assisted engineering:** MatrixQ names Cursor + Claude Code; this repo already uses Cursor-style workflows, BAML policy, and Ollama for local inference.
- **Auditability & ops narrative:** TwinSentry’s Langfuse traces and MatrixQ’s “verification workbench” both sell **evidence** to stakeholders, not just raw simulation.

### Divergence (different centers of gravity)

| MatrixQ emphasizes | This repo emphasizes |
|--------------------|----------------------|
| **OpenQASM 3.0** as the interchange language | **Natural language → typed pulse contract** (BAML asserts) |
| **Materials VQE** and **logistics optimization** personas | **Pulse control / TDSE** and **CFD** (AeroQ) personas |
| **Serverless auto-scaling** classical networks | **In-process Rust twin** + optional single-node cloud submit |
| **Topology + noise profile mapping** at circuit scale | **Gate mapping** from policy + **domain mocks** (weather, drug, QPU vendor) |

**Takeaway:** MatrixQ reads like a **horizontal verification platform**; TwinSentry is a **vertical control-plane twin**. They can coexist: MatrixQ could consume **exported QASM** from TwinSentry’s cloud path, while TwinSentry could treat MatrixQ as an external verifier.

---

## 3. Persona mapping

| MatrixQ persona | Closest portfolio fit | Gap |
|-----------------|----------------------|-----|
| Dr. Helena Vance (materials / VQE) | **Drug discovery mock** + future chemistry stubs in `domain_mocks` | No production VQE engine or OpenQASM materials pipeline in repo today |
| Marcus Vance (supply chain / routing) | **AeroQ** (optimization, mesh) only loosely | No vehicle-routing or combinatorial logistics module |
| *(implicit)* Quantum verification engineer | **TwinSentry** + `quantum-cloud-backends.md` | TwinSentry validates **pulses**, not arbitrary QASM topologies at scale |

---

## 4. Architecture & constraints

### 4.1 Developer workspace (§3.1)

| Element | MatrixQ PRD | Current repo implementation |
|---------|-------------|----------------------------|
| Cursor (visual synthesis) | Required | Used to build repo; not a runtime dependency |
| Claude Code (CLI orchestration) | Required | Optional; `scripts/`, `maturin`, pytest |
| Streamlit labs | Implied web routes | **Twin Lab**, **Projects Lab** |

### 4.2 Zero-cost prototyping (§3.2)

| Element | MatrixQ PRD | Current repo implementation |
|---------|-------------|----------------------------|
| Local containers | Mandated for routes/contracts | Partial (Langfuse Docker optional) |
| Ollama for inference | Mandated | **Yes** — `OLLAMA_*`, BAML client, sidebar health |
| Mock vs real UI | Not named in MatrixQ excerpt | **Yes** — `portfolio_mode.py`, sidebar execution mode |

MatrixQ’s mandate is **already partially satisfied** by TwinSentry’s Ollama + Mock mode; MatrixQ adds **containerized full-stack parity** for every route, which this repo does not claim yet.

---

## 5. Feature block comparison (§4.1 Materials / VQE)

| Capability | MatrixQ §4.1 (VQE) | TwinSentry | AeroQ | Drug mock |
|------------|-------------------|------------|-------|-----------|
| Li₂S preset → lab telemetry (e.g. 4.12 V) | **FR-4.1.3** | — | — | — |
| Jordan-Wigner / ansatz UI | **FR-4.1.1** | — | — | — |
| SPSA + cloud shot loop | **FR-4.1.2** | RK4 only (classical twin) | QSVT narrative | Staged mock |
| 30-qubit orbital sim (no OOM) | KPI | 2-qubit scope | — | — |
| 3 weeks → &lt;4 min footprint | KPI | — | — | — |
| `counts` → bond length / voltage | Design §5.1 VQE parser | Fidelity proxy only | — | Mock JSON stages |

## 5b. Feature block comparison (§4.2 Logistics / QAOA)

| Capability | MatrixQ §4.2 (QAOA) | TwinSentry | AeroQ | Drug mock |
|------------|-------------------|------------|-------|-----------|
| VRP inputs (coords, capacity, windows) | **FR-4.2.1** | — | Mesh partition (different problem) | — |
| QUBO + cost/mixer Hamiltonians | **FR-4.2.2** | — | QAOA in PRD (mesh), not VRP | — |
| Bitstrings → route map | **FR-4.2.3** | — | — | — |
| \(>10^{40}\) permutations → qubit register | KPI claim | — | — | — |
| Hours → sub-minute routing | KPI | — | — | — |

**Recommendation:** If MatrixQ materials sandbox is in scope for **this** repo, extend **Drug discovery mock** toward a real VQE submodule—or keep MatrixQ as a **separate repo** and link via OpenQASM export only.

---

## 6. What to build where (decision guide)

| If the goal is… | Prefer… |
|-----------------|---------|
| Safe NL pulse control + lab audit demos | **TwinSentry** (stay in this repo) |
| CFD / aerospace hybrid narrative | **AeroQ** (this repo scaffold) |
| TLS/signing migration story | **PQC** (separate module/repo per PRD) |
| OpenQASM verification at scale + serverless HPC | **MatrixQ** (new service or repo; don’t stretch TwinSentry TDSE) |
| Materials VQE without full MatrixQ | Extend **domain_mocks** / Projects Lab drug panel |
| Fleet routing / Marcus persona | New module or MatrixQ; **not** in current PRDs |

---

## 7. Suggested integration hooks (if MatrixQ joins the portfolio)

1. **Export path:** TwinSentry cloud submit → serialized OpenQASM 3.0 → MatrixQ verifier (HTTP or CLI).
2. **Shared execution mode:** Reuse `mock` / `real` semantics for MatrixQ job submission labels.
3. **Shared tracing:** Langfuse trace IDs across TwinSentry run and MatrixQ verification job.
4. **Persona-aligned mocks:** Map Helena → drug/chemistry mock; Marcus → new routing mock tab in Projects Lab (optional).

---

## 8. Shared data contract (design doc §5)

MatrixQ standardizes API responses with `success`, `counts`, `quantum_metadata`, and `bloch_vectors`. TwinSentry today returns a different shape (pulse params, Rust snapshots, optional cloud job metadata). **Alignment opportunity:** extend cloud submit in this repo to emit MatrixQ-compatible JSON for WebGL or external MatrixQ UI.

| Field | MatrixQ | TwinSentry (approximate) |
|-------|---------|--------------------------|
| `counts` | 8192-shot histogram | Cloud backend may return counts |
| `bloch_vectors` | Per-qubit x,y,z for WebGL | Bloch from reduced state in UI |
| `quantum_metadata` | Qubits, depth, duration_ms | Partial via cloud / twin metadata |
| Business parsers | VQE voltage / QAOA routes | Gate mapping + Langfuse trace |

---

## 9. Document index

| Document | Path |
|----------|------|
| MatrixQ PRD | [`MatrixQ-Sandbox-Platform-PRD.md`](MatrixQ-Sandbox-Platform-PRD.md) |
| MatrixQ technical design | [`../DESIGN_DOC_Master.md`](../DESIGN_DOC_Master.md) |
| TwinSentry | [`TwinSentry-Digital-Twin-PRD.md`](TwinSentry-Digital-Twin-PRD.md) |
| AeroQ | [`AeroQ-Consolidated-PRD-v3.0.md`](AeroQ-Consolidated-PRD-v3.0.md) |
| PQC | [`Post-Quantum-Crypto-Project-PRD.md`](Post-Quantum-Crypto-Project-PRD.md) |
| Business rollup | [`../Business-Guide.md`](../Business-Guide.md) |
