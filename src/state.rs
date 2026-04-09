//! Two-qubit state vector in the computational basis
//! `|b1 b0⟩` with indices: `0=|00⟩, 1=|01⟩, 2=|10⟩, 3=|11⟩`.

use num_complex::Complex32;

/// Four complex amplitudes (ℂ⁴) for a 2-qubit ket.
#[derive(Clone, Debug, PartialEq)]
pub struct StateVector4 {
    pub psi: [Complex32; 4],
}

impl Default for StateVector4 {
    fn default() -> Self {
        Self::ground()
    }
}

impl StateVector4 {
    pub fn ground() -> Self {
        let mut psi = [Complex32::new(0.0, 0.0); 4];
        psi[0] = Complex32::new(1.0, 0.0);
        Self { psi }
    }

    /// ∑ |aᵢ|² ; must be 1.0 for a physical ket.
    pub fn norm_sq(&self) -> f32 {
        self.psi.iter().map(|z| z.norm_sqr()).sum()
    }

    pub fn normalize(&mut self) {
        let n = self.norm_sq().sqrt();
        if n > 0.0 && n.is_finite() {
            let inv = 1.0 / n;
            for z in &mut self.psi {
                *z *= inv;
            }
        }
    }
}
