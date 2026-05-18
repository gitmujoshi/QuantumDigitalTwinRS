from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .qsvt import catalyst_jit_if_available


@dataclass(frozen=True)
class OsslBmSpec:
    """
    One-step simplified Lattice Boltzmann (OSSLBM) circuit spec.

    This is an R&D-friendly scaffold:
    - **Amplitude encoding** loads an initial velocity-density distribution over a 2D grid.
    - **Collision** is modeled as a unitary acting on the velocity subspace (shared across positions).
    - **Streaming** is modeled as a unitary permutation of basis states that shifts populations
      according to velocity directions (periodic boundaries).

    The goal is to provide a clean place to iterate on realistic collision models and streaming networks,
    while remaining executable on simulators and suitable for GPU-accelerated backends.
    """

    nx: int
    ny: int
    nv: int  # number of discrete velocities (must be power-of-two for this scaffold)
    velocity_set: str = "D2Q4"  # "D2Q4" or "D2Q9" (embedded in power-of-two nv via padding)
    collision_theta: float = 0.25
    device: str = "lightning.gpu"  # AMD MI300X target path (if available)


def _is_power_of_two(x: int) -> bool:
    return x > 0 and (x & (x - 1) == 0)


def _num_qubits_for_dim(n: int) -> int:
    if n <= 0 or not _is_power_of_two(n):
        raise ValueError("Dimensions must be positive powers of two for this scaffold.")
    return int(np.log2(n))


def _flat_index(x: int, y: int, v: int, *, nx: int, ny: int, nv: int) -> int:
    return (y * nx + x) * nv + v


def _unflat_index(i: int, *, nx: int, ny: int, nv: int) -> tuple[int, int, int]:
    v = i % nv
    ij = i // nv
    x = ij % nx
    y = ij // nx
    return x, y, v


def _velocity_to_shift(v: int, *, velocity_set: str, nv: int) -> tuple[int, int]:
    """
    Map discrete velocity index → (dx, dy).

    Supported sets:
    - D2Q4 (requires nv>=4): 4 axial directions
    - D2Q9 (requires nv>=9): 8 directions + rest (0,0)

    Note: D2Q9 has 9 velocities; this scaffold keeps `nv` as a power-of-two by padding
    (e.g. nv=16) and mapping unused channels to (0,0).
    """
    vs = str(velocity_set).upper().strip()
    if vs == "D2Q4":
        if nv < 4:
            raise ValueError("D2Q4 requires nv>=4")
        # (E, W, N, S)
        if v == 0:
            return (1, 0)
        if v == 1:
            return (-1, 0)
        if v == 2:
            return (0, 1)
        if v == 3:
            return (0, -1)
        return (0, 0)

    if vs == "D2Q9":
        if nv < 9:
            raise ValueError("D2Q9 requires nv>=9 (use nv=16 in this scaffold).")
        # Common D2Q9 indexing:
        # 0: rest, 1:E, 2:N, 3:W, 4:S, 5:NE, 6:NW, 7:SW, 8:SE
        mapping = {
            0: (0, 0),
            1: (1, 0),
            2: (0, 1),
            3: (-1, 0),
            4: (0, -1),
            5: (1, 1),
            6: (-1, 1),
            7: (-1, -1),
            8: (1, -1),
        }
        return mapping.get(v, (0, 0))

    raise ValueError(f"Unsupported velocity_set: {velocity_set!r}")


def amplitude_encode_velocity_density(
    f0: np.ndarray,
    *,
    nx: int,
    ny: int,
    nv: int,
) -> np.ndarray:
    """
    Convert a (ny, nx, nv) velocity-density tensor into a normalized amplitude vector.
    """
    arr = np.asarray(f0, dtype=float)
    if arr.shape != (ny, nx, nv):
        raise ValueError(f"Expected f0 shape {(ny, nx, nv)}, got {arr.shape}.")

    flat = arr.reshape((-1,))
    if np.any(flat < 0):
        raise ValueError("f0 must be non-negative for amplitude encoding in this scaffold.")

    # Amplitude encoding: encode sqrt(density) as amplitudes (then normalize).
    amps = np.sqrt(flat)
    norm = float(np.linalg.norm(amps))
    if norm < 1e-12:
        raise ValueError("f0 is all zeros; cannot amplitude-encode.")
    return (amps / norm).astype(np.complex128)


