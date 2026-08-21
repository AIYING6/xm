#!/usr/bin/env python3
"""Read-only EDR-Q2 structural audit on a frozen relay-failure record.

This script neither instantiates an environment nor writes/updates a model.  The
EDR branch is an analytical, parameter-reusing aggregation prototype; its action
outputs are structural propagation diagnostics and explicitly not performance
evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import torch
import torch.nn.functional as F

PROTOCOL = "EDR-Q2-STRUCTURAL-PROPERTY-AUDIT-V1"
RECEIVER_ATTACKER = 2
SENDER_RELAY = 1
FIXED_C = 4.0


def find_record(raw_path: Path, post_step: int) -> dict:
    pattern = rf'"post_step":{post_step},.*"scenario":"f0_seen_44_80"'
    result = subprocess.run(["rg", "-m", "1", pattern, str(raw_path)], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def tensor(value, dtype=torch.float32):
    return torch.tensor(value, dtype=dtype).unsqueeze(0)


def linear(x: torch.Tensor, weight: torch.Tensor, bias: torch.Tensor | None = None) -> torch.Tensor:
    out = x @ weight.T
    return out if bias is None else out + bias


def scores_and_payload(x, adj, edge, state, prefix):
    h = linear(x, state[f"actor.{prefix}.proj.weight"])
    b, n, d = h.shape
    hi = h.unsqueeze(2).expand(b, n, n, d)
    hj = h.unsqueeze(1).expand(b, n, n, d)
    score = linear(torch.cat([hi, hj], dim=-1), state[f"actor.{prefix}.attn.weight"]).squeeze(-1)
    edge_hidden = torch.tanh(linear(edge, state[f"actor.{prefix}.edge_score.0.weight"], state[f"actor.{prefix}.edge_score.0.bias"]))
    score = F.leaky_relu(score + linear(edge_hidden, state[f"actor.{prefix}.edge_score.2.weight"]).squeeze(-1), negative_slope=0.2)
    eye = torch.eye(n, dtype=adj.dtype).unsqueeze(0)
    mask = torch.clamp(adj + eye, 0.0, 1.0)
    return score, h, mask


def aggregate(x, adj, edge, state, prefix, edr: bool):
    score, h, mask = scores_and_payload(x, adj, edge, state, prefix)
    if edr:
        gate = torch.sigmoid(score) * mask
        contribution = gate.unsqueeze(-1) * h.unsqueeze(1)
        out = torch.tanh(contribution.sum(dim=2) / FIXED_C)
        return out, gate, contribution
    weights = torch.softmax(score.masked_fill(mask <= 0.0, -1e9), dim=-1)
    contribution = weights.unsqueeze(-1) * h.unsqueeze(1)
    out = torch.tanh(contribution.sum(dim=2))
    return out, weights, contribution


def actor_logits(record, state, edr: bool, adj_override=None):
    actor = record["actor"]
    obs = tensor(actor["obs"])
    node = tensor(actor["graph_node_feat"])
    edge = tensor(actor["graph_edge_feat"])
    role = torch.tensor(actor["graph_role"], dtype=torch.long).unsqueeze(0)
    adj = tensor(actor["graph_adj"]) if adj_override is None else adj_override
    role_emb = state["actor.role_emb.weight"][role]
    x = torch.tanh(linear(torch.cat([node, role_emb], dim=-1), state["actor.input.0.weight"], state["actor.input.0.bias"]))
    x, weights1, contrib1 = aggregate(x, adj, edge, state, "gat1", edr)
    x, weights2, contrib2 = aggregate(x, adj, edge, state, "gat2", edr)
    graph = x[:, :3]
    target = x[:, 3:]
    intent = linear(torch.tanh(linear(target, state["actor.intent_head.0.weight"], state["actor.intent_head.0.bias"])), state["actor.intent_head.2.weight"], state["actor.intent_head.2.bias"])
    intent_context = (torch.softmax(intent, dim=-1) @ state["actor.intent_emb.weight"]).mean(dim=1).unsqueeze(1).expand(-1, 3, -1)
    obs_feat = torch.tanh(linear(obs, state["actor.obs_encoder.0.weight"], state["actor.obs_encoder.0.bias"]))
    logits = linear(torch.tanh(linear(torch.cat([obs_feat, graph, intent_context], dim=-1), state["actor.policy_head.0.weight"], state["actor.policy_head.0.bias"])), state["actor.policy_head.2.weight"], state["actor.policy_head.2.bias"])
    return logits, {"weights1": weights1, "weights2": weights2, "contrib1": contrib1, "contrib2": contrib2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-telemetry", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")

    # `failure_active_post` becomes one after the transition at step 44.  The
    # actor's first subsequent input graph is therefore the record at step 45,
    # not the pre-decision graph recorded at step 44.
    pre = find_record(args.raw_telemetry, 43)
    post = find_record(args.raw_telemetry, 45)
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    pre_adj = tensor(pre["actor"]["graph_adj"])
    synthetic = pre_adj.clone()
    synthetic[0, RECEIVER_ATTACKER, SENDER_RELAY] = 0.0

    sg_pre_logits, sg_pre = actor_logits(pre, state, edr=False)
    sg_del_logits, sg_del = actor_logits(pre, state, edr=False, adj_override=synthetic)
    edr_pre_logits, edr_pre = actor_logits(pre, state, edr=True)
    edr_del_logits, edr_del = actor_logits(pre, state, edr=True, adj_override=synthetic)

    survivor = [node for node in range(4) if node != SENDER_RELAY]
    sg_survivor_delta = (sg_del["contrib1"][0, RECEIVER_ATTACKER, survivor] - sg_pre["contrib1"][0, RECEIVER_ATTACKER, survivor]).norm().item()
    edr_survivor_delta = (edr_del["contrib1"][0, RECEIVER_ATTACKER, survivor] - edr_pre["contrib1"][0, RECEIVER_ATTACKER, survivor]).norm().item()
    sg_weight_delta = (sg_del["weights1"][0, RECEIVER_ATTACKER, survivor] - sg_pre["weights1"][0, RECEIVER_ATTACKER, survivor]).abs().max().item()
    edr_gate_delta = (edr_del["weights1"][0, RECEIVER_ATTACKER, survivor] - edr_pre["weights1"][0, RECEIVER_ATTACKER, survivor]).abs().max().item()
    transition = {
        "scheduled_onset": pre["scheduled_failure_onset"], "pre_step": pre["post_step"], "post_step": post["post_step"],
        "failure_active_pre": pre["failure_active_post"], "failure_active_post": post["failure_active_post"],
        "relay_to_attacker_pre": float(pre_adj[0, RECEIVER_ATTACKER, SENDER_RELAY]),
        "relay_to_attacker_post": float(tensor(post["actor"]["graph_adj"])[0, RECEIVER_ATTACKER, SENDER_RELAY]),
        "direct_scout_to_attacker_pre": float(pre_adj[0, RECEIVER_ATTACKER, 0]),
        "direct_scout_to_attacker_post": float(tensor(post["actor"]["graph_adj"])[0, RECEIVER_ATTACKER, 0]),
    }
    result = {
        "protocol": PROTOCOL, "offline_only": True, "no_environment_constructed": True, "no_optimizer_update": True,
        "checkpoint_parameters": int(sum(value.numel() for value in state.values())), "fixed_normalizer_C": FIXED_C,
        "recorded_transition": transition,
        "test_A_existing_sg_vulnerability": {"surviving_weight_max_delta": sg_weight_delta, "surviving_contribution_l2_delta": sg_survivor_delta, "aggregate_l2_delta": (sg_del["contrib1"][0, RECEIVER_ATTACKER].sum(0) - sg_pre["contrib1"][0, RECEIVER_ATTACKER].sum(0)).norm().item(), "pass": sg_weight_delta > 0 and sg_survivor_delta > 0},
        "test_B_edr_locality": {"surviving_gate_max_delta": edr_gate_delta, "surviving_contribution_l2_delta": edr_survivor_delta, "pass": edr_gate_delta == 0.0 and edr_survivor_delta == 0.0},
        "test_C_relay_failure_relevance": {"pass": transition["scheduled_onset"] == 44 and transition["pre_step"] == 43 and transition["post_step"] == 45 and transition["failure_active_pre"] == 0 and transition["failure_active_post"] == 1 and transition["relay_to_attacker_pre"] == 1.0 and transition["relay_to_attacker_post"] == 0.0 and transition["direct_scout_to_attacker_post"] == 1.0},
        "test_D_structural_action_propagation": {"sg_logit_l2": (sg_del_logits - sg_pre_logits).norm().item(), "analytic_edr_logit_l2": (edr_del_logits - edr_pre_logits).norm().item(), "not_performance_evidence": True},
        "actor_legality": {"used": ["existing obs", "existing node_feat", "existing edge_feat", "existing role", "existing adjacency"], "forbidden": ["failure label", "global route", "future state", "share_obs"]},
        "caveat": "The EDR calculations reuse trained SG parameters with an analytical fixed-normalization/sigmoid operator. They verify deletion-local propagation, not trained-policy performance or robustness.",
    }
    args.output_root.mkdir(parents=True)
    (args.output_root / "edr_q2_structural_property_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "completed", "A": result["test_A_existing_sg_vulnerability"]["pass"], "B": result["test_B_edr_locality"]["pass"], "C": result["test_C_relay_failure_relevance"]["pass"]}, indent=2))


if __name__ == "__main__":
    main()
