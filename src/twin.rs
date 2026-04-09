//! Digital twin orchestration: state + RK4 + optional pulse queue drain.

use crate::hamiltonian;
use crate::rk4::{rk4_step_pulse, Rk4Scratch};
use crate::spsc::{PulseCommand, PulseReceiver};
use crate::state::StateVector4;
use num_complex::Complex32;

/// Core simulator: 2-qubit state + reusable RK4 scratch + last-applied pulse parameters.
pub struct TwinEngine {
    pub state: StateVector4,
    scratch: Rk4Scratch,
    pub pulse: PulseCommand,
}

impl TwinEngine {
    pub fn new(initial: StateVector4, pulse: PulseCommand) -> Self {
        Self {
            state: initial,
            scratch: Rk4Scratch::new(),
            pulse,
        }
    }

    /// Advance simulation time by `dt` using the current `self.pulse` Hamiltonian.
    pub fn step_trotter_rk4(&mut self, t: f32, dt: f32) {
        let omega_ref = hamiltonian::hz_to_rad_s(self.pulse.rabi_ref_hz);
        rk4_step_pulse(
            t,
            dt,
            self.pulse.frequency_hz,
            self.pulse.qubit0_split_hz,
            self.pulse.qubit1_split_hz,
            self.pulse.amplitude,
            omega_ref,
            &mut self.state.psi,
            &mut self.scratch,
        );
    }

    /// Non-blocking: apply the latest command from the queue, if any.
    pub fn drain_pulse_queue(&mut self, rx: &PulseReceiver) {
        while let Ok(cmd) = rx.try_recv() {
            self.pulse = cmd;
        }
    }

    /// Normalize state (manage numerical drift).
    pub fn renormalize(&mut self) {
        self.state.normalize();
    }

    /// Probability of measuring ∣00⟩ (ground) — common “fidelity” proxy vs ideal ∣00⟩.
    #[inline]
    pub fn fidelity_ground(&self) -> f32 {
        self.state.psi[0].norm_sqr()
    }
}

impl Default for TwinEngine {
    fn default() -> Self {
        Self::new(StateVector4::ground(), PulseCommand::default())
    }
}

/// Map [`PulseCommand`] + time to Hamiltonian matrix (for tests / inspection).
pub fn hamiltonian_from_command(t_s: f32, p: &PulseCommand) -> [[Complex32; 4]; 4] {
    hamiltonian::hamiltonian_at(
        t_s,
        p.frequency_hz,
        p.qubit0_split_hz,
        p.qubit1_split_hz,
        p.amplitude,
        hamiltonian::hz_to_rad_s(p.rabi_ref_hz),
    )
}
