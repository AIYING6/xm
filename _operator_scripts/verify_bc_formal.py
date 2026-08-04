"""9/9 formal BC acceptance audit.

For each (ablation, seed): load the BC checkpoint through the official chain,
check architecture (state-dict keys = 50, total params = 96,384), mechanism
flags per ablation, and record SHA. Usage:
  python verify_bc_formal.py [--only ablation,seed] [--out report]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pretrain_ri_gmappo_3d_bc import build_config  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import build_agent, make_env  # noqa: E402

OUT_ROOT = ROOT / "results" / "paper_config_runs" / "formal_ablation_v1.5_bc_freeze_20260804"
SIGMOID_04 = 0.598687660112452
# BC checkpoint is the full RIGMAPPOAgent (actor + critic + graph), verified by
# the first formal BC (w_o_gate_prior/seed0) and required to match v1.4 Full BC.
EXPECTED_KEYS = 74
EXPECTED_PARAMS = 117302

ABLATIONS = {
    "w_o_gate_prior": {"rel": "none", "msg": "none", "prior": 0.0, "fixed": 0.5, "sem": "gate_prior"},
    "w_o_task_support": {"rel": "no_task_support", "msg": "none", "prior": 0.4, "fixed": 0.5, "sem": "task_support"},
    "w_o_role_pair_gate": {"rel": "none", "msg": "no_role_pair_gate", "prior": 0.4, "fixed": SIGMOID_04, "sem": "role_pair_gate"},
}


def make_args(abl: dict):
    return SimpleNamespace(
        hidden_dim=64, role_dim=8, intent_dim=8,
        graph_encoder="multi_relation",
        graph_relation_ablation=abl["rel"],
        graph_message_ablation=abl["msg"],
        graph_input_ablation="none",
        role_gate_prior_strength=abl["prior"],
        role_pair_gate_fixed_value=abl["fixed"],
        multi_relation_global_residual_weight=1.0,
        device="cpu", seed=0,
        episodes=120, epochs=20, batch_size=256, lr=1e-3, max_grad_norm=1.0,
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


def load_agent(abl: dict, ckpt: Path):
    args = make_args(abl)
    args.checkpoint = ckpt
    cfg = build_config(args)
    env = make_env(cfg, 0, training=False)
    _, _, graph = env.reset()
    agent, _ = build_agent(args, cfg)
    return agent, cfg


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def full_bc_keys() -> set[str]:
    """v1.4 Full EA-RG BC state-dict keys (architecture reference)."""
    p = Path(r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\ea_rg_mappo_s_gate_prior\bc_seed0\actor_critic_latest.pt")
    if p.exists():
        return set(torch.load(p, map_location="cpu").keys())
    return set()


def check_semantics(agent, sem: str) -> list[tuple[str, bool]]:
    enc = agent.actor.multi_relation_graph
    out = []
    if sem == "gate_prior":
        gate_w = enc.layer1[0].role_pair_gate.weight
        out.append(("gate param exists", gate_w is not None))
        out.append(("gate learnable", gate_w.requires_grad))
    elif sem == "task_support":
        out.append(("disable_task_support flag", enc.disable_task_support))
        torch.manual_seed(0)
        x = torch.randn(1, 4, 64); role = torch.tensor([[0, 1, 2, 3]])
        rel_adj = torch.ones(1, 3, 4, 4); union_adj = torch.ones(1, 4, 4)
        with torch.no_grad():
            o2, _ = enc.layer1[2](x, rel_adj[:, 2], None, role)
            o0, _ = enc.layer1[0](x, rel_adj[:, 0], None, role)
            o1, _ = enc.layer1[1](x, rel_adj[:, 1], None, role)
        out.append(("self-loop nonzero (zeroing needed)", float(torch.norm(o2)) > 1e-6))
        out.append(("perception nonzero", float(torch.norm(o0)) > 1e-6))
        out.append(("comm nonzero", float(torch.norm(o1)) > 1e-6))
    else:  # role_pair_gate
        lay = enc.layer1[0]
        out.append(("use_role_pair_gate False", lay.use_role_pair_gate is False))
        out.append(("fixed gate ~0.598687660112452", abs(lay.fixed_gate_value - SIGMOID_04) < 1e-9))
        out.append(("embedding retained", hasattr(lay, "role_pair_gate")))
        torch.manual_seed(0)
        x = torch.randn(1, 4, 64); role = torch.tensor([[0, 1, 2, 3]])
        adj = torch.ones(1, 4, 4)
        with torch.no_grad():
            _, w1 = enc.layer1[0](x, adj, None, role)
            _, w2 = enc.layer1[0](x + 0.5, adj, None, role)
        out.append(("attention input-dependent", not torch.allclose(w1, w2, atol=1e-6)))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None, help="ablation,seed")
    parser.add_argument("--out", type=Path, default=OUT_ROOT / "_bc_operator_notes" / "v1.5_bc_semantics_audit.md")
    args = parser.parse_args()

    lines = ["# v1.5 Formal BC Semantics Audit", "", f"generated: (see end)", ""]
    all_ok = True
    rows = []
    for abl, cfg in ABLATIONS.items():
        for seed in (0, 1, 2):
            if args.only and args.only != f"{abl},{seed}":
                continue
            ckpt = OUT_ROOT / abl / f"bc_seed{seed}" / "actor_critic_latest.pt"
            lines.append(f"## {abl} seed{seed}")
            if not ckpt.exists():
                lines.append("- checkpoint MISSING")
                all_ok = False
                continue
            sd = torch.load(ckpt, map_location="cpu")
            n_keys = len(sd)
            n_params = sum(v.numel() for v in sd.values())
            lines.append(f"- checkpoint: {ckpt}")
            lines.append(f"- sha256: {sha256(ckpt)}")
            lines.append(f"- state_dict keys: {n_keys} (expected {EXPECTED_KEYS})")
            lines.append(f"- total params: {n_params} (expected {EXPECTED_PARAMS})")
            ok_arch = n_keys == EXPECTED_KEYS and n_params == EXPECTED_PARAMS
            lines.append(f"- architecture exact: {ok_arch}")
            all_ok &= ok_arch
            # compare key set with v1.4 Full BC architecture
            fk = full_bc_keys()
            if fk:
                same_keys = set(sd.keys()) == fk
                lines.append(f"- state-dict keys identical to v1.4 Full BC: {same_keys}")
                all_ok &= same_keys
            agent, _ = load_agent(cfg, ckpt)
            for name, ok in check_semantics(agent, cfg["sem"]):
                lines.append(f"- [{('PASS' if ok else 'FAIL')}] {name}")
                all_ok &= ok
            rows.append((abl, seed, n_keys, n_params, sha256(ckpt)))
            lines.append("")
    lines.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    lines[2] = f"generated: see final line; overall PASS={all_ok}"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for abl, seed, k, p, s in rows:
        print(f"{abl:<20} seed{seed} keys={k} params={p} sha={s[:16]}...")
    print(f"report: {args.out}")


if __name__ == "__main__":
    main()
