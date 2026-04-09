# PRD — Post-quantum cryptography & “quantum-safe” readiness (future project)

**Status:** Draft — **not** in scope for TwinSentry-RS digital twin work.  
**Purpose:** Capture product intent before switching focus so requirements are not lost.  
**Last updated:** 2026-04-08

---

## 1. Executive summary

Build a **standalone project** (separate repo or clearly separated module) focused on **understanding and implementing protections** against the **quantum threat to classical cryptography**: what breaks (and what does not), how **post-quantum cryptography (PQC)** mitigates it, and how to **operationalize** migration (hybrid protocols, crypto agility, key lifecycle).

This is **orthogonal** to TwinSentry-RS, which remains a **quantum control / digital twin** stack (pulse policy, Rust TDSE simulation, optional cloud gate circuits).

---

## 2. Problem statement

- **Public-key schemes** based on integer factoring and (elliptic-curve) discrete logarithms are **not** post-quantum: **Shor’s algorithm** (on a sufficiently large fault-tolerant quantum computer) breaks those assumptions.
- **Symmetric cryptography** faces a **weaker** threat model: **Grover’s algorithm** implies revised security margins (often discussed as ~halving effective key length in coarse models for generic attacks).
- **Harvest now, decrypt later:** adversaries may store ciphertext today and decrypt when quantum capability exists—defense requires **early migration** for long-lived secrets.

Organizations need **clarity** (education), **reference implementations** (labs), and **migration patterns** (TLS, signing, key exchange)—not confusion with analog pulse simulation.

---

## 3. Goals

| ID | Goal |
|----|------|
| G1 | Explain **which primitives** are affected (Shor vs Grover) at an **engineer-actionable** level. |
| G2 | Demonstrate **NIST-aligned PQC** usage (e.g. **ML-KEM** / Kyber family for KEM, **ML-DSA** / Dilithium for signatures—exact APIs per chosen standard version). |
| G3 | Show **hybrid** classical + PQC compositions where policies require **interoperability** during transition. |
| G4 | Provide **crypto-agility** patterns: algorithm identifiers, versioning, key rotation. |
| G5 | Document **non-goals** and **threat model** explicitly (no implied “break real systems”). |

---

## 4. Non-goals

- Breaking or attacking **third-party** production systems; all cryptanalysis demos confined to **synthetic keys**, **CTF-style** labs, or **local** test vectors.
- Replacing TwinSentry’s mission (digital twin / control plane).
- Claiming **NISQ** devices “break the internet” today at cryptographic scales.
- Shipping a **new** cryptographic primitive (no custom PQC inventing); use **vetted libraries** (e.g. **liboqs**, **OpenSSL OQS**, language bindings as appropriate).

---

## 5. Target users

- **Security / platform engineers** planning TLS and code-signing migration.
- **Software architects** needing a **PQC + hybrid** story for services.
- **Learners** mapping “quantum breaks crypto” headlines to **concrete mitigations**.

---

## 6. Functional requirements (draft)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | **Educational layer:** concise docs on Shor (PK), Grover (symmetric), HNDL. | P0 |
| FR2 | **Lab harness:** encrypt/decrypt or encapsulate/decapsulate using **PQC KEM** via a **standard library**; configurable parameter sets. | P0 |
| FR3 | **Signatures:** sign/verify with **PQC signatures** (ML-DSA / Dilithium class) in demo code. | P1 |
| FR4 | **Hybrid mode:** combine legacy (e.g. X25519 or RSA) + PQC in a documented pattern (where applicable). | P1 |
| FR5 | **CLI or API** for repeatable demos (language TBD: Rust / Python / Go). | P2 |
| FR6 | **Test vectors:** known-answer tests from standards / project repos where license permits. | P1 |

---

## 7. Non-functional requirements

- **Dependencies:** pin audited PQC stacks; reproducible builds.
- **Safety:** default to **test keys**; never log secrets; document secure deployment separately.
- **Licensing:** compatible OSS; attribute NIST / liboqs / upstream.
- **Performance:** benchmark KEM/sign (ops/sec, sizes) for awareness—not TwinSentry-scale physics.

---

## 8. Out of scope (v1)

- Full **TLS 1.3** production integration (may be v2 if scoped).
- **Hardware security modules (HSM)** integration (v2+).
- **Side-channel** analysis lab (unless explicitly added later).

---

## 9. Milestones (suggested)

| Phase | Deliverable |
|-------|-------------|
| M0 | Repo skeleton + README threat model + “what breaks / what does not.” |
| M1 | PQC KEM demo (encaps/decaps) + docs. |
| M2 | PQC signatures demo + tests. |
| M3 | Hybrid composition doc + minimal example. |
| M4 | Migration checklist (inventory RSA/ECC, agility, HNDL narrative). |

---

## 10. Success metrics

- A new reader can answer: **Why** RSA/ECC are vulnerable to large FTQC, **why** AES-256 is treated differently than RSA, **what** PQC changes in a deployment.
- Demos run **locally** with **pinned** library versions and **passing** tests.
- Clear **separation** from TwinSentry-RS (cross-link only if desired).

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Algorithm obsolescence / updates | Track NIST / IETF; versioned docs. |
| Misuse in production without review | Banner “educational”; separate hardening PRD. |
| Confusion with TwinSentry | Separate repo name (e.g. `pqc-readiness-lab`) or top-level `docs/` boundary. |

---

## 12. Open questions

- **Language:** Rust-first vs Python-first for demos?
- **Scope of TLS:** include **oqs-openssl**-style demo or stay at library level?
- **Compliance:** any organizational policy (FIPS, regional)?

---

## 13. Relation to TwinSentry-RS

| Project | Focus |
|---------|--------|
| **TwinSentry-RS** | Digital twin, pulse policy, Rust simulation, Langfuse, optional Qiskit cloud. |
| **This PRD (future)** | Cryptography education + PQC migration demos; **no** TDSE physics core. |

Cross-reference only; **do not** merge unrelated crypto code into TwinSentry unless a later ADR explicitly justifies it (not planned here).

---

## 14. Document control

- **Owner:** (assign when project starts)
- **Review:** before M1 merge to default branch

When this project spins up, copy this PRD into the new repository’s `docs/PRD.md` or keep this file as the canonical draft and link from the new repo’s README.
