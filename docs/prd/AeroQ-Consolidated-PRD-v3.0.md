# PRD — AeroQ Consolidated (v3.0)

## Part 1: The AeroQ Consolidated PRD (v3.0)

### 1. Product Vision

AeroQ is a hybrid quantum-classical platform that accelerates Computational Fluid Dynamics (CFD) for aerospace engineering. It solves the "Simulation Wall" where classical supercomputers fail due to memory and time constraints.

### 2. Core Technical Pillars

- **Simulation (The Engine)**: Solving linear systems (\(Ax=b\)) using Quantum Singular Value Transformation (QSVT).
- **Optimization (The Fabric)**: Efficiently partitioning 3D meshes using Iterative-QAOA.
- **QML (The Brain)**: Real-time aerodynamics feedback via Quantum-Assisted Physics-Informed Neural Networks (QA-PINNs).

### 3. Key User Features

- **Unified Hardware Abstraction (HAL)**: One-click toggle between AMD GPU simulators (via PennyLane) and IBM Quantum Processors (via Qiskit).
- **Adaptive Mesh-Partitioning**: Automatic domain decomposition optimized for multi-node GPU clusters.
- **Surrogate Designer**: A QML-powered dashboard that predicts lift/drag instantly as the user modifies CAD geometry.

---

## Part 2: The Quantum Glossary for Business Leaders

| Term | Simple Definition | Business Value |
|---|---|---|
| QSVT | A mathematical framework for performing matrix operations on a quantum computer. | The primary "engine" that allows us to solve flight physics. |
| QAOA | An algorithm that finds the best solution among millions of possibilities. | Optimizes where to spend compute power, saving 15-20% in cloud costs. |
| Hybrid Computing | Splitting a task so the GPU does the heavy lifting and the QPU (Quantum Unit) does the "hard math." | Allows us to provide value today without waiting for "perfect" quantum computers. |
| Barren Plateau | A situation where a quantum AI stops learning because it can't find the "downhill" path to the solution. | A technical risk we mitigate by using specialized "Physics-Informed" neural networks. |
| Digital Twin | A virtual 1:1 replica of a physical jet engine or wing. | Allows thousands of "virtual test flights" before a single physical part is built. |

---

## Part 3: The "Hands-On" Developer Prompts

Copy and paste these into Cursor or Claude Code to generate your MVP.

### Prompt 1: The Framework Abstraction Layer

> "Act as a Senior Quantum Software Engineer. Create a hardware-agnostic Python class named AeroQKernel. It should support two backends:
> PennyLaneAMD: Uses lightning.gpu with the catalyst JIT compiler for high-speed CFD simulation on AMD GPUs.
> QiskitIBM: Uses the qiskit_ibm_runtime to run circuits on IBM's 2026 Heron processors.
> Include a method solve_linear_system(A, b) that routes the request based on a config.yaml file. Use 2026 SDK standards (Primitive V2 for Qiskit)."

### Prompt 2: The QSVT Simulation Module

> "Generate a PennyLane function for Block-Encoding a sparse 256x256 matrix. Follow the 2026 Xanadu/AMD whitepaper methodology: Use the Quantum Singular Value Transformation (QSVT) to solve the system Ax=b. Implement a polynomial approximation for 1/x to transform the singular values. Optimize the circuit for low gate depth using catalyst.jit."

### Prompt 3: The QML Surrogate Engine

> "Develop a QA-PINN (Quantum-Assisted Physics-Informed Neural Network). The model should include:
> A classical neural network (using PyTorch) for general features.
> A Variational Quantum Circuit (VQC) layer using a 'Strongly Entangling Layer' for turbulence feature extraction.
> A custom loss function that incorporates the Navier-Stokes residual (the physics constraint).
> Use PennyLane's TorchLayer for seamless integration."

---

## Part 4: Success Benchmarks (The "Demo" Proof)

To secure funding, your code must produce these three charts:

1. **Speedup Graph**: Showing the 25x reduction in time when switching from CPU-only to the AMD-accelerated QSVT.
2. **Training Curve**: Showing that the QA-PINN converges to 98% accuracy with 50% less data than a standard AI.
3. **Optimization Heatmap**: Comparing a "standard" mesh vs. your QAOA-optimized mesh, highlighting the reduction in "Graph Fill-in."

