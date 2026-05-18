import numpy as np

from aeroq.osslbm import (
    OsslBmSpec,
    amplitude_encode_velocity_density,
    collision_unitary,
    streaming_permutation,
    streaming_permutation_with_velocity_set,
    build_osslbm_one_step_qnode,
)


def test_amplitude_encoding_normalizes() -> None:
    f0 = np.zeros((2, 2, 4), dtype=float)
    f0[0, 0, 0] = 1.0
    amps = amplitude_encode_velocity_density(f0, nx=2, ny=2, nv=4)
    assert np.isclose(np.linalg.norm(amps), 1.0)


def test_collision_unitary_is_unitary() -> None:
    U = collision_unitary(4, theta=0.2)
    eye = np.eye(U.shape[0], dtype=np.complex128)
    assert np.allclose(U.conj().T @ U, eye, atol=1e-10)


def test_streaming_is_permutation_unitary() -> None:
    P = streaming_permutation(2, 2, 4)
    eye = np.eye(P.shape[0], dtype=np.complex128)
    assert np.allclose(P.conj().T @ P, eye, atol=1e-10)


def test_streaming_d2q9_padding_is_unitary() -> None:
    P = streaming_permutation_with_velocity_set(2, 2, 16, velocity_set="D2Q9")
    eye = np.eye(P.shape[0], dtype=np.complex128)
    assert np.allclose(P.conj().T @ P, eye, atol=1e-10)


def test_gate_streaming_matches_permutation_unitary_small() -> None:
    # Compare output probabilities for a simple one-hot initial condition.
    nx, ny, nv = 2, 2, 16
    f0 = np.zeros((ny, nx, nv), dtype=float)
    f0[0, 0, 1] = 1.0  # D2Q9: E direction

    # Gate network qnode (current default)
    q_gate = build_osslbm_one_step_qnode(spec=OsslBmSpec(nx=nx, ny=ny, nv=nv, velocity_set="D2Q9"), f0=f0, jit=False)
    out_gate = q_gate()
    probs_gate = np.abs(out_gate) ** 2

    # Pure unitary streaming reference: replicate circuit using U_stream matrix.
    import pennylane as qml  # type: ignore

    n_wires = int(np.log2(nx)) + int(np.log2(ny)) + int(np.log2(nv))
    wires = list(range(n_wires))
    state = amplitude_encode_velocity_density(f0, nx=nx, ny=ny, nv=nv)
    Uc = collision_unitary(nv, theta=0.25)
    U_collision = np.kron(np.eye(nx * ny, dtype=np.complex128), Uc)
    U_stream = streaming_permutation_with_velocity_set(nx, ny, nv, velocity_set="D2Q9")
    dev = qml.device("default.qubit", wires=n_wires)

    @qml.qnode(dev)
    def circ_ref():  # type: ignore[no-untyped-def]
        qml.AmplitudeEmbedding(state, wires=wires, normalize=False)
        qml.QubitUnitary(U_collision, wires=wires)
        qml.QubitUnitary(U_stream, wires=wires)
        return qml.state()

    out_ref = circ_ref()
    probs_ref = np.abs(out_ref) ** 2

    assert np.allclose(probs_gate, probs_ref, atol=1e-10)

