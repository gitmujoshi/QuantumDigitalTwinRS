# Technical Design Document: MatrixQ Infrastructure & Microservices

**Version:** 1.0.0  
**Author:** Principal Cloud & Quantum Architects  
**Classification:** Technical / Internal  
**Status:** Imported reference design (MatrixQ product line)  
**Last updated:** 2026-05-20  
**Related PRD:** [`prd/MatrixQ-Sandbox-Platform-PRD.md`](prd/MatrixQ-Sandbox-Platform-PRD.md)

---

## 1. System Topology Overview

MatrixQ relies on an automated, multi-tiered architecture that segregates user management, data manipulation, and high-compute execution into independent, stateless container configurations.

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│     1. USER LAYER      │ ───> │   2. COMPUTE ROUTER    │ ───> │  3. SERVERLESS ENGINES │
│ Next.js App Router UI  │      │ FastAPI Core Service   │      │ AWS Fargate / Azure CA │
│ Custom Web Workbench   │      │ Mapping / Optimization │      │ Qiskit Aer Emulators   │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

---

## 2. Global Codebase Execution Environment Constraints

To enforce runtime stability across all engineering pods, the IDE workspace mounts persistent environment configuration directives via dedicated global rules maps (`.cursor/rules/matrixq-core.mdc`).

```markdown
---
description: Universal standards, tech stack rules, and testing requirements for MatrixQ
globs: ["**/*"]
alwaysApply: true
---
# MatrixQ Foundation Standards

## Architecture & Versions
- Frontend: Next.js (TypeScript, Tailwind CSS, App Router)
- Backend: Python FastAPI (Stateless REST endpoints)
- Automation: Docker Compose (Local Testing Stack)

## Core Integration Contracts
- Local AI Interface: Forward requests via `httpx` to http://host.docker.internal:11434
- Default Model: `qwen2.5-coder:32b`
- Cross-Origin Resource Sharing (CORS): Enforce isolated origins between frontend and backend.

## Testing & Stability Mandate
- No feature is complete without a corresponding automated execution test.
- Python Backend: `pytest` with clean mock coverage handlers.
- Infrastructure: All configuration must be explicit, modular, and container-safe.
```

---

## 3. Deployment & Environment Automation Scripting

The workspace is defined declaratively to maintain complete environment symmetry between local developer machines, staging gates, and final production multi-cloud targets.

### 3.1 Local Container Orchestration Engine (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    networks:
      - matrixq-mesh

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
      - OLLAMA_MODEL=qwen2.5-coder:32b
    networks:
      - matrixq-mesh

networks:
  matrixq-mesh:
    driver: bridge
```

### 3.2 Headless Local DevOps Testing Rig (`./scripts/test-local.sh`)

```bash
#!/usr/bin/env bash
set -eo pipefail

echo "Initializing multi-container detached testing mesh..."
docker compose up -d --build

echo "Awaiting connection readiness from FastAPI core endpoint..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8000/docs); do
    printf '.'
    sleep 1
done

echo "Executing Pytest framework with structural mocking routines..."
docker compose exec -T backend pytest backend/tests/

echo "Tearing down testing container infrastructure..."
docker compose down
```

### 3.3 Multi-Cloud Provisioning Framework

Images are compiled as stateless assets, making them completely multi-cloud compatible. Production delivery maps directly into the following container deployment patterns:

| Cloud | Pattern |
|-------|---------|
| **AWS** | Amazon ECR → ECS Fargate serverless task definition |
| **Azure** | Azure Container Registry → Azure Container App with explicit ingress |
| **GCP** | Google Artifact Registry → Cloud Run microservice tasks |

---

## 4. Advanced Computational Microservices

### 4.1 Section A: Material Science VQE Simulator Engine

The system translates chemical properties into complex matrix formulations. For a Lithium Sulfide (Li₂S) configuration, the system generates an electronic energy map using a Jordan-Wigner transformation, assigning molecular orbital configurations directly to independent qubit arrays.

```
          ┌──────────┐     ┌──────────┐     ┌───────────┐
q_0: ─────┤ H Gate   ├─────┤─●────────┤─────┤ Rz(theta) ├───── [Measure]
          └──────────┘     │ │        │     └───────────┘
          ┌──────────┐     │ ▼        │     ┌───────────┐
