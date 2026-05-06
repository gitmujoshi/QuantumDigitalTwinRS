from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class QAPinnConfig:
    in_dim: int = 3  # (x, y, t)
    hidden_dim: int = 64
    hidden_layers: int = 4
    vqc_wires: int = 4
    vqc_layers: int = 2
    out_dim: int = 3  # (u, v, p)


def build_qapinn_model(cfg: QAPinnConfig) -> Any:
    """
    Build a QA-PINN model:
    - Classical MLP feature trunk (PyTorch)
    - PennyLane VQC layer via TorchLayer (StronglyEntanglingLayers)
    - Head producing (u, v, p)
    """
    try:
        import torch
        import torch.nn as nn
    except Exception as e:
        raise ImportError("PyTorch is required. Install `aeroq[qml]`.") from e

    try:
        import pennylane as qml  # type: ignore
    except Exception as e:
        raise ImportError("PennyLane is required. Install `aeroq[qml]`.") from e

    dev = qml.device("default.qubit", wires=cfg.vqc_wires)

    @qml.qnode(dev, interface="torch", diff_method="backprop")
    def vqc(inputs, weights):  # type: ignore[no-untyped-def]
        # inputs: (vqc_wires,) expected
        qml.AngleEmbedding(inputs, wires=range(cfg.vqc_wires), rotation="Y")
        qml.StronglyEntanglingLayers(weights, wires=range(cfg.vqc_wires))
        return [qml.expval(qml.PauliZ(i)) for i in range(cfg.vqc_wires)]

    weight_shapes = {"weights": (cfg.vqc_layers, cfg.vqc_wires, 3)}
    vqc_layer = qml.qnn.TorchLayer(vqc, weight_shapes)

    layers: list[nn.Module] = []
    layers.append(nn.Linear(cfg.in_dim, cfg.hidden_dim))
    layers.append(nn.Tanh())
    for _ in range(cfg.hidden_layers - 1):
        layers.append(nn.Linear(cfg.hidden_dim, cfg.hidden_dim))
        layers.append(nn.Tanh())
    trunk = nn.Sequential(*layers)

    # Project trunk features to VQC input dimension
    to_vqc = nn.Linear(cfg.hidden_dim, cfg.vqc_wires)
    # Combine trunk + vqc features
    head = nn.Sequential(
        nn.Linear(cfg.hidden_dim + cfg.vqc_wires, cfg.hidden_dim),
        nn.Tanh(),
        nn.Linear(cfg.hidden_dim, cfg.out_dim),
    )

    class QAPINN(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.trunk = trunk
            self.to_vqc = to_vqc
            self.vqc = vqc_layer
            self.head = head

        def forward(self, xyt):  # type: ignore[no-untyped-def]
            feats = self.trunk(xyt)
            vqc_in = self.to_vqc(feats)
            vqc_feats = self.vqc(vqc_in)
            both = torch.cat([feats, vqc_feats], dim=-1)
            out = self.head(both)
            return out

    return QAPINN()


def navier_stokes_residual_loss(
    model: Any,
    xyt: Any,
    *,
    nu: float = 0.01,
) -> Any:
    """
    Physics-informed loss for 2D incompressible Navier–Stokes (toy form).

    Model outputs: (u, v, p) as functions of (x, y, t).

    Residuals:
    - Continuity: u_x + v_y = 0
    - Momentum-x: u_t + u*u_x + v*u_y + p_x - nu*(u_xx + u_yy) = 0
    - Momentum-y: v_t + u*v_x + v*v_y + p_y - nu*(v_xx + v_yy) = 0
    """
    import torch

    xyt = xyt.requires_grad_(True)
    uvp = model(xyt)
    u = uvp[..., 0:1]
    v = uvp[..., 1:2]
    p = uvp[..., 2:3]

    def grad(outputs, inputs):  # type: ignore[no-untyped-def]
        return torch.autograd.grad(
            outputs,
            inputs,
            grad_outputs=torch.ones_like(outputs),
            create_graph=True,
            retain_graph=True,
        )[0]

    grads_u = grad(u, xyt)
    grads_v = grad(v, xyt)
    grads_p = grad(p, xyt)

    u_x, u_y, u_t = grads_u[..., 0:1], grads_u[..., 1:2], grads_u[..., 2:3]
    v_x, v_y, v_t = grads_v[..., 0:1], grads_v[..., 1:2], grads_v[..., 2:3]
    p_x, p_y = grads_p[..., 0:1], grads_p[..., 1:2]

    u_xx = grad(u_x, xyt)[..., 0:1]
    u_yy = grad(u_y, xyt)[..., 1:2]
    v_xx = grad(v_x, xyt)[..., 0:1]
    v_yy = grad(v_y, xyt)[..., 1:2]

    continuity = u_x + v_y
    mom_x = u_t + u * u_x + v * u_y + p_x - nu * (u_xx + u_yy)
    mom_y = v_t + u * v_x + v * v_y + p_y - nu * (v_xx + v_yy)

    return (continuity.square().mean() + mom_x.square().mean() + mom_y.square().mean())


def supervised_mse_loss(model: Any, xyt: Any, uvp_target: Any) -> Any:
    import torch

    pred = model(xyt)
    return torch.nn.functional.mse_loss(pred, uvp_target)


def train_step(
    model: Any,
    optimizer: Any,
    *,
    xyt_collocation: Any,
    xyt_supervised: Any | None = None,
    uvp_supervised: Any | None = None,
    nu: float = 0.01,
    w_phys: float = 1.0,
    w_sup: float = 1.0,
) -> dict[str, float]:
    import torch

    model.train()
    optimizer.zero_grad(set_to_none=True)

    phys = navier_stokes_residual_loss(model, xyt_collocation, nu=nu)
    loss = w_phys * phys

    sup_val = None
    if xyt_supervised is not None and uvp_supervised is not None:
        sup = supervised_mse_loss(model, xyt_supervised, uvp_supervised)
        loss = loss + w_sup * sup
        sup_val = float(sup.detach().cpu().item())

    loss.backward()
    optimizer.step()

    out = {"loss": float(loss.detach().cpu().item()), "physics": float(phys.detach().cpu().item())}
    if sup_val is not None:
        out["supervised"] = sup_val
    return out

