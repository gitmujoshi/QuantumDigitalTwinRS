# Portfolio Consolidated PRD — QuantumDigitalTwinRS

**Version:** 1.0.0  
**Status:** Active (canonical product document for this repository)  
**Last updated:** 2026-05-20  
**Supersedes:** Per-project PRDs remain as module appendices; this file is the single source of truth for scope and integration.

**Module appendices:** [TwinSentry](TwinSentry-Digital-Twin-PRD.md) · [AeroQ](AeroQ-Consolidated-PRD-v3.0.md) · [MatrixQ](MatrixQ-Sandbox-Platform-PRD.md) · [PQC](Post-Quantum-Crypto-Project-PRD.md) · [Design](../DESIGN_DOC_Master.md)

---

## 1. Executive summary

**QuantumDigitalTwinRS** is a unified **quantum portfolio sandbox**: one repo, one **Mock / Real-world** execution mode, one **simulation JSON contract** (MatrixQ-compatible), and four product modules:

| Module | Job | Primary user |
|--------|-----|--------------|
| **TwinSentry** | NL → BAML pulse policy → Rust 2-qubit TDSE twin → optional cloud gates → Langfuse audit | Control-plane / pulse engineers |
| **MatrixQ sandboxes** | VQE materials (Li₂S) + QAOA logistics mocks with `counts` → business telemetry | Materials scientist, supply-chain VP |
| **AeroQ** | Hybrid CFD scaffold (HAL, linear solve, OSSLBM) | Aerospace / platform engineers |
| **PQC readiness** | Migration education, hybrid KEM/sig demos | Security / platform engineers |

Local development follows the **zero-cost mandate**: Ollama for BAML policy, mock backends by default, real Qiskit Aer / IBM / AeroQ `.venv` when **Real-world** mode is selected.

---

## 2. Shared platform requirements

### 2.1 Execution mode (FR-PLAT-1)

- Sidebar control: **Mock (sandbox)** vs **Real-world (configured deps)**.
- Mock: `mock_ibm` / `mock_ionq` / `mock_rigetti`, domain mocks, no OSSLBM.
- Real: `local_aer` / `ibm_quantum`, AeroQ OSSLBM when `.venv` exists.
- Implementation: `python/portfolio_mode.py`.

### 2.2 Simulation contract (FR-PLAT-2)

All quantum runs that produce shot data SHALL expose a **`simulation_payload`** object aligned with MatrixQ design §5:

```json
{
  "success": true,
  "counts": { "00": 512, "11": 512 },
  "quantum_metadata": { "allocated_qubits": 2, "optimized_gate_depth": 8, "execution_duration_ms": 12.5 },
  "bloch_vectors": [{ "qubit": 0, "x": 0.0, "y": 0.0, "z": 1.0 }],
  "business_telemetry": {}
}
```

- TwinSentry fills this from Rust state + optional cloud `counts`.
- MatrixQ mocks fill `business_telemetry` (VQE: voltage, bond length; QAOA: routes, fuel savings).
- Implementation: `python/twin_sentry/simulation_contract.py`.

### 2.3 Policy & audit (FR-PLAT-3)

- BAML typed pulses with asserts; Ollama default (`OLLAMA_*`).
- Optional Langfuse traces; BAML file logs under `logs/baml/`.

### 2.4 UI (FR-PLAT-4)

- **Twin Lab** — full twin + Bloch + `simulation_payload` tab.
- **Projects Lab** — all modules, PRDs, MatrixQ sandboxes, execution mode.

---

## 3. Module: TwinSentry (digital twin control plane)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-TS-1 | NL intent → `QuantumPulse` via BAML | Implemented |
| FR-TS-2 | Deterministic Rust RK4 twin (2 qubit) | Implemented |
| FR-TS-3 | Gate mapping → initial state / note | Implemented |
| FR-TS-4 | Optional cloud submit after twin | Implemented |
| FR-TS-5 | `simulation_payload` on every run | Implemented (this release) |
| FR-TS-6 | Streamlit lab with presets + sample prompts | Implemented |

**Non-goals:** 30-qubit chemistry, full device physics, production multi-tenant auth.

*Detail:* [TwinSentry-Digital-Twin-PRD.md](TwinSentry-Digital-Twin-PRD.md)