q_1: ─────┤ X Gate   ├─────┤─X────────┤─────┤ Ry(phi)   ├───── [Measure]
          └──────────┘     └──────────┘     └───────────┘
         (Superposition)   (Entanglement)   (Tuning Rotations)
```

The algorithm loops continuously between classical optimization layers and serverless cloud nodes to identify the lowest possible molecular energy footprint:

| Step | Phase | Description |
|------|-------|-------------|
| 1 | **Initialize parameter array** (classical) | Boots a classical optimizer on a standard server node; sets baseline ansatz rotational parameters (θ, φ). |
| 2 | **Execute target quantum circuit** (serverless) | Packs parameters into an OpenQASM payload; dispatches to scalable cloud runner (Qiskit Aer). |
| 3 | **Ingest telemetry payload** (API gateway) | Processes 8,192 sampling shots; returns structured JSON with bitstring probability counts. |
| 4 | **Calculate expectation value** (convergence) | Classical node evaluates molecular energy; if ground state not converged, modifies parameters and repeats. |

---

### 4.2 Section B: Logistics Combinatorial QAOA Engine

Vehicle routing assigns binary decision variables (\(x_i \in \{0,1\}\)) to discrete path coordinates, compiled into a **QUBO** model where business violations are penalized as positive mathematical weights.

| Step | Phase | Description |
|------|-------|-------------|
| 1 | **Initialize circuit depth steps** (classical) | Launches classical parameter optimization; sets baseline variational angles (γ, β). |
| 2 | **Execute parametric QAOA circuit** (serverless) | Constructs OpenQASM 3.0 script (cost layers + mixer gates); dispatches to cloud instances. |
| 3 | **Ingest probability bitstrings** (API gateway) | Executes 8,192 shots; returns structured binary `counts` payload. |
| 4 | **Update variational angles** (convergence) | Maps highest-frequency bitstrings to transportation cost matrix; shifts angles until shortest route profile locks. |

---

## 5. System Inter-Service Data Contract

When any advanced simulation node completes its processing loop, it transmits a standardized JSON package across the API gateway to frontend dashboard parsers:

```json
{
  "success": true,
  "counts": {
    "10110010": 6942,
    "01001101": 984,
    "00100100": 266
  },
  "quantum_metadata": {
    "allocated_qubits": 8,
    "optimized_gate_depth": 32,
    "execution_duration_ms": 114.7
  },
  "bloch_vectors": [
    {"qubit": 0, "x": 0.052, "y": 0.012, "z": 0.985},
    {"qubit": 1, "x": -0.041, "y": 0.095, "z": -0.921}
  ]
}
```

### 5.1 Downstream Business Parsing Rules

| Parser | Input | Output |
|--------|-------|--------|
| **VQE parsing core** | Molecular energy states at convergence | Optimum interatomic bond lengths; maximum safe voltage thresholds (e.g. cap quick-charge at **4.12 V** for cell lifetime). |
| **QAOA parsing core** | High-frequency bitstring (e.g. `"10110010"`) | Maps index bits to dispatch tables (1 = execute route, 0 = bypass congestion); human-readable multi-vehicle schedules. |
| **Bloch geometry core** | `bloch_vectors` array | WebGL module renders 3D state on sphere without extra client-side quantum math. |

---

## 6. Contrast with QuantumDigitalTwinRS (this repo)

| MatrixQ design | This repo today |
|----------------|-----------------|
| Next.js + FastAPI + Docker Compose mesh | Streamlit (`twin_lab.py`, `projects_lab.py`) + Rust extension |
| Standard simulation JSON (`counts`, `bloch_vectors`) | Twin result: fidelity, state snapshots, `gate_mapping`, optional cloud job |
| VQE / QAOA microservices | Drug mock, weather mock, AeroQ OSSLBM; no 30-qubit VQE loop |
| `qwen2.5-coder:32b` default | `llama3.1:latest` default for BAML/Ollama |
| WebGL Bloch dashboard | Streamlit Plotly Bloch in Twin Lab |

Potential bridge: align TwinSentry cloud submit responses with §5 JSON shape so a future MatrixQ frontend could consume the same contract.