def collision_unitary(nv: int, theta: float) -> np.ndarray:
    """
    Return a simple unitary acting on the velocity subspace (size nv).

    This is a *toy collision* operator: it mixes velocity channels via a block-diagonal rotation.
    Replace with a physics-motivated unitary as research progresses.
    """
    if not _is_power_of_two(nv):
        raise ValueError("nv must be a power of two.")
    if nv < 2:
        return np.eye(nv, dtype=np.complex128)

    # Pairwise mixing: for channels (0,1), (2,3), ... apply same 2x2 rotation.
    c = float(np.cos(theta))
    s = float(np.sin(theta))
    r = np.array([[c, -s], [s, c]], dtype=np.complex128)

    U = np.eye(nv, dtype=np.complex128)
    for k in range(0, nv, 2):
        U[k : k + 2, k : k + 2] = r
    return U


def streaming_permutation(nx: int, ny: int, nv: int) -> np.ndarray:
    """
    Build the full streaming permutation matrix over the flattened state space.

    This is implemented as a dense permutation matrix for clarity and correctness.
    For larger grids, replace with a structured SWAP/controlled-SWAP network.
    """
    dim = nx * ny * nv
    P = np.zeros((dim, dim), dtype=np.complex128)

    for i in range(dim):
        x, y, v = _unflat_index(i, nx=nx, ny=ny, nv=nv)
        dx, dy = _velocity_to_shift(v, velocity_set="D2Q4", nv=nv)
        x2 = (x + dx) % nx
        y2 = (y + dy) % ny
        j = _flat_index(x2, y2, v, nx=nx, ny=ny, nv=nv)
        P[j, i] = 1.0
    return P


def streaming_permutation_with_velocity_set(nx: int, ny: int, nv: int, *, velocity_set: str) -> np.ndarray:
    """
    Same as `streaming_permutation`, but configurable velocity set.
    """
    dim = nx * ny * nv
    P = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(dim):
        x, y, v = _unflat_index(i, nx=nx, ny=ny, nv=nv)
        dx, dy = _velocity_to_shift(v, velocity_set=velocity_set, nv=nv)
        x2 = (x + dx) % nx
        y2 = (y + dy) % ny
        j = _flat_index(x2, y2, v, nx=nx, ny=ny, nv=nv)
        P[j, i] = 1.0
    return P


def _bits_lsb_first(value: int, nbits: int) -> list[int]:
    return [(value >> i) & 1 for i in range(nbits)]


def _bits_msb_first(value: int, nbits: int) -> list[int]:
    return [((value >> (nbits - 1 - i)) & 1) for i in range(nbits)]


def _increment_mod_2n(wires: Sequence[int]) -> None:
    """
    In-place add 1 mod 2^n on `wires` (LSB-first).

    Gate network:
    - X on bit0
    - MCX on bit1 controlled by bit0==1
    - MCX on bit2 controlled by bit0..bit1==1
    - ...
    """
    import pennylane as qml  # type: ignore

    ws = list(wires)
    if not ws:
        return
    qml.PauliX(ws[0])
    for k in range(1, len(ws)):
        qml.MultiControlledX(wires=list(ws[:k]) + [ws[k]], control_values=[1] * k)


def _decrement_mod_2n(wires: Sequence[int]) -> None:
    """
    In-place subtract 1 mod 2^n on `wires` (LSB-first).

    Equivalent to increment on bitwise-not representation:
    x := ~x; x := x+1; x := ~x
    """
    import pennylane as qml  # type: ignore

    ws = list(wires)
    for w in ws:
        qml.PauliX(w)
    _increment_mod_2n(ws)
    for w in ws:
        qml.PauliX(w)

