// TwinSentry-RS — Policy contract (FR1): QuantumPulse + optional NoiseProfile.
// @assert: hard-stop invalid structured output (PEP / BamlValidationError).
// @check: same policy bands, inspectable in client without always raising (see BoundaryML docs).

enum GateType {
  HADAMARD @description("Hadamard / superposition")
  X @description("Pauli-X / bit-flip")
  Y @description("Pauli-Y")
  Z @description("Pauli-Z / phase-flip")
  CNOT @description("Controlled-NOT (2-qubit)")
  PHASE @description("Diagonal phase gate")
  ROTATION @description("Arbitrary single-qubit rotation")
  CUSTOM @description("Custom drive; validate carefully")
}

class NoiseProfile {
  /// T2 dephasing contribution as a relative noise scale (policy: at most 10%).
  t2_dephasing_relative float
    @assert(t2_noise_within_band, {{ this >= 0.0 and this <= 0.1 }})
    @check(t2_noise_under_10pct, {{ this < 0.1 }})

  /// Thermal jitter contribution as a relative noise scale (policy: at most 10%).
  thermal_jitter_relative float
    @assert(thermal_noise_within_band, {{ this >= 0.0 and this <= 0.1 }})
    @check(thermal_noise_under_10pct, {{ this < 0.1 }})
}

class QuantumPulse {
  /// Drive amplitude; physical range [0, 1]. Policy may require headroom below full scale.
  amplitude float
    @assert(amplitude_in_range, {{ this >= 0.0 and this <= 1.0 }})
    @check(amplitude_lt_1, {{ this < 1.0 }})

  /// Drive frequency in Hz (SI).
  frequency_hz float
    @assert(frequency_positive, {{ this > 0.0 }})

  /// Pulse duration in seconds (SI).
  duration_s float
    @assert(duration_positive, {{ this > 0.0 }})

  gate_type GateType

  /// Optional digital-twin noise; omit for ideal (noiseless) execution.
  noise_profile NoiseProfile?
}

function ParsePulseFromIntent(user_intent: string) -> QuantumPulse {
  client Gemini15Pro
  prompt #"
    You are TwinSentry's quantum control policy assistant.
    From the user's natural-language intent, emit exactly one `QuantumPulse`.

    Rules:
    - Use SI units: frequency_hz in Hz, duration_s in seconds.
    - amplitude must stay within [0, 1]; prefer values strictly below 1.0 when unsure (hardware headroom).
    - If the user describes noise, T2 dephasing, or thermal jitter, fill `noise_profile` with
      relative strengths in [0, 0.1] (10% max each). Omit `noise_profile` for an ideal pulse.
    - Choose `gate_type` from the enum; use CUSTOM only if no listed gate fits.

    {{ ctx.output_format }}

    {{ _.role("user") }}
    {{ user_intent }}
  "#
}
