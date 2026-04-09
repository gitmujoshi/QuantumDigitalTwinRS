# Quantum engineering fundamentals — training companion

**Audience:** Engineers who will design pulses, interpret simulation output, review policy limits, or connect lab hardware to control software.  
**Relationship to other docs:** This page builds **conceptual background**. For product-specific procedures (repo layout, BAML, Langfuse, exercises), see [TwinSentry-Training-Guide.md](TwinSentry-Training-Guide.md).

---

## 1. How to use this document

Work through **Sections 2–10** to align on language used across quantum labs and software stacks. **Section 12** maps each topic to **TwinSentry-RS** (Rust twin, BAML policy, Streamlit Lab, optional cloud circuits).

**What this is not:** A substitute for a full quantum mechanics course, a calibration manual for a specific vendor, or a certification syllabus. It is a **shared vocabulary** layer so quantum and software engineers can review the same traces and parameters without talking past each other.

---

## 2. Mathematical background (what you actually need)

### 2.1 Complex numbers and linear algebra

- Quantum states are **vectors** over the complex numbers. Amplitudes are **complex**; probabilities come from **modulus squared**.
- **Inner products** \(\langle \phi | \psi \rangle\) encode overlap; **norm** \(\sqrt{\langle\psi|\psi\rangle}\) must be 1 for pure states.
- **Operators** (observables, Hamiltonians) are **Hermitian** matrices; **unitary** matrices \(U\) preserve norms (ideal closed-system evolution).
- **Tensor products** \(\lvert \psi \rangle_A \otimes \lvert \phi \rangle_B\) describe independent subsystems; **entangled** states cannot be written as a single tensor product of one-qubit kets.

### 2.2 Dirac notation (minimal)

- **Ket** \(\lvert \psi \rangle\): state vector (column). **Bra** \(\langle \psi \rvert\): conjugate transpose (row).
- **Computational basis** for one qubit: \(\lvert 0 \rangle\), \(\lvert 1 \rangle\). For \(n\) qubits, basis kets are bit strings of length \(n\), e.g. \(\lvert 00 \rangle, \ldots, \lvert 11 \rangle\).

### 2.3 Eigenvalues and measurement (outcome probabilities)

- Measuring Hermitian \(O\) in state \(\lvert\psi\rangle\): outcomes are **eigenvalues** of \(O\); probability of eigenvalue \(\lambda\) is **\(\lvert \langle \lambda \vert \psi \rangle \lvert^2\)** where \(\lvert\lambda\rangle\) is the corresponding eigenstate (for non-degenerate spectrum).

You do **not** need graduate-level functional analysis to work with TwinSentry; you **do** need comfort with **2×2 and 4×4 matrices** and **complex arithmetic**.

---

## 3. Quantum bits and the Bloch sphere

### 3.1 One-qubit pure states

Any pure state of one qubit can be written

\[
\lvert \psi \rangle = \alpha \lvert 0 \rangle + \beta \lvert 1 \rangle,
\quad \lvert \alpha \rvert^2 + \lvert \beta \rvert^2 = 1.
\]

Up to global phase, this maps to a **unit vector** \((x, y, z)\) on the **Bloch sphere**:

- **North pole** \(\lvert 0 \rangle\), **south pole** \(\lvert 1 \rangle\).
- **Equator** = equal superpositions with relative phase (e.g. \(\lvert +\rangle = \frac{1}{\sqrt{2}}(\lvert 0\rangle + \lvert 1\rangle)\)).

**Engineering intuition:** Control pulses **rotate** the Bloch vector. The **axis and angle** of rotation depend on drive frequency, amplitude, phase, and duration in the lab frame or rotating frame.

### 3.2 Mixed states (when purity < 1)

Real devices often produce **mixed** states \(\rho\) (density matrices): \(\rho = \sum_k p_k \lvert \psi_k \rangle \langle \psi_k \rvert\). The **Bloch vector** can still be defined for a single-qubit reduced state \(\rho_A = \mathrm{Tr}_B(\rho_{AB})\) for a 2-qubit system; its length is **≤ 1** (equality iff pure).

**Purity** \(\mathrm{Tr}(\rho^2)\) equals 1 for pure states and is **< 1** for mixed states — a useful sanity check when noise or partial trace is involved.

---

## 4. Multi-qubit states and entanglement

### 4.1 Product vs entangled

- **Product state:** \(\lvert \psi \rangle_{AB} = \lvert \psi \rangle_A \otimes \lvert \phi \rangle_B\).
- **Entangled:** cannot be factored as a single product. Example: **Bell state** \(\frac{1}{\sqrt{2}}(\lvert 00 \rangle + \lvert 11 \rangle)\).

### 4.2 Partial trace and “what qubit A looks like”

