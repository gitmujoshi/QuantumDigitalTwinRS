//! Fourth-order Runge–Kutta integration for `dψ/dt = -i H(t) ψ`.

use crate::hamiltonian::{self, C4};
use crate::simd_ops::{apply_tdse_rhs, simd_axpy_c4, simd_copy_c4};
use num_complex::Complex32;

/// One RK4 step with mid-point sampling of `H(t)` (Trotter-style splitting uses the same `dt` as the sub-step size).
pub fn rk4_step_tdse(
    t: f32,
    dt: f32,
    h_builder: impl Fn(f32) -> C4,
    psi: &mut [Complex32; 4],
    scratch: &mut Rk4Scratch,
) {
    let h1 = h_builder(t);
    rhs(&h1, psi, &mut scratch.k1);

    let h2 = h_builder(t + dt * 0.5);
    simd_copy_c4(psi, &mut scratch.tmp);
    simd_axpy_c4(0.5 * dt, &scratch.k1, &mut scratch.tmp);
    rhs(&h2, &scratch.tmp, &mut scratch.k2);

    simd_copy_c4(psi, &mut scratch.tmp);
    simd_axpy_c4(0.5 * dt, &scratch.k2, &mut scratch.tmp);
    rhs(&h2, &scratch.tmp, &mut scratch.k3);

    let h3 = h_builder(t + dt);
    simd_copy_c4(psi, &mut scratch.tmp);
    simd_axpy_c4(dt, &scratch.k3, &mut scratch.tmp);
    rhs(&h3, &scratch.tmp, &mut scratch.k4);

    let sixth = dt / 6.0;
    simd_axpy_c4(sixth, &scratch.k1, psi);
    simd_axpy_c4(2.0 * sixth, &scratch.k2, psi);
    simd_axpy_c4(2.0 * sixth, &scratch.k3, psi);
    simd_axpy_c4(sixth, &scratch.k4, psi);
}

#[inline]
fn rhs(h: &C4, psi: &[Complex32; 4], out: &mut [Complex32; 4]) {
    let mut work = [Complex32::new(0.0, 0.0); 4];
    apply_tdse_rhs(h, psi, &mut work, out);
}

/// Reusable temporaries for [`rk4_step_tdse`] (avoids heap allocs on the hot path).
pub struct Rk4Scratch {
    k1: [Complex32; 4],
    k2: [Complex32; 4],
    k3: [Complex32; 4],
    k4: [Complex32; 4],
    tmp: [Complex32; 4],
}

impl Default for Rk4Scratch {
    fn default() -> Self {
        Self::new()
    }
}

impl Rk4Scratch {
    pub fn new() -> Self {
        Self {
            k1: [Complex32::new(0.0, 0.0); 4],
            k2: [Complex32::new(0.0, 0.0); 4],
            k3: [Complex32::new(0.0, 0.0); 4],
            k4: [Complex32::new(0.0, 0.0); 4],
            tmp: [Complex32::new(0.0, 0.0); 4],
        }
    }
}

/// Convenience: evolve using [`hamiltonian::hamiltonian_at`] with scalar parameters.
#[allow(clippy::too_many_arguments)]
pub fn rk4_step_pulse(
    t: f32,
    dt: f32,
    drive_frequency_hz: f32,
    qubit0_split_hz: f32,
    qubit1_split_hz: f32,
    amplitude: f32,
    omega_rabi_ref_rad_s: f32,
    psi: &mut [Complex32; 4],
    scratch: &mut Rk4Scratch,
) {
    let builder = |time: f32| {
        hamiltonian::hamiltonian_at(
            time,
            drive_frequency_hz,
            qubit0_split_hz,
            qubit1_split_hz,
            amplitude,
            omega_rabi_ref_rad_s,
        )
    };
    rk4_step_tdse(t, dt, builder, psi, scratch);
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::StateVector4;
    use std::time::Instant;

    #[test]
    fn identity_h_no_change_small_dt() {
        let mut s = StateVector4::ground();
        let mut scratch = Rk4Scratch::new();
        let dt = 1e-9;
        let h0 = hamiltonian::driven_qubit0_zeeman_qubit1(0.0, 0.0, 0.0);
        rk4_step_tdse(0.0, dt, |_| h0, &mut s.psi, &mut scratch);
        assert!((s.psi[0].re - 1.0).abs() < 1e-4);
        assert!(s.psi[0].im.abs() < 1e-4);
    }

    /// Release-only timing guard for one RK4/Trotter sub-step (PRD: < 10 µs).
    #[test]
    #[ignore]
    fn rk4_trotter_step_under_10us() {
        let mut s = StateVector4::ground();
        let mut scratch = Rk4Scratch::new();
        let dt = 5e-10;
        let omega_ref = hamiltonian::hz_to_rad_s(10e6);
        let start = Instant::now();
        for _ in 0..10_000 {
            rk4_step_pulse(
                0.0,
                dt,
                5e9,
                5e9,
                4.5e9,
                0.35,
                omega_ref,
                &mut s.psi,
                &mut scratch,
            );
        }
        let elapsed = start.elapsed();
        let per = elapsed / 10_000;
        assert!(
            per.as_micros() < 10,
            "one RK4 step took {:?} (expected < 10 µs in release)",
            per
        );
    }
}
