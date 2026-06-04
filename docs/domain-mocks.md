# Domain mocks (weather, drug discovery, production QPU)

These modules are **portfolio demos**: realistic **workflow shape** and APIs, not production physics or hardware.

## Weather — regional NWP mock

**Module:** `python/domain_mocks/weather.py`  
**UI:** Projects Lab → AeroQ → **Regional forecast (mock NWP)**

| Backend | Mock behavior |
|---------|----------------|
| `classical_hpc` | LU-style subroutine, fastest wall time |
| `hybrid_qsvt` | QSVT linear-solve stub, better toy RMSE |
| `qpu_accelerator_stub` | Queued QPU stub + extra latency |

Outputs: synthetic 2D temperature field summary, RMSE vs analysis, wall time, subroutine name.

**Real-world path:** Replace the stub with your NWP dynamical core + AeroQ HAL for expensive linear/LBM subroutines.

## Drug discovery — pipeline mock

**Module:** `python/domain_mocks/drug_discovery.py`  
**UI:** Projects Lab → **Drug discovery (mock)**

Stages (by backend):

1. Classical docking (always)
2. VQE active-space stub (`hybrid_vqe`, `surrogate_ml`)
3. ML surrogate ranking (`surrogate_ml` only)

**Real-world path:** OpenMM/RDKit docking, PySCF/Chem+VQE on QPU, internal ML rankers — same staged audit pattern as TwinSentry.

## Production QPU control — vendor mocks

**Module:** `python/twin_sentry/qpu_vendor_mock.py`  
**UI:** Twin Lab or Projects Lab → cloud backend **`mock_ibm`**, **`mock_ionq`**, **`mock_rigetti`**

Simulates:

- Policy gate (reject if not approved)
- Calibration snapshot (T1/T2, readout error, max pulse length)
- Queue depth + job id
- Deterministic shot counts from pulse + gate type

**Real-world path:** Swap mock for Qiskit IBM Runtime, IonQ, Rigetti SDKs; keep TwinSentry policy + Langfuse in front.

## Materials & Logistics (merged PRD §4)

| Mode | Materials (Li₂S VQE) | Logistics (VRP) |
|------|----------------------|-----------------|
| **Mock** | `run_vqe_materials(..., real=False)` | `run_logistics_qaoa(..., real=False)` |
| **Real-world** | Classical SPSA + optional Aer | Greedy VRP on metro coordinates |

**UI:** Projects Lab → **Materials & Logistics** (always in sidebar; behavior follows execution mode).

Both emit `simulation_payload` (`python/twin_sentry/simulation_contract.py`).

## Mock vs Real in the UI

Both **Twin Lab** and **Projects Lab** have a sidebar control:

- **Mock (sandbox)** — mock IBM/IonQ/Rigetti, regional NWP mock, drug pipeline mock  
- **Real-world (configured deps)** — Qiskit Aer / IBM Quantum, AeroQ OSSLBM (PennyLane in `AeroQ/.venv`)

Implementation: `python/portfolio_mode.py`

## Run

```bash
streamlit run app/projects_lab.py
# or
streamlit run app/twin_lab.py
```

```bash
pytest tests/test_domain_mocks.py -q
```
