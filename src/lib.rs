//! TwinSentry-RS — 2-qubit state vector, TDSE integration via RK4,
//! SIMD-accelerated ℂ⁴ algebra, and SPSC pulse ingress.
//!
//! Simulation has **no network I/O**; the control plane pushes [`PulseCommand`] updates through
//! [`spsc::pulse_queue`]. With the `python` feature, the `bridge` module exposes `TwinEngine` to PyO3.

#[cfg(feature = "python")]
mod bridge;
pub mod hamiltonian;
pub mod rk4;
pub mod simd_ops;
pub mod spsc;
pub mod state;
pub mod twin;

#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyModule;

#[cfg(feature = "python")]
#[pymodule]
fn _native(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    bridge::init_module(m)
}

pub use hamiltonian::{hamiltonian_at, hz_to_rad_s, kron_2x2, scaled_rabi_rad_s};
pub use rk4::{rk4_step_pulse, rk4_step_tdse, Rk4Scratch};
pub use spsc::{pulse_queue, PulseCommand, PulseReceiver, PulseSender};
pub use state::StateVector4;
pub use twin::{hamiltonian_from_command, TwinEngine};
