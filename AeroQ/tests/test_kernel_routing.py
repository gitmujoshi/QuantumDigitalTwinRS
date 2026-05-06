import numpy as np

from aeroq.kernel import AeroQKernel


def test_solve_linear_system_runs(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "\n".join(
            [
                "backend: pennylane_amd",
                "pennylane_amd:",
                "  device: default.qubit",
                "  wires: 4",
                "  shots: null",
                "qiskit_ibm:",
                "  instance: null",
                "  backend_name: null",
                "  prefer_simulator: true",
                "  shots: 1024",
                "",
            ]
        )
    )

    k = AeroQKernel(config_path=cfg)
    A = np.array([[2.0, 0.0], [0.0, 5.0]])
    b = np.array([4.0, 10.0])
    x = k.solve_linear_system(A, b)
    assert np.allclose(x, np.array([2.0, 2.0]))

