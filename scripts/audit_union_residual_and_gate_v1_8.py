"""Low-cost structural audit of EA-RG channels, residual and role-pair gates."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import MultiRelationGraphEncoder  # noqa: E402


def entropy(weights: torch.Tensor) -> float:
    p = weights.clamp_min(1e-8)
    return float((-(p * p.log()).sum(dim=-1)).mean().item())


def audit(checkpoint: Path | None, seed: int = 913):
    torch.manual_seed(seed)
    model = MultiRelationGraphEncoder(32, 18, 5)
    label = "random_init" if checkpoint is None else str(checkpoint)
    if checkpoint is not None and checkpoint.exists():
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        own = {k[len("actor.multi_relation_graph."):]: v for k, v in state.items()
               if k.startswith("actor.multi_relation_graph.")}
        model.load_state_dict(own, strict=True)
    b, n, h = 64, 4, 32
    x = torch.randn(b, n, h, requires_grad=True)
    edge = torch.randn(b, n, n, 18)
    role = torch.randint(0, 5, (b, n))
    rel = torch.randint(0, 2, (b, 3, n, n)).float()
    rel[:, :, torch.arange(n), torch.arange(n)] = 1.0
    union = rel.amax(dim=1)
    outputs = []; attns = []
    layers = model.layer1
    for rid, layer in enumerate(layers):
        out, attn = layer(x, rel[:, rid], edge, role)
        outputs.append(out); attns.append(attn)
    global_out, global_attn = model.global_layer1(x, union, edge)
    channel_norms = [float(v.norm(dim=-1).mean().item()) for v in outputs]
    global_norm = float(global_out.norm(dim=-1).mean().item())
    total = sum(channel_norms) + model.global_residual_weight * global_norm
    fused = model.fuse1(torch.cat(outputs + [global_out * model.global_residual_weight], dim=-1))
    (fused.square().mean()).backward()
    relation_grad = []
    for layer in model.layer1:
        relation_grad.append(float(sum((p.grad.norm().item() ** 2) for p in layer.parameters() if p.grad is not None) ** 0.5))
    global_grad = float(sum((p.grad.norm().item() ** 2) for p in model.global_layer1.parameters() if p.grad is not None) ** 0.5)
    gate = torch.sigmoid(model.layer1[0].role_pair_gate.weight.detach())
    gate_variation = float(gate.std().item())
    gate_nontrivial = float((gate.max() - gate.min()).item())
    # Representation sensitivity to removing the learned role-pair variation.
    ablated = copy.deepcopy(model)
    ablated.zero_grad()
    with torch.no_grad():
        for layer in ablated.layer1:
            layer.role_pair_gate.weight.zero_()
    out_ab, _ = ablated.layer1[0](x.detach(), rel[:, 0], edge, role)
    role_repr_delta = float((outputs[0].detach() - out_ab).norm(dim=-1).mean().item())
    return {
        "label": label, "relation_channel_norms": channel_norms,
        "union_residual_norm": global_norm,
        "union_share_of_input_norm": float(model.global_residual_weight * global_norm / total),
        "fused_output_norm": float(fused.detach().norm(dim=-1).mean().item()),
        "relation_gradient_norms": relation_grad, "union_gradient_norm": global_grad,
        "union_share_of_gradient_norm": float(global_grad / (global_grad + sum(relation_grad))),
        "relation_attention_entropy_mean": float(np.mean([entropy(a) for a in attns])),
        "union_attention_entropy": entropy(global_attn),
        "role_pair_gate_std": gate_variation, "role_pair_gate_range": gate_nontrivial,
        "role_pair_representation_delta": role_repr_delta,
    }


if __name__ == "__main__":
    for ckpt in (None, ROOT / "results/actor_boundary_pilot_ea/actor_critic_latest.pt"):
        print(audit(ckpt))