- Tracing out qubit B from \(\rho_{AB}\) gives **reduced state** \(\rho_A\) — what you describe if you only care about A. **TwinSentry Lab** plots Bloch vectors from **reduced density matrices** on each qubit for the 2-qubit simulator state.

### 4.3 Why 2-qubit matters for control engineers

Even if you only “drive” one qubit, **cross-talk**, **always-on couplings**, and **leakage** can make the **true** Hilbert space larger than the ideal qubit subspace. A **2-qubit** twin is a minimal step toward **multi-qubit awareness** without full device physics.

---

## 5. Time evolution: Schrödinger equation and unitaries

### 5.1 Closed system

\[
\mathrm{i}\hbar \frac{\mathrm{d}}{\mathrm{d}t}\lvert \psi \rangle = H(t) \lvert \psi \rangle.
\]

For **time-independent** \(H\), formal solution \(\lvert \psi(t) \rangle = \mathrm{e}^{-\mathrm{i} H t / \hbar}\lvert \psi(0)\rangle\) is a **unitary** (in code, \(\hbar\) is often set to 1).

### 5.2 Piecewise drives

In the lab, \(H(t)\) changes when pulses turn on/off. **Numerical integration** (e.g. Runge–Kutta) advances \(\psi\) over small \(\Delta t\). **Error** depends on \(\Delta t\), smoothness of \(H(t)\), and stiffness of the problem.

### 5.3 Rotating-frame picture (conceptual)

Microwave control often works in a **rotating frame** at the drive frequency: fast oscillations are **removed**, leaving **detuning** and **Rabi** terms that are easier to interpret. The twin’s Hamiltonian uses **split frequencies** and **drive frequency** to express **detuning** in that spirit (see `hamiltonian.rs` in the repo).

---

## 6. Common gates and circuit intuition

### 6.1 Pauli and Clifford gates

- **\(X\):** bit-flip (equivalent to \(\pi\) rotation around \(\hat{x}\) on the Bloch sphere).
- **\(Z\):** phase flip; **\(Y\):** \(\pi\) around \(\hat{y}\).
- **\(H\) (Hadamard):** \(\lvert 0\rangle \leftrightarrow \lvert +\rangle\) superposition.

### 6.2 Phase and arbitrary rotations

- **\(R_z(\theta)\)** / **\(R_y(\theta)\)** / **\(R_x(\theta)\)** — **single-qubit** rotations by angle \(\theta\) about an axis.
- **Phase gate** \(P(\phi)\) adds a relative phase on \(\lvert 1 \rangle\).

### 6.3 Two-qubit gates

- **CNOT** (and other controlled gates) are **essential** for entanglement and universal quantum computation with single-qubit rotations.

### 6.4 Gates vs pulses in practice

- **Abstract circuits** (Qiskit, Cirq, etc.) use **discrete gates**.
- **Lab hardware** often implements **continuous pulses** (microwave envelopes) that **approximate** those gates after **calibration** and **pulse shaping** (e.g. DRAG to reduce leakage).

**TwinSentry-RS** uses a **continuous Hamiltonian** in Rust (pulse-like) while the optional **cloud path** maps to **discrete gates** for IBM/Aer — a deliberate separation documented in [quantum-cloud-backends.md](../quantum-cloud-backends.md).

---

## 7. Pulses, rotating frames, and lab control

### 7.1 Rabi oscillations

- Driving on resonance (in the right frame) **rotates** the Bloch vector at a rate proportional to **Rabi frequency** \(\Omega\) (scales with **amplitude** and coupling strength).
- **Pulse area** \(\int \Omega(t)\,\mathrm{d}t\) (roughly \(\Omega \times \text{duration}\) for flat tops) determines rotation angle (e.g. \(\pi\) pulse for inversion).

### 7.2 Detuning

- If drive frequency is **off** from qubit transition, **phase** accumulates between drive and qubit — **rotations** become **incomplete** or **phase-shifted** vs. ideal.

### 7.3 Pulse shaping

- **Square** vs **Gaussian** vs **DRAG** — trade spectral leakage, bandwidth, and robustness. The twin does **not** model every pulse shape; it uses a **parameterized envelope** (see `PulseCommand` and Hamiltonian construction).

### 7.4 Calibration loop (what “good” looks like)

- **Spectroscopy** → **Rabi** → **Ramsey** (T2*) → **T1** (relaxation) → **readout calibration** → **gate error** (RB, tomography).  
Digital twins help **before** burning expensive hardware time, but **never** replace the calibration loop on real devices.

---

## 8. Noise, decoherence, and open-system models

### 8.1 T1 and T2 (intuitive)

- **T1** (energy relaxation): population decays toward **thermal equilibrium** (often \(\lvert 0 \rangle\) at millikelvin).
- **T2** (dephasing): **loss of phase coherence** in superposition (Ramsey envelope decay). **T2** ≤ **2 T1** in simple models.

