# Sample quantum prompts (testing reference)

This page documents every **natural-language intent** shipped for testing TwinSentry’s BAML policy layer and the Rust digital twin. The canonical definitions live in:

`python/twin_sentry/sample_prompts.py`

- **`SIDEBAR_PRESETS`** — four buttons in **TwinSentry Lab** (`app/twin_lab.py`).
- **`SAMPLE_PROMPTS`** — extended list available via the sidebar dropdown (“More sample prompts”) and **`prompts_by_label()`** for unit tests or scripts.

Set `GOOGLE_API_KEY` (and optional Langfuse keys) when exercising prompts end-to-end through the controller.

---

## How to use these prompts

| Method | What to do |
|--------|------------|
| **TwinSentry Lab** | Run `streamlit run app/twin_lab.py`. Use sidebar quick presets or pick a row under “More sample prompts” and click **Insert into command box**, then run the pipeline. |
| **Python** | `from twin_sentry.sample_prompts import SIDEBAR_PRESETS, SAMPLE_PROMPTS, prompts_by_label` |
| **Regression / CI** | Prefer importing strings from `sample_prompts.py` so docs and UI stay aligned. |

When interpreting results, compare **parsed pulse parameters** (amplitude, frequency, duration, noise flags), **policy allow/deny**, and **simulation metrics** (Bloch vectors, purity) against the intent described below.

---

## Part A — Sidebar presets (`SIDEBAR_PRESETS`)

These are the primary demos: superposition, bit-flip, noisy twin, and policy stress.

### Hadamard

**Purpose:** Exercise a **moderate-amplitude, ideal (noise-free)** pulse aimed at **Hadamard-style superposition** on qubit 0, with explicit **5 GHz** and **80 ns** duration. Use to verify baseline parsing and clean unitary evolution.

**Full prompt:**

```
Apply a Hadamard-style superposition pulse on qubit 0 with moderate amplitude and 5 GHz drive, duration 80 nanoseconds, ideal (no noise).
```

**What to watch:** Amplitude should stay in a sensible range; no digital-twin noise terms; qubit 0 Bloch trajectory should move toward an equator-like superposition (exact shape depends on internal parameterization).

---

### Pi pulse

**Purpose:** Request a **π-class rotation** (bit-flip style) on qubit 0 with **~0.45 amplitude**, **5 GHz**, **80 ns**. Good baseline for comparing against Hadamard wording.

**Full prompt:**

```
Apply a pi pulse on qubit 0 for a bit-flip style rotation, amplitude about 0.45, 5 GHz, 80 ns duration.
```

**What to watch:** Parsed duration/frequency match; distinguish from PHASE-style intents if your policy exposes gate class.

---

### Noise stress test

Purpose: Drive the **digital twin noise model** with **elevated T2 dephasing** and **thermal jitter** (relative **0.08** / **0.07**), plus **0.3 amplitude** and **5 GHz**. Validates that noise fields propagate into simulation, not just ideal unitary blocks.

**Full prompt:**

```
Stress test with elevated digital-twin noise: T2 dephasing relative 0.08 and thermal jitter relative 0.07, amplitude 0.3, 5 GHz.
```

**What to watch:** Reduced purity / mixed-state signatures on Bloch metrics vs. ideal presets; audit trail should reflect noise parameters if exposed.

---

### Safety violation (demo)

**Purpose:** Deliberately request an **unsafe amplitude (1.5)** to test **policy rejection or clamping** and user-visible messaging. Not for production hardware—demo only.

**Full prompt:**

```
Unsafe operating point: request amplitude 1.5 on the drive (policy stress test).
```

**What to watch:** Policy outcome (deny, warn, or clamp), error strings, and that the UI does not silently apply 1.5 without review.

---

## Part B — Extended catalog (`SAMPLE_PROMPTS`)

Grouped as in the source file. Each entry: **label** (dropdown name), **intent**, **notes**.

### Baseline and single-qubit style

#### Small-angle rotation (q0)

**Intent:** Low-amplitude, short pulse on qubit 0; **no noise**.

```
Apply a small rotation on qubit 0: amplitude 0.15, drive 5 GHz, duration 50 ns, no noise.
```

**Notes:** Small angle on Bloch sphere; useful for linear-response checks and numerical stability.

---

#### Z-like phase emphasis

**Intent:** Emphasize **PHASE** gate type wording, **0.25** amplitude, **5 GHz**, **100 ns**, ideal twin.

```
Prepare a pulse with amplitude 0.25, 5 GHz, 100 ns duration, gate type PHASE, ideal twin (no noise profile).
```

**Notes:** Tests whether “PHASE” and “ideal twin” disambiguate from X/rotation defaults.

---

#### Pauli-X style bit-flip