---

## 4. Module: Materials & Logistics (MatrixQ use cases)

Merged from MatrixQ PRD §4.1–4.2. Available in **both** execution modes:

| Mode | Materials (VQE) | Logistics (VRP) |
|------|-----------------|-------------------|
| **Mock** | Synthetic SPSA + telemetry | Synthetic QAOA bitstrings |
| **Real-world** | Classical SPSA on Li₂S PES + optional Aer | Greedy VRP on lat/lon stops |

### 4.1 VQE materials (FR-MQ-1)

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-4.1.1 | Configure geometry, Jordan-Wigner mapping, ansatz preset | `VqeMaterialsRequest` + Li₂S preset in UI |
| FR-4.1.2 | Hybrid loop (SPSA + cloud shots) | Mock stages; **real:** numpy SPSA + optional Aer |
| FR-4.1.3 | `counts` → ground energy, bond length, max safe voltage | `business_telemetry` in payload |

**KPI (mock narrative):** 3 weeks → &lt;4 min; up to 30 qubits — *not executed at scale in repo*.

### 4.2 Logistics QAOA (FR-MQ-2)

| ID | Requirement | Implementation |
|----|-------------|----------------|
| FR-4.2.1 | Coords, capacities, time windows | `LogisticsRequest` |
| FR-4.2.2 | QUBO / cost + mixer (mock) | Synthetic Hamiltonian metadata |
| FR-4.2.3 | Bitstrings → route schedule | Mock bitstrings; **real:** `routes` + distance reduction % |

*Detail:* [MatrixQ-Sandbox-Platform-PRD.md](MatrixQ-Sandbox-Platform-PRD.md), [DESIGN_DOC_Master.md](../DESIGN_DOC_Master.md)

---

## 5. Module: AeroQ (CFD scaffold)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-AQ-1 | HAL linear solve (PennyLane / Qiskit config) | Implemented |
| FR-AQ-2 | OSSLBM one-step (Real-world + AeroQ `.venv`) | Implemented |
| FR-AQ-3 | Regional weather mock (Mock mode tab) | Implemented |

*Detail:* [AeroQ-Consolidated-PRD-v3.0.md](AeroQ-Consolidated-PRD-v3.0.md)

---

## 6. Module: PQC readiness

Orthogonal to simulation; education + crypto-agility patterns. No change to twin core.

*Detail:* [Post-Quantum-Crypto-Project-PRD.md](Post-Quantum-Crypto-Project-PRD.md)

---

## 7. Architecture (implemented)

| Layer | Technology | Path |
|-------|------------|------|
| Policy | BAML + Ollama/Gemini | `baml_src/`, `python/twin_sentry/llm_env.py` |
| Twin | Rust TDSE + PyO3 | `src/`, `python/twin_sentry/controller.py` |
| Contract | MatrixQ JSON envelope | `python/twin_sentry/simulation_contract.py` |
| Domain mocks | Weather, drug, VQE, QAOA | `python/domain_mocks/` |
| Cloud | Aer / IBM / vendor mocks | `python/twin_sentry/quantum_cloud.py` |
| UI | Streamlit | `app/twin_lab.py`, `app/projects_lab.py` |
| Observability | Langfuse + BAML logs | `docker-compose.yaml`, `logs/baml/` |

---

## 8. Success criteria (portfolio demo-ready)

1. Toggle **Mock / Real** and see cloud + AeroQ options change.
2. Twin Lab run returns **fidelity**, **Bloch**, and **`simulation_payload`**.
3. Projects Lab **MatrixQ sandboxes** runs Li₂S VQE mock and VRP QAOA mock with telemetry.
4. AeroQ linear solve + (Real) OSSLBM or (Mock) weather tab.
5. PQC panel runs without blocking other modules.
6. Consolidated PRD + comparison readable in Projects Lab → PRDs.

---

## 9. Future work (explicit)

- Real VQE/QAOA backends behind same `simulation_payload` shape.
- Optional Next.js/FastAPI gateway (full MatrixQ design) consuming TwinSentry API.
- Extend twin beyond 2 qubits; OpenPulse export.
- Production MatrixQ serverless mesh (out of repo scope today).
