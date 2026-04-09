//! PyO3 bridge (Milestone 4): expose the twin engine and SPSC queue to Python.
#![allow(clippy::useless_conversion)] // PyO3 `#[pymethods]` return types trigger false positives

use crate::spsc::{pulse_queue as queue_new, PulseCommand, PulseReceiver, PulseSender};
use crate::state::StateVector4;
use crate::twin::TwinEngine;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyModule;

#[pyclass(name = "PulseCommand")]
#[derive(Clone)]
pub struct PyPulseCommand {
    #[pyo3(get, set)]
    pub amplitude: f32,
    #[pyo3(get, set)]
    pub frequency_hz: f32,
    #[pyo3(get, set)]
    pub duration_s: f32,
    #[pyo3(get, set)]
    pub qubit0_split_hz: f32,
    #[pyo3(get, set)]
    pub qubit1_split_hz: f32,
    #[pyo3(get, set)]
    pub rabi_ref_hz: f32,
}

#[pymethods]
impl PyPulseCommand {
    #[new]
    #[pyo3(signature = (
        amplitude = 0.0,
        frequency_hz = 5e9,
        duration_s = 100e-9,
        qubit0_split_hz = 5e9,
        qubit1_split_hz = 4.5e9,
        rabi_ref_hz = 10e6,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        amplitude: f32,
        frequency_hz: f32,
        duration_s: f32,
        qubit0_split_hz: f32,
        qubit1_split_hz: f32,
        rabi_ref_hz: f32,
    ) -> Self {
        Self {
            amplitude,
            frequency_hz,
            duration_s,
            qubit0_split_hz,
            qubit1_split_hz,
            rabi_ref_hz,
        }
    }
}

impl From<&PyPulseCommand> for PulseCommand {
    fn from(p: &PyPulseCommand) -> Self {
        PulseCommand {
            amplitude: p.amplitude,
            frequency_hz: p.frequency_hz,
            duration_s: p.duration_s,
            qubit0_split_hz: p.qubit0_split_hz,
            qubit1_split_hz: p.qubit1_split_hz,
            rabi_ref_hz: p.rabi_ref_hz,
        }
    }
}

impl From<&PulseCommand> for PyPulseCommand {
    fn from(p: &PulseCommand) -> Self {
        Self {
            amplitude: p.amplitude,
            frequency_hz: p.frequency_hz,
            duration_s: p.duration_s,
            qubit0_split_hz: p.qubit0_split_hz,
            qubit1_split_hz: p.qubit1_split_hz,
            rabi_ref_hz: p.rabi_ref_hz,
        }
    }
}

#[pyclass(name = "PulseSender")]
pub struct PyPulseSender {
    pub(crate) inner: PulseSender,
}

#[pymethods]
impl PyPulseSender {
    fn send(&self, cmd: PyRef<PyPulseCommand>) -> PyResult<()> {
        match self.inner.send(PulseCommand::from(&*cmd)) {
            Ok(()) => Ok(()),
            Err(e) => Err(PyRuntimeError::new_err(format!("send failed: {e}"))),
        }
    }
}

#[pyclass(name = "PulseReceiver")]
pub struct PyPulseReceiver {
    pub(crate) inner: PulseReceiver,
}

#[pyclass(name = "TwinEngine")]
pub struct PyTwinEngine {
    inner: TwinEngine,
}

#[pymethods]
impl PyTwinEngine {
    #[new]
    #[pyo3(signature = (pulse=None))]
    fn new(pulse: Option<PyRef<PyPulseCommand>>) -> Self {
        let p = pulse.map(|r| PulseCommand::from(&*r)).unwrap_or_default();
        Self {
            inner: TwinEngine::new(StateVector4::ground(), p),
        }
    }

    fn step(&mut self, t: f32, dt: f32) {
        self.inner.step_trotter_rk4(t, dt);
    }

    fn drain(&mut self, rx: PyRef<PyPulseReceiver>) {
        self.inner.drain_pulse_queue(&rx.inner);
    }

    fn renormalize(&mut self) {
        self.inner.renormalize();
    }

    fn state(&self) -> Vec<(f32, f32)> {
        self.inner.state.psi.iter().map(|z| (z.re, z.im)).collect()
    }

    fn fidelity_ground(&self) -> f32 {
        self.inner.fidelity_ground()
    }

    #[getter]
    fn pulse(&self) -> PyPulseCommand {
        PyPulseCommand::from(&self.inner.pulse)
    }

    #[setter]
    fn set_pulse(&mut self, p: PyRef<PyPulseCommand>) {
        self.inner.pulse = PulseCommand::from(&*p);
    }
}

/// Create a bounded single-producer / single-consumer queue for [`PulseCommand`] updates.
#[pyfunction]
#[pyo3(name = "pulse_queue")]
fn pulse_queue_py(capacity: usize) -> (PyPulseSender, PyPulseReceiver) {
    let (tx, rx) = queue_new(capacity);
    (PyPulseSender { inner: tx }, PyPulseReceiver { inner: rx })
}

pub fn init_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPulseCommand>()?;
    m.add_class::<PyPulseSender>()?;
    m.add_class::<PyPulseReceiver>()?;
    m.add_class::<PyTwinEngine>()?;
    m.add_function(wrap_pyfunction!(pulse_queue_py, m)?)?;
    Ok(())
}
