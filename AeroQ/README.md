## AeroQ (MVP scaffold)

Hybrid quantum-classical platform scaffold for aerospace CFD acceleration.

### Quick start

```bash
cd AeroQ
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
python scripts/smoke_kernel.py
```

### Configure backend

Edit `config.yaml`:

- `backend: pennylane_amd` for local GPU simulator workflows (PennyLane).
- `backend: qiskit_ibm` for IBM Runtime workflows (Qiskit).

Notes:
- The current `solve_linear_system(A, b)` implementation is an MVP routing layer. It defaults to a classical solve and provides clean extension points for QSVT/HHL-style solvers.

