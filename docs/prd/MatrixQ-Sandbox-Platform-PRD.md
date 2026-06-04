# Product Requirement Document (PRD): MatrixQ Sandbox Platform

**Version:** 1.0.0  
**Author:** Product Engineering Core  
**Classification:** Technical / Internal  
**Status:** Imported reference (external product line)  
**Last updated:** 2026-05-20  
**Canonical portfolio PRD:** [`Portfolio-Consolidated-PRD.md`](Portfolio-Consolidated-PRD.md)  
**Related:** [`../DESIGN_DOC_Master.md`](../DESIGN_DOC_Master.md) · [`MatrixQ-vs-Portfolio-Comparison.md`](MatrixQ-vs-Portfolio-Comparison.md)  
**Code:** `python/domain_mocks/vqe_materials.py`, `logistics_qaoa.py` (mock implementations)

---

## 1. Product Vision & Executive Summary

MatrixQ is a hardware-agnostic, serverless quantum simulation and verification workbench built to bridge the gap between abstract quantum algorithms and real-world industrial computing infrastructure. By coupling an industry-standard OpenQASM 3.0 runtime engine with cloud-native, auto-scaling classical compute networks, MatrixQ allows researchers and operations engineers to validate logic topologies, map environmental noise profiles, and eliminate extreme hardware execution costs at scale.

---

## 2. Core User Personas

1. **Dr. Helena Vance (Lead Materials Scientist):** Needs to determine the structural degradation thresholds of novel energy-storage configurations without running multi-week classical supercomputing grid arrays or premature physical lab tests.
2. **Marcus Vance (VP of Global Supply Chain Operations):** Needs to optimize massive metropolitan vehicle dispatch routines along the absolute shortest, most fuel-efficient trajectory lines without running into combinatorial classical processing walls.

---

## 3. Product Architecture & Technical Constraints

### 3.1 Developer Workspace Paradigm

The platform is built around a lean, modern engineering workspace that shifts seamlessly across developer toolchains:

- **Visual Synthesis Core (Cursor):** Drives primary multi-file generation, dependency tracking, code refactoring, and interactive UI visual debugging loops.
- **Terminal Integration Engine (Claude Code):** Manages headless script orchestration, unit-test diagnostics execution, and automated compilation bug-fixing right from the CLI.

### 3.2 The Zero-Cost Prototyping Mandate

To conserve premium cloud resources, the system enforces a strict hybrid development lifecycle. All core web routes, data contracts, and interface actions are prototyped locally against containerized application nodes. These nodes map their local inference and code completion streams to hardware-bound open-weight language engines running locally on the developer's machine via an Ollama daemon layer.

---

## 4. High-Performance Compute Feature Specifications

### 4.1 Feature Block A: Material Science Sandbox (VQE Engine)

- **Objective:** Enable non-trivial, hybrid quantum-classical chemical simulations for molecular energy profiling.

**User journey matrix:**

```
[INPUT MOLECULAR GEOMETRY] ──> [HYBRID VQE LOOP] ──> [ACTIONABLE LAB TELEMETRY]
(Selects Li2S Preset)        (Executes on Cloud)     (Max Safe Voltage: 4.12V)
```

**Functional requirements:**

| ID | Requirement |
|----|-------------|
| **FR-4.1.1** | The UI must provide a workspace allowing researchers to configure atomic structures, select chemical mapping matrices (e.g., Jordan-Wigner), and inject custom algorithmic templates (Ansatz configurations). |
| **FR-4.1.2** | The backend system must handle iterative payload generation, running standard classical optimization algorithms (e.g., SPSA) in tandem with serverless cloud quantum simulation passes. |
| **FR-4.1.3** | The platform must decode binary hardware probability strings (`counts`) into high-level physical telemetry parameters (ground state energy, optimal interatomic bond lengths, and maximum voltage breakdown parameters). |

**Success criteria & KPIs:**

- Successfully execute up to a **30-qubit** molecular orbital matrix tracking simulation on cloud-allocated instances without triggering Out-Of-Memory (OOM) faults.
- Reduce the time required to calculate a molecule's stable geometric footprint from **3 weeks** (standard classical infrastructure) to **under 4 minutes**.

---

### 4.2 Feature Block B: Logistics Optimization Sandbox (QAOA Engine)

- **Objective:** Enable supply chain managers to solve large-scale, combinatorial vehicle routing problems (VRP) by transforming spatial constraints into parameterized quantum optimization models.

**User journey matrix:**

```
[INPUT ROUTE & TRUCK MATRIX] ──> [HYBRID QAOA MESH] ──> [ACTIONABLE LOGISTICS MAP]
(Enforces No-Collision Rules)    (Executes on Cloud)     (Saves $4M/Month in Fuel)
```

**Functional requirements:**

| ID | Requirement |
|----|-------------|
| **FR-4.2.1** | The platform UI must accept unstructured logistics data inputs, including geographic coordinate arrays, vehicle capacities, and delivery time windows. |
| **FR-4.2.2** | The backend system must map these parameters to an unconstrained binary optimization model, automatically generating the cost Hamiltonians and mixer circuits required for quantum evaluation. |
| **FR-4.2.3** | The software must parse the returned high-frequency bitstrings from the JSON payload and translate them into human-readable multi-vehicle route scheduling visualizations. |

**Success criteria & KPIs:**

- Successfully process combinatorially scaling route complexities that would paralyze a traditional classical server (\(>10^{40}\) permutations) by mapping them to compressed, clean qubit registers.
- Reduce automated fleet routing generation loops from **hours of grid computing** to **sub-minute serverless execution intervals**.

---

## 5. Relationship to this repository

MatrixQ is a **sibling product concept** in the same portfolio family as TwinSentry, AeroQ, and PQC readiness. It emphasizes **OpenQASM-scale circuit verification**, **VQE/QAOA domain sandboxes**, and a **Next.js + FastAPI + serverless** stack—whereas TwinSentry-RS in this repo focuses on **NL → typed pulse policy → Rust TDSE twin → audit traces** (Streamlit labs today).

See: [`MatrixQ-vs-Portfolio-Comparison.md`](MatrixQ-vs-Portfolio-Comparison.md).