**Intent:** Explicit **X-style** pulse, **0.48** amplitude, **5 GHz**, **80 ns**, **minimal noise**.

```
Execute an X-style pulse on qubit 0: amplitude 0.48, frequency 5 GHz, duration 80 ns, minimal noise.
```

**Notes:** Near “π pulse” preset numerically; good for consistency checks between similar wordings.

---

### Noise and digital twin

#### Mild T2 dephasing only

**Intent:** **T2 = 0.03** relative, **no thermal jitter**; **0.35** amplitude, **5 GHz**, **80 ns**.

```
Digital twin with T2 dephasing relative 0.03 and no thermal jitter, amplitude 0.35, 5 GHz, 80 ns.
```

**Notes:** Isolate T2 channel vs. thermal jitter.

---

#### Thermal jitter only

**Intent:** **Thermal jitter 0.05**, **T2 0.02**; **0.4** amplitude, **5 GHz**.

```
Pulse with thermal jitter relative 0.05 and T2 dephasing relative 0.02, amplitude 0.4, 5 GHz.
```

**Notes:** Both noise types nonzero but asymmetric; useful for attribution in traces.

---

#### High noise (under 10% caps)

**Intent:** Both **T2** and **thermal** at **0.09** (under typical 10% caps), **0.25** amplitude, **5 GHz**.

```
Noise stress: T2 dephasing relative 0.09 and thermal jitter relative 0.09, amplitude 0.25, 5 GHz drive.
```

**Notes:** Stronger mixed-state behavior than “Mild T2”; compare purity to “Noise stress test” preset.

---

### Frequency and duration wording

#### Different drive frequency

**Intent:** **4.8 GHz** (not 5.0 default), **0.33** amplitude, **60 ns**, ideal.

```
Calibrate a pulse at 4.8 GHz on qubit 0, amplitude 0.33, duration 60 nanoseconds, ideal conditions.
```

**Notes:** Parses alternative GHz; good for regression on numeric extraction.

---

#### Longer envelope

**Intent:** **200 ns** duration, **0.2** amplitude, **5 GHz**, qubit 0, **no noise**.

```
Use a longer 200 ns duration pulse, amplitude 0.2, 5 GHz, qubit 0, no noise.
```

**Notes:** Stresses time base and step count when paired with RK4 settings in the Lab.

---

### Policy and edge cases

#### At-amplitude boundary

**Intent:** **Exactly 0.95** amplitude, **5 GHz** π-style, **90 ns**, **no noise**.

```
Set amplitude exactly 0.95 for a 5 GHz pi-style pulse on qubit 0, 90 ns, no noise.
```

**Notes:** Boundary-friendly value; tests rounding and policy thresholds near max safe amplitude.

---

#### Ambiguous multi-qubit wording

**Intent:** **CUSTOM** gate, **0.4** amplitude, **5 GHz**, **100 ns**, **optional small noise**—wording is intentionally loose.

```
We need a CUSTOM gate pulse for calibration: amplitude 0.4, 5 GHz, 100 ns, optional small noise.
```

**Notes:** Tests disambiguation (single-qubit default vs. multi-qubit hints) and optional noise handling.

---

#### Explicit no noise

**Intent:** Ideal unitary only; **omit noise profile** explicitly.

```
Ideal unitary evolution only: amplitude 0.5, 5 GHz, 80 ns, omit noise profile entirely.
```

**Notes:** Should align with ideal presets; validates “negative” instruction (no noise).

---

### Stress and regression

#### Empty-sounding but valid

**Intent:** Minimal sentence; **0.1** amplitude, **5e9 Hz**, **20 ns** on **q0**.

```
Short pulse on q0: amplitude 0.1, 5e9 Hz, 20 ns.
```

**Notes:** Scientific notation and terse phrasing; good for tokenizer/parser robustness.

---

#### Keywords: CNOT + rotation

**Intent:** Mentions **CNOT** and **ROTATION** but describes **single-qubit calibration**: **5 GHz**, **0.38**, **75 ns**, **low noise**.

```
Describe a ROTATION class pulse for single-qubit calibration at 5 GHz, amplitude 0.38, 75 ns, low noise.
```

**Notes:** Keyword noise vs. actual single-qubit intent; useful for policy tests that must not blindly allocate two-qubit gates.

---

## Maintenance

When adding or changing a prompt:

1. Edit `python/twin_sentry/sample_prompts.py`.
2. Update this document so **label**, **full text**, and **purpose/notes** stay accurate.
3. Re-run TwinSentry Lab smoke tests if UI strings change.

---

## See also

- [TwinSentry training guide](training/TwinSentry-Training-Guide.md) — broader product and workflow context  
- Repository `README.md` — quick start and Lab commands  
