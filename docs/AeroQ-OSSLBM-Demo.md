# AeroQ — OSSLBM (One-step Simplified Lattice Boltzmann) demo

This repo includes an R&D scaffold for a **one-step simplified Lattice Boltzmann (LBM)** quantum circuit implemented in **PennyLane**, with an optional **Catalyst JIT** hook.

## What it demonstrates

- **Amplitude encoding** of an initial 2D velocity-density field \(f_0(x,y,v)\)
- A **collision** step modeled as a **unitary** acting on the velocity subspace
- A **streaming** step modeled as a **unitary permutation** over the \((x,y,v)\) basis with periodic boundaries

## Velocity sets

- **D2Q4**: 4 axial directions (power-of-two friendly)
- **D2Q9**: 9-velocity 2D LBM set. Because 9 is not a power of two, this scaffold embeds D2Q9 into a **padded velocity register**:
  - use `nv=16`
  - channels `0..8` are D2Q9 (with `0` as rest)
  - channels `9..15` are padding and stream as `(0,0)`

## Files

- Implementation: `AeroQ/src/aeroq/osslbm.py`
- Demo script: `AeroQ/scripts/osslbm_demo.py`
- Tests: `AeroQ/tests/test_osslbm.py`

## Run the demo

From the repo root:

```bash
cd AeroQ
./.venv/bin/pip install -e ".[dev,qsvt,pennylane_amd]"
./.venv/bin/python scripts/osslbm_demo.py
```

## Run via the UI

The Streamlit Projects Lab includes an **OSSLBM** tab under **AeroQ**. It uses `AeroQ/.venv` automatically so the root environment doesn’t need PennyLane.

```bash
streamlit run app/projects_lab.py
```

## Notes / limitations (by design for MVP)

- The streaming operator is currently applied as a permutation unitary (clear + correct for small grids).
- The collision operator is a toy unitary mixing velocity channels; replace it with a physics-motivated construction as research progresses.
- Catalyst JIT is used only when installed (`catalyst`).

