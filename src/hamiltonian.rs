//! Time-dependent two-qubit Hamiltonians in the lab frame (σ basis, ⊗ ordering: q1 ⊗ q0).

use num_complex::Complex32;
use std::f32::consts::PI;

pub type C4 = [[Complex32; 4]; 4];

#[inline]
fn c(re: f32, im: f32) -> Complex32 {
    Complex32::new(re, im)
}

/// Kronecker product for 2×2 complex matrices (row-major output 4×4).
#[inline]
#[allow(clippy::needless_range_loop)]
pub fn kron_2x2(a: &[[Complex32; 2]; 2], b: &[[Complex32; 2]; 2]) -> C4 {
    let mut out = [[c(0.0, 0.0); 4]; 4];
    for i in 0..2 {
        for j in 0..2 {
            for k in 0..2 {
                for l in 0..2 {
                    let r = 2 * i + k;
                    let c = 2 * j + l;
                    out[r][c] = a[i][j] * b[k][l];
                }
            }
        }
    }
    out
}

#[inline]
fn pauli_i() -> [[Complex32; 2]; 2] {
    [[c(1.0, 0.0), c(0.0, 0.0)], [c(0.0, 0.0), c(1.0, 0.0)]]
}

#[inline]
fn pauli_z() -> [[Complex32; 2]; 2] {
    [[c(1.0, 0.0), c(0.0, 0.0)], [c(0.0, 0.0), c(-1.0, 0.0)]]
}

fn mat_add_4(a: &C4, b: &C4) -> C4 {
    let mut o = [[c(0.0, 0.0); 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            o[i][j] = a[i][j] + b[i][j];
        }
    }
    o
}

fn mat_scale_4(s: f32, m: &C4) -> C4 {
    let mut o = [[c(0.0, 0.0); 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            o[i][j] = m[i][j] * s;
        }
    }
    o
}

/// Single-qubit Hamiltonian in rotating frame of the drive: `(Δ/2) σ_z + (Ω/2) σ_x`.
#[inline]
pub fn single_qubit_rabi(delta_rad_s: f32, rabi_rad_s: f32) -> [[Complex32; 2]; 2] {
    [
        [c(delta_rad_s / 2.0, 0.0), c(rabi_rad_s / 2.0, 0.0)],
        [c(rabi_rad_s / 2.0, 0.0), c(-delta_rad_s / 2.0, 0.0)],
    ]
}

/// `H = H_q0 ⊗ I + I ⊗ ((ω1_z/2) σ_z)` — drive on qubit 0, Zeeman on qubit 1.
pub fn driven_qubit0_zeeman_qubit1(delta_rad_s: f32, rabi_rad_s: f32, omega1_z_rad_s: f32) -> C4 {
    let hq0 = single_qubit_rabi(delta_rad_s, rabi_rad_s);
    let i = pauli_i();
    let z = pauli_z();

    let term0 = kron_2x2(&hq0, &i);
    let hz1 = mat_scale_4(omega1_z_rad_s / 2.0, &kron_2x2(&i, &z));
    mat_add_4(&term0, &hz1)
}

/// Convert Hz → rad/s.
#[inline]
pub fn hz_to_rad_s(hz: f32) -> f32 {
    2.0 * PI * hz
}

/// Rabi frequency from normalized amplitude in `[0, 1]` and a reference Ω_ref (rad/s).
#[inline]
pub fn scaled_rabi_rad_s(amplitude: f32, omega_rabi_ref_rad_s: f32) -> f32 {
    amplitude.max(0.0) * omega_rabi_ref_rad_s
}

/// Build `H(t)` for a square envelope drive on qubit 0.
pub fn hamiltonian_at(
    t_s: f32,
    drive_frequency_hz: f32,
    qubit0_split_hz: f32,
    qubit1_split_hz: f32,
    amplitude: f32,
    omega_rabi_ref_rad_s: f32,
) -> C4 {
    let omega_d = hz_to_rad_s(drive_frequency_hz);
    let w0 = hz_to_rad_s(qubit0_split_hz);
    let w1 = hz_to_rad_s(qubit1_split_hz);
    // Rotating-frame detuning vs lab: approximate Δ ≈ w0 - ω_d for the qubit-0 transition.
    let delta = w0 - omega_d;
    let rabi = scaled_rabi_rad_s(amplitude, omega_rabi_ref_rad_s);
    // Phase of drive could be ω_d t; absorbed into interaction picture — keep real Rabi along X.
    let _ = t_s; // reserved for shaped envelopes / phase noise (future work)
    driven_qubit0_zeeman_qubit1(delta, rabi, w1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kron_identity() {
        let i = pauli_i();
        let k = kron_2x2(&i, &i);
        assert_eq!(k[0][0], c(1.0, 0.0));
        assert_eq!(k[3][3], c(1.0, 0.0));
    }

    #[test]
    fn hermitian_rabi_block() {
        let h = hamiltonian_at(0.0, 5e9, 5e9, 4.5e9, 0.2, hz_to_rad_s(10e6));
        // Hermitian: H = H†
        for i in 0..4 {
            for j in 0..4 {
                assert!((h[i][j].conj() - h[j][i]).norm() < 1e-5);
            }
        }
    }
}