### 8.2 Channels (very short)

- **Dephasing** (phase damping) kills off-diagonal coherences of \(\rho\).
- **Amplitude damping** (T1-like) moves population toward \(\lvert 0 \rangle\).

### 8.3 TwinSentry’s noise model (policy + metadata)

- BAML **`NoiseProfile`** carries **relative** scales (T2 dephasing, thermal jitter) with **policy caps** — not a full Lindblad master equation in the current Rust core.
- Treat these as **integration-test knobs** and **audit metadata**; extend the simulator if you need **Lindblad** or **stochastic** trajectories.

---

## 9. Measurement and readout

### 9.1 Projective measurement

- Ideal measurement in the computational basis **projects** \(\lvert \psi \rangle\) onto \(\lvert 0 \rangle\) or \(\lvert 1 \rangle\) with probabilities \(| \langle 0 | \psi \rangle |^2\), \(| \langle 1 | \psi \rangle |^2\).

### 9.2 Readout errors

- Real devices have **assignment error** (guess \(|1\rangle\) when state was \(|0\rangle\)) and **crosstalk**; distinguish **SPAM** (state prep + measurement) from **gate** error.

### 9.3 TwinSentry’s fidelity metric

- **`fidelity_ground`** in the twin is **population of \(\lvert 00 \rangle\)**: \(|a_{00}|^2\). It is a **simple proxy**, not full process tomography or RB. See the training guide for extending metrics.

---

## 10. Fidelity, benchmarking, and validation

### 10.1 State overlap

- **Fidelity** between pure state \(\lvert \psi \rangle\) and target \(\lvert \phi \rangle\): \(|\langle \phi | \psi \rangle|^2\).

### 10.2 Process fidelity (high level)

- **Process tomography** (expensive) or **randomized benchmarking (RB)** (scalable) estimates **average gate error**; **interleaved RB** targets a specific gate.

### 10.3 What to validate in a control plane

- **Policy** respects **amplitude / frequency / duration** bands.
- **Simulator** matches **known limits** (e.g. small-angle vs \(\pi\) pulse).
- **Traces** (Langfuse) tie **intent** → **schema** → **parameters** → **scores**.

---

## 11. Control-plane architecture (lab + software)

### 11.1 Layers

1. **User intent** (human or upstream system).
2. **Policy / safety** (schema validation, limits, approvals).
3. **Compilation** (gates → pulses, or pulses → hardware format).
4. **Execution** (hardware driver or simulator).
5. **Observability** (logs, traces, metrics).

**TwinSentry** sits across **1–2–4** with a **digital twin** at 4 and **Langfuse** at 5.

### 11.2 Why “no network in the Rust core”**

- Isolation reduces **attack surface** and **non-determinism**; parameters come through a **queue** from Python.

---

## 12. Connecting fundamentals to TwinSentry-RS

| Concept (this doc) | Where it appears in the repo |
|--------------------|-------------------------------|
| 2-qubit state, computational basis | `StateVector4`, `src/state.rs` |
| Schrödinger evolution, RK4 | `src/rk4.rs`, `src/twin.rs` |
| Hamiltonian + drive / splits | `src/hamiltonian.rs`, `PulseCommand` fields |
| Bloch sphere of reduced ρ | `python/twin_sentry/quantum_viz.py`, `app/twin_lab.py` |
| Policy + schema | `baml_src/quantum.baml`, `ParsePulseFromIntent` |
| Noise metadata (relative scales) | BAML `NoiseProfile`, Langfuse spans |
| Gate-equivalent cloud circuits | `python/twin_sentry/quantum_cloud.py` |
| Sample NL intents for testing | `python/twin_sentry/sample_prompts.py`, [sample-quantum-prompts.md](../sample-quantum-prompts.md) |

**Suggested learning path:** Read **Sections 3–7** here, then **Part A** of [TwinSentry-Training-Guide.md](TwinSentry-Training-Guide.md), then run **TwinSentry Lab** (Streamlit) and vary **RK4 steps** and **dt** while watching Bloch vectors and **fidelity_ground**.

---

## 13. Further reading

- **Nielsen & Chuang, *Quantum Computation and Quantum Information*** — standard reference for gates, algorithms, and noise (select chapters).
- **Girvin, lecture notes on superconducting qubits** — rotating frame, Rabi, coupling (often available as course PDFs).
- **Vendor docs** (IBM, Google, IonQ, etc.) — pulse APIs, calibration workflows, and **hardware-specific** limits supersede any generic simulator.

---

## 14. Document maintenance

When TwinSentry gains new physics (e.g. Lindblad, more qubits, pulse shapes), update **Section 12** and the **training guide** together. Keep this file **concept-first**; put **repo-specific** commands and file paths in `TwinSentry-Training-Guide.md`.
