//! Single-producer / single-consumer ingress for pulse parameter updates (bounded crossbeam channel).

use crossbeam_channel::{Receiver, Sender, TryRecvError};

/// Latest pulse drive parameters ingested from the control plane (Python) into the Rust twin.
#[derive(Clone, Debug, PartialEq)]
pub struct PulseCommand {
    pub amplitude: f32,
    pub frequency_hz: f32,
    pub duration_s: f32,
    /// Splitting / lab-frame energy scale for qubit 0 (Hz).
    pub qubit0_split_hz: f32,
    /// Splitting for qubit 1 (Hz).
    pub qubit1_split_hz: f32,
    /// Reference Rabi scale in Hz (maps amplitude → Ω via `amplitude * 2π * rabi_ref_hz`).
    pub rabi_ref_hz: f32,
}

impl Default for PulseCommand {
    fn default() -> Self {
        Self {
            amplitude: 0.0,
            frequency_hz: 5e9,
            duration_s: 100e-9,
            qubit0_split_hz: 5e9,
            qubit1_split_hz: 4.5e9,
            rabi_ref_hz: 10e6,
        }
    }
}

/// Create a bounded SPSC queue for [`PulseCommand`] values.
pub fn pulse_queue(capacity: usize) -> (PulseSender, PulseReceiver) {
    let (tx, rx) = crossbeam_channel::bounded(capacity);
    (PulseSender { inner: tx }, PulseReceiver { inner: rx })
}

/// Producer handle (intended: one writer).
pub struct PulseSender {
    inner: Sender<PulseCommand>,
}

/// Consumer handle (intended: one reader — simulation thread).
pub struct PulseReceiver {
    inner: Receiver<PulseCommand>,
}

impl PulseSender {
    #[inline]
    pub fn try_send(
        &self,
        cmd: PulseCommand,
    ) -> Result<(), crossbeam_channel::TrySendError<PulseCommand>> {
        self.inner.try_send(cmd)
    }

    #[inline]
    pub fn send(
        &self,
        cmd: PulseCommand,
    ) -> Result<(), crossbeam_channel::SendError<PulseCommand>> {
        self.inner.send(cmd)
    }
}

impl PulseReceiver {
    #[inline]
    pub fn try_recv(&self) -> Result<PulseCommand, TryRecvError> {
        self.inner.try_recv()
    }

    #[inline]
    pub fn recv(&self) -> Result<PulseCommand, crossbeam_channel::RecvError> {
        self.inner.recv()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spsc_roundtrip() {
        let (tx, rx) = pulse_queue(4);
        let cmd = PulseCommand {
            amplitude: 0.5,
            frequency_hz: 5e9,
            duration_s: 50e-9,
            qubit0_split_hz: 5e9,
            qubit1_split_hz: 4.5e9,
            rabi_ref_hz: 12e6,
        };
        tx.send(cmd.clone()).unwrap();
        assert_eq!(rx.recv().unwrap(), cmd);
    }
}
