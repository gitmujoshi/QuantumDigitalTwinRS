# Quantum cloud backends (optional)

TwinSentry’s **Rust digital twin** simulates analog-style `PulseCommand` envelopes. **Public quantum computers** are usually programmed with **gates or calibrated pulses** via vendor SDKs. This repo adds an **optional** path: after BAML approves a pulse, Python maps **`gate_type` + amplitude** to a small **Qiskit `QuantumCircuit`**, then runs it on:

| Backend | Package | Account / cost | Notes |
|--------|---------|----------------|--------|
| **Qiskit Aer** (local) | `qiskit`, `qiskit-aer` | None | Fast, deterministic for CI and demos. |
| **IBM Quantum** | `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime` | Free tier at [IBM Quantum](https://quantum.ibm.com/) | Real QPU or IBM cloud simulators; queue times vary. |

Other major providers (same idea—gate API + credentials—not wired in code here):

- **Amazon Braket** — IonQ, Rigetti, simulators; needs AWS account and `amazon-braket-sdk`.
- **Azure Quantum** — IonQ, Quantinuum, etc.; Azure subscription.
- **Google Quantum AI** — limited access; Cirq-centric workflows.

Use env vars and vendor docs when you add adapters that call those APIs.

## Mapping (important)

The cloud path is **not** a literal export of the twin’s TDSE drive. It is a **gate-equivalent** stub for integration testing:

- `HADAMARD` → `h(0)`
- `X` / `Y` / `Z` → Pauli on qubit 0
- `PHASE` → `p(π × amplitude, 0)`
- `ROTATION` / `CUSTOM` / default → `ry(π × amplitude, 0)`
- `CNOT` → `cx(0,1)` on two qubits

Production hardware workflows should add **calibration**, **transpilation targets**, and **pulse-level** (e.g. OpenPulse) programs—not only this logical map.

## Install

```bash
# Local simulator only
pip install 'twinsentry-rs[quantum-cloud]'

# IBM Quantum (includes Aer)
pip install 'twinsentry-rs[ibm-quantum]'
```

## Environment

| Variable | Purpose |
|----------|---------|
| `QISKIT_IBM_TOKEN` | IBM Quantum API token (also accepts `IBM_QUANTUM_TOKEN`). |
| `IBM_QUANTUM_BACKEND` | Optional fixed backend name (e.g. `ibm_torino`). |
| `IBM_QUANTUM_PREFER_SIMULATOR` | `1` / `true` to prefer IBM cloud simulators if you have no QPU access. |

## API

- `twin_sentry.quantum_cloud.submit_pulse_cloud(cmd, gate_type, cloud_backend=..., shots=...)`
- `run_twin_pipeline(..., cloud_backend="local_aer"|"ibm_quantum"|None, cloud_shots=1024)` — see `python/twin_sentry/controller.py`

TwinSentry Lab exposes **optional cloud** in the sidebar when you run `streamlit run app/twin_lab.py`.
