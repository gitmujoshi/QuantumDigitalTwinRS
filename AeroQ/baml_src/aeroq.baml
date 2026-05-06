// AeroQ BAML surface (MVP).
//
// This is intentionally small: it gives AeroQ a typed, auditable interface for any
// LLM-assisted steps (mesh partition suggestions, solver choice, config synthesis, etc.).

type LinearSolvePlan {
  method string
  rationale string
  backend_hint string?
}

function DraftLinearSolvePlan(intent: string) -> LinearSolvePlan {
  client Gemini15Pro
  prompt #"
You are a senior quantum/HPC engineer working on AeroQ (hybrid quantum-classical CFD).

User intent:
{{ intent }}

Task:
- Propose a plan for solving a linear system Ax=b in an MVP.
- Be concrete about the method name (e.g., "classical_lu", "qsvt_stub", "iterative_cg").
- Give a short rationale.
- If relevant, suggest a backend hint: "pennylane_amd" or "qiskit_ibm".

Return JSON for LinearSolvePlan.
"#
}