def _controlled_x_on_velocity(*, value: int, vel_wires: Sequence[int], target_wire: int) -> None:
    """
    Apply X(target_wire) controlled on velocity register equaling `value`.
    Assumes vel_wires is in wire-order (MSB->LSB).
    """
    import pennylane as qml  # type: ignore

    bits = _bits_msb_first(value, len(vel_wires))
    qml.MultiControlledX(wires=list(vel_wires) + [target_wire], control_values=bits)


def _controlled_increment_mod_2n(*, value: int, vel_wires: Sequence[int], reg_lsb_wires: Sequence[int]) -> None:
    """
    Apply (reg := reg + 1 mod 2^n) controlled on velocity == value.
    `reg_lsb_wires` must be LSB-first.
    """
    import pennylane as qml  # type: ignore

    bits = _bits_msb_first(value, len(vel_wires))
    ws = list(reg_lsb_wires)
    if not ws:
        return

    # Bit0 flip controlled by velocity pattern.
    qml.MultiControlledX(wires=list(vel_wires) + [ws[0]], control_values=bits)

    # Carry chain: flip bit k when all lower bits are 1 AND velocity matches.
    for k in range(1, len(ws)):
        control_wires = list(vel_wires) + ws[:k]
        control_values = bits + [1] * k
        qml.MultiControlledX(wires=control_wires + [ws[k]], control_values=control_values)


def _controlled_decrement_mod_2n(*, value: int, vel_wires: Sequence[int], reg_lsb_wires: Sequence[int]) -> None:
    """
    Apply (reg := reg - 1 mod 2^n) controlled on velocity == value.
    """
    # x := ~x; x := x+1; x := ~x, all under the same velocity control.
    for w in reg_lsb_wires:
        _controlled_x_on_velocity(value=value, vel_wires=vel_wires, target_wire=w)
    _controlled_increment_mod_2n(value=value, vel_wires=vel_wires, reg_lsb_wires=reg_lsb_wires)
    for w in reg_lsb_wires:
        _controlled_x_on_velocity(value=value, vel_wires=vel_wires, target_wire=w)


