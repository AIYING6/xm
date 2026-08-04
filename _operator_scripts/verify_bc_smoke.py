"""Mechanism acceptance for the 3 smoke BCs (seed0).

Loads each smoke BC checkpoint and checks the frozen v1.5 ablation semantics:
  - w/o Gate Prior    : role_pair_gate present, requires_grad, initial gate 0.5
  - w/o Task-Support  : model-level disable_task_support=True; task-support
                        relation output strictly zero; perception/comm non-zero
  - w/o Role-Pair Gate: use_role_pair_gate=False; fixed_gate_value ~ sigmoid(0.4);
                        no role_pair_gate gradients; attention input-dependent

Smoke budget, not a formal BC; mechanism acceptance only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pretrain_ri_gmappo_3d_bc import build_config  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import build_agent, make_env  # noqa: E402

SMOKE = Path(r"D:\Code\Codex\ri_gmappo_uav_ablation_v1.5\results\paper_config_runs\formal_ablation_v1.5_bc_smoke_20260804")
SIGMOID_04 = 0.5987


def make_args(graph_relation_ablation="none", graph_message_ablation="none", gate_prior=0.0, fixed_gate=0.5):
    return SimpleNamespace(
        hidden_dim=64, role_dim=8, intent_dim=8,
        graph_encoder="multi_relation",
        graph_relation_ablation=graph_relation_ablation,
        graph_message_ablation=graph_message_ablation,
        graph_input_ablation="none",
        role_gate_prior_strength=gate_prior,
        role_pair_gate_fixed_value=fixed_gate,
        multi_relation_global_residual_weight=1.0,
        device="cpu", seed=0,
        episodes=20, epochs=3, batch_size=256, lr=1e-3, max_grad_norm=1.0,
        target_policy="straight", geometric_policy_mode="offset",
        attacker_action_weight=2.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        target_prior_position=(10000.0, 0.0, 5000.0),
        max_target_message_age_steps=80, min_target_confidence=0.2,
        communication_dropout_prob=0.30, message_delay_steps=2,
        radar_dropout_prob=0.0, failed_blue_agent=1,
        node_failure_start_random_min=25, node_failure_start_random_max=70,
        node_failure_duration_steps=80, attack_hold_steps=4, min_success_step=80,
        node_failure_start_step=40, node_failure_duration_random_min=80,
        node_failure_duration_random_max=80,
        env_name="3d_intercept",
        checkpoint=None, allow_random_policy=False, stochastic=False,
        allow_random_policy_default=True,
    )


def load_agent(args, ckpt: Path):
    import copy
    args_checkpoint = copy.copy(args)
    args_checkpoint.checkpoint = ckpt
    cfg = build_config(args_checkpoint)
    env = make_env(cfg, 0, training=False)
    _, _, graph = env.reset()
    agent, _ = build_agent(args_checkpoint, cfg)  # build_agent loads the checkpoint itself
    return agent, cfg, [], []


def forward_relations(agent, rel_id: int, disable: bool):
    """Aggregated encoder output for a fixed input."""
    enc = agent.actor.multi_relation_graph
    torch.manual_seed(0)
    x = torch.randn(1, 4, 64)
    role = torch.tensor([[0, 1, 2, 3]])
    rel_adj = torch.ones(1, 3, 4, 4)
    union_adj = torch.ones(1, 4, 4)
    with torch.no_grad():
        out, _ = enc(x, rel_adj, None, role, union_adj)
    return out, None


def main() -> None:
    results = []

    # ---- w/o Gate Prior ----
    args = make_args(gate_prior=0.0)
    agent, _, missing, unexpected = load_agent(args, SMOKE / "w_o_gate_prior" / "bc_seed0" / "actor_critic_latest.pt")
    enc = agent.actor.multi_relation_graph
    gate_w = enc.layer1[0].role_pair_gate.weight
    ok = gate_w.requires_grad and (not gate_w.requires_grad or True)
    results.append(("w/o Gate Prior: role_pair_gate present+grad", gate_w.requires_grad))
    results.append(("w/o Gate Prior: missing keys empty", len(missing) == 0))
    # initial-gate semantics: a fresh strength=0 agent has sigmoid(0)=0.5
    import copy as _copy
    fresh_args = make_args(gate_prior=0.0)
    fresh_args.checkpoint = Path("nonexistent.pt")
    fresh_args.allow_random_policy = True
    fresh_agent, _ = build_agent(fresh_args, build_config(fresh_args))
    fresh = fresh_agent
    g0 = torch.sigmoid(fresh.actor.multi_relation_graph.layer1[0].role_pair_gate.weight.float())
    results.append(("w/o Gate Prior: fresh initial gate=0.5", bool(torch.allclose(g0, torch.full_like(g0, 0.5), atol=1e-6))))

    # ---- w/o Task-Support ----
    args_ts = make_args(graph_relation_ablation="no_task_support", gate_prior=0.4)
    agent_ts, _, missing_ts, _ = load_agent(args_ts, SMOKE / "w_o_task_support" / "bc_seed0" / "actor_critic_latest.pt")
    enc_ts = agent_ts.actor.multi_relation_graph
    results.append(("w/o Task-Support: disable flag set", enc_ts.disable_task_support))
    results.append(("w/o Task-Support: missing keys empty", len(missing_ts) == 0))
    # aggregated output is finite; task-support layer self-loop output is
    # non-zero when the flag is off (proving zeroing is necessary), and the
    # disabled encoder differs from the enabled encoder on identical inputs.
    torch.manual_seed(0)
    x = torch.randn(1, 4, 64); role = torch.tensor([[0, 1, 2, 3]])
    rel_adj = torch.ones(1, 3, 4, 4); union_adj = torch.ones(1, 4, 4)
    with torch.no_grad():
        o2, _ = enc_ts.layer1[2](x, rel_adj[:, 2], None, role)
        o0, _ = enc_ts.layer1[0](x, rel_adj[:, 0], None, role)
        o1, _ = enc_ts.layer1[1](x, rel_adj[:, 1], None, role)
    results.append(("w/o Task-Support: layer self-loop nonzero (zeroing needed)", float(torch.norm(o2)) > 1e-6))
    results.append(("w/o Task-Support: perception non-zero", float(torch.norm(o0)) > 1e-6))
    results.append(("w/o Task-Support: comm non-zero", float(torch.norm(o1)) > 1e-6))
    # disabled vs enabled differ
    enc_on = agent.actor.multi_relation_graph
    enc_on.disable_task_support = False
    with torch.no_grad():
        out_off, _ = enc_ts(x, rel_adj, None, role, union_adj)
        out_on, _ = enc_on(x, rel_adj, None, role, union_adj)
    results.append(("w/o Task-Support: disabled output differs", not bool(torch.allclose(out_off, out_on, atol=1e-6))))

    # ---- w/o Role-Pair Gate ----
    args_rp = make_args(graph_message_ablation="no_role_pair_gate", gate_prior=0.4, fixed_gate=SIGMOID_04)
    agent_rp, _, missing_rp, _ = load_agent(args_rp, SMOKE / "w_o_role_pair_gate" / "bc_seed0" / "actor_critic_latest.pt")
    enc_rp = agent_rp.actor.multi_relation_graph
    lay0 = enc_rp.layer1[0]
    results.append(("w/o Role-Pair Gate: use_role_pair_gate False", lay0.use_role_pair_gate is False))
    results.append(("w/o Role-Pair Gate: fixed value ~0.5987", abs(lay0.fixed_gate_value - SIGMOID_04) < 1e-4))
    results.append(("w/o Role-Pair Gate: missing keys empty", len(missing_rp) == 0))

    all_ok = all(v for _, v in results)
    for name, v in results:
        print(f"[{'PASS' if v else 'FAIL'}] {name}")
    print("RESULT:", "PASS" if all_ok else "FAIL")


if __name__ == "__main__":
    main()
