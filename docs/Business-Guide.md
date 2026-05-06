# Business Guide — How companies can use this repo

This repository is a **portfolio of three practical, company-relevant quantum workstreams**. It is designed to help business stakeholders understand:

- **What problems each workstream solves**
- **What can be demoed today**
- **How to evaluate ROI and risk**
- **How to operationalize pilots inside an enterprise**

---

## 1) What this repo contains (in plain language)

### TwinSentry (Digital Twin for quantum control)
**What it is:** A safe “sandbox” that turns natural-language intent into **validated pulse parameters**, runs a **deterministic simulation**, and produces **auditable traces**.

**What it’s for in a company:**
- Prove you can build **safety + governance** around advanced compute workflows (AI-assisted control).
- Create **reproducible** engineering evidence: “who requested what, what parameters were used, what result happened.”
- Enable R&D teams to iterate faster with a shared review surface (UI + traces).

**Business outcomes:**
- Reduced risk of unsafe/invalid parameterization
- Faster iteration and clearer stakeholder review
- Better compliance posture for high-impact experimental workflows

---

### AeroQ (Hybrid quantum-classical acceleration concept for CFD)
**What it is:** A scaffold for a future aerospace CFD product: hardware abstraction (GPU simulator vs QPU), linear-system kernels, and QML surrogate modeling.

**What it’s for in a company:**
- Establish a **credible architecture** for “hybrid value now” (GPU-first) with a clean path to quantum backends.
- Provide a testbed for **backend selection, benchmarking plans, and integration design**.

**Business outcomes:**
- A concrete technical narrative for funding, partnerships, and roadmap planning
- Faster prototyping of “what would it take” to integrate quantum methods into simulation stacks

---

### Post‑Quantum Crypto Readiness (PQC migration and quantum-safe engineering)
**What it is:** A readiness program and demo path for migrating cryptography away from schemes threatened by future quantum computers.

**What it’s for in a company:**
- Build an internal plan for **crypto-agility** and staged migration (including hybrid periods).
- Educate stakeholders on Shor vs Grover, and why **“harvest now, decrypt later”** changes priorities.

**Business outcomes:**
- Reduced long-term security risk for long-lived data
- Practical migration patterns rather than abstract fear/uncertainty

---

## 2) Who should care (stakeholders)

- **CTO / VP Engineering**: roadmap realism, pilot scope, buy-vs-build, integration costs
- **Security leadership (CISO / AppSec / Crypto owners)**: PQC migration risk, auditability, compliance
- **R&D / Applied science leaders**: reproducibility, governance, and experimental velocity
- **Platform teams**: operational patterns, configuration, observability, and CI readiness

---

## 3) What you can demo today (no slides required)

### One UI to run everything

Run:

```bash
streamlit run app/projects_lab.py
```

Then pick a project in the sidebar:

- **TwinSentry**: enter an intent → run → show fidelity proxy + full JSON output (and trace IDs if configured).
- **AeroQ**: solve a small linear system \(Ax=b\) (foundation for future QSVT-style acceleration).
- **Post‑Quantum Crypto**: run a “hybrid handshake” and “hybrid signatures” demo (shows crypto‑agility patterns).

---

## 4) How this maps to company use cases

### A) Governance for advanced compute (AI + simulation + safety)
Many organizations struggle with governance once AI can generate parameters that affect real systems (lab equipment, security policy, optimization systems).

**TwinSentry shows a pattern**:
- typed “contracts” for AI output (policy layer)
- deterministic execution (so outcomes are reproducible)
- tracing/audit (so decisions are reviewable)

### B) Hybrid acceleration roadmaps
Quantum value is often **hybrid** for the near-term: classical accelerators do most work; quantum methods may assist specific subroutines.

**AeroQ provides an architecture** to:
- define a backend abstraction layer (GPU vs QPU)
- route workloads via config
- benchmark and evolve without rewriting the whole stack

### C) PQC migration programs
PQC readiness is not one library upgrade—it’s an engineering program.

**The PQC readiness workstream** helps companies:
- prioritize what to migrate first (long-lived secrets)
- adopt crypto-agility (switch algorithms by config)
- run hybrid phases and record what was used

---

## 5) Suggested “pilot” paths (low-risk adoption)

### Pilot 1 (2–4 weeks): PQC readiness assessment + demo
- Inventory where public-key crypto is used (TLS termination, signing, key exchange, internal services).
- Establish algorithm agility requirements and rollout stages.
- Use the repo demo to communicate “hybrid migration” to stakeholders.

### Pilot 2 (2–6 weeks): Governance + auditability for AI-assisted engineering
- Define a typed policy surface (what AI is allowed to propose).
- Require trace IDs and structured outputs for review.
- Use TwinSentry-style tracing as an internal pattern for future systems.

### Pilot 3 (4–8 weeks): Hybrid simulation architecture (AeroQ-style)
- Build a benchmark harness around one expensive subroutine (often linear algebra).
- Add backend routing + metrics.
- Run GPU-first, but keep a clean path to quantum backends.

---

## 6) What this is NOT (so expectations stay realistic)

- Not a drop-in production quantum control system for a specific vendor device
- Not a complete QSVT production implementation (AeroQ is a scaffold)
- Not a complete PQC library suite; it focuses on migration patterns and demos

---

## 7) Next steps for a company evaluating this repo

- **Choose a primary goal**:
  - security readiness (PQC)
  - governance/auditability (TwinSentry patterns)
  - hybrid acceleration architecture (AeroQ)
- **Run the Projects Lab demo** and capture screenshots + outputs
- **Define success metrics** (time saved, risk reduced, reproducibility, audit coverage)
- **Plan a pilot** with one owner, one environment, and explicit non-goals