def streaming_gate_network(
    *,
    nx: int,
    ny: int,
    nv: int,
    velocity_set: str,
    x_wires: Sequence[int],
    y_wires: Sequence[int],
    vel_wires: Sequence[int],
) -> None:
    """
    Gate-level streaming operator: conditionally shift (x,y) based on velocity value.

    This avoids building a giant dense permutation matrix and is closer to a hardware-style streaming step.
    It assumes nx, ny, nv are powers of two (mod arithmetic is natural).
    """
    import pennylane as qml  # type: ignore

    if not (_is_power_of_two(nx) and _is_power_of_two(ny) and _is_power_of_two(nv)):
        raise ValueError("nx, ny, nv must be powers of two for gate-level streaming.")

    vs = str(velocity_set).upper().strip()
    if vs not in ("D2Q4", "D2Q9"):
        raise ValueError(f"Unsupported velocity_set: {velocity_set!r}")

    # Define controlled shifts for each velocity channel.
    # Arithmetic helpers expect LSB-first wires, but PennyLane wire-order is typically MSB->LSB.
    x_lsb = list(reversed(list(x_wires)))
    y_lsb = list(reversed(list(y_wires)))

    if vs == "D2Q4":
        # v=0:E, v=1:W, v=2:N, v=3:S
        _controlled_increment_mod_2n(value=0, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
        _controlled_decrement_mod_2n(value=1, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
        _controlled_increment_mod_2n(value=2, vel_wires=vel_wires, reg_lsb_wires=y_lsb)
        _controlled_decrement_mod_2n(value=3, vel_wires=vel_wires, reg_lsb_wires=y_lsb)
        return

    # D2Q9: 0 rest, 1:E,2:N,3:W,4:S,5:NE,6:NW,7:SW,8:SE (>=9 are padding/no-op)
    _controlled_increment_mod_2n(value=1, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_increment_mod_2n(value=2, vel_wires=vel_wires, reg_lsb_wires=y_lsb)
    _controlled_decrement_mod_2n(value=3, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_decrement_mod_2n(value=4, vel_wires=vel_wires, reg_lsb_wires=y_lsb)

    # Diagonals: do both shifts under the same velocity-control.
    _controlled_increment_mod_2n(value=5, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_increment_mod_2n(value=5, vel_wires=vel_wires, reg_lsb_wires=y_lsb)

    _controlled_decrement_mod_2n(value=6, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_increment_mod_2n(value=6, vel_wires=vel_wires, reg_lsb_wires=y_lsb)

    _controlled_decrement_mod_2n(value=7, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_decrement_mod_2n(value=7, vel_wires=vel_wires, reg_lsb_wires=y_lsb)

    _controlled_increment_mod_2n(value=8, vel_wires=vel_wires, reg_lsb_wires=x_lsb)
    _controlled_decrement_mod_2n(value=8, vel_wires=vel_wires, reg_lsb_wires=y_lsb)


def build_osslbm_one_step_qnode(
    *,
    spec: OsslBmSpec,
    f0: np.ndarray,
    jit: bool = True,
):
    """
    Build a PennyLane QNode that performs one OSSL-BM step (collision + streaming).

    Backend targeting:
    - Uses `lightning.gpu` when available (intended for AMD MI300X).
    - Falls back to `default.qubit` if the requested device is unavailable.
    - Optionally wrapped by `catalyst.jit` if Catalyst is installed and `jit=True`.
    """
    try:
        import pennylane as qml  # type: ignore
    except Exception as e:
        raise ImportError("PennyLane is required. Install `aeroq[pennylane_amd,qsvt]`.") from e

    if not (_is_power_of_two(spec.nx) and _is_power_of_two(spec.ny) and _is_power_of_two(spec.nv)):
        raise ValueError("nx, ny, nv must be powers of two for this scaffold.")

    n_pos = _num_qubits_for_dim(spec.nx) + _num_qubits_for_dim(spec.ny)
    n_vel = _num_qubits_for_dim(spec.nv)
    n_wires = n_pos + n_vel
    wires = list(range(n_wires))

    state = amplitude_encode_velocity_density(f0, nx=spec.nx, ny=spec.ny, nv=spec.nv)

    # Device selection for AMD GPU simulator path.
    try:
        dev = qml.device(spec.device, wires=n_wires)
    except Exception:
        dev = qml.device("default.qubit", wires=n_wires)

    Uc = collision_unitary(spec.nv, spec.collision_theta)
    # Lift collision to full space: I_pos ⊗ U_vel
    U_collision = np.kron(np.eye(spec.nx * spec.ny, dtype=np.complex128), Uc)
    U_stream = streaming_permutation_with_velocity_set(spec.nx, spec.ny, spec.nv, velocity_set=spec.velocity_set)

    # Wire-order is MSB->LSB in PennyLane's state-indexing.
    # Our dense permutation uses flattened ordering where y is more-significant than x:
    # index = ((y * nx + x) * nv + v). To match that layout at the gate level, place
    # y-wires before x-wires in wire-order.
    n_x = _num_qubits_for_dim(spec.nx)
    n_y = _num_qubits_for_dim(spec.ny)
    y_wires = wires[:n_y]
    x_wires = wires[n_y : n_y + n_x]
    vel_wires = wires[n_y + n_x :]

    @qml.qnode(dev)
    def _circuit():  # type: ignore[no-untyped-def]
        qml.AmplitudeEmbedding(state, wires=wires, normalize=False)
        qml.QubitUnitary(U_collision, wires=wires)
        # Gate-level streaming network (structured). Keep unitary matrix available for validation/debug.
        streaming_gate_network(
            nx=spec.nx,
            ny=spec.ny,
            nv=spec.nv,
            velocity_set=spec.velocity_set,
            x_wires=x_wires,
            y_wires=y_wires,
            vel_wires=vel_wires,
        )
        return qml.state()

    if jit:
        return catalyst_jit_if_available(_circuit)
    return _circuit

