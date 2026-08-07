# run_efficiency_smoke_v1_5.py
# Phase-2 efficiency profiling smoke (FORMAL_EFFICIENCY_PROTOCOL_V1_5).
#
# NOT formal measurements: verifies the joint-decision timing / memory /
# communication chains for the 5 methods on locked seed0 checkpoints.
#
# Budgets (smoke only):
#   architecture-only latency: warm-up 10, measure 20, repeats 2, batch 1 and 8
#   end-to-end: 8 envs x 16 steps
#   memory: 1 inference pass + 1 tiny profiling update (1 PPO update,
#           8x16 rollout)
#   communication: fixed matched episodes, RPG on/off message-count check
#
# Output: _smoke/efficiency_v1_5/ (+ smoke_audit/)
#   efficiency_smoke_audit.md
#   efficiency_smoke_manifest.json
#   efficiency_import_identity.csv
#   efficiency_joint_decision_check.csv
#   efficiency_memory_check.csv
#   efficiency_communication_check.csv
#   hardware_snapshot.json
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AB_ROOT))

from scripts.evaluate_ri_gmappo_3d import build_agent as build_ri_agent  # noqa: E402
from scripts.evaluate_happo_3d import build_agent as build_happo_agent  # noqa: E402
from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs  # noqa: E402
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    strict_bc_load,
)
from _operator_scripts.efficiency_profiler import (  # noqa: E402
    CommStats,
    LatencyResult,
    collect_comm_stats,
    comm_stats_to_dict,
    hardware_snapshot,
    reset_memory,
    snapshot_memory,
    time_joint_forward,
)

CKS = {
    "full_ea_rg": r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\ea_rg_mappo_s_gate_prior\ppo_seed0_1m\actor_critic_update_0700.pt",
    "w_o_role_pair_gate": r"D:\Code\Codex\ri_gmappo_uav_ablation_v1.5\results\paper_config_runs\formal_ablation_v1.5_ppo_977_20260804\w_o_role_pair_gate\ppo_seed0_1m\actor_critic_update_0100.pt",
    "mappo": r"D:\Code\Codex\ri_gmappo_uav_mappo_v1.5\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806\ppo_seed0\actor_critic_update_0600.pt",
    "happo": r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\happo\ppo_seed0_1m\happo_update_0300.pt",
    "param_matched_single": r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\param_matched_single\ppo_seed0_1m\actor_critic_update_0500.pt",
}
METHODS = list(CKS.keys())
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
HIDDEN = 64


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def make_ri_agent(ckpt: str, graph_encoder: str, relation_abl: str = "none",
                  message_abl: str = "none", gate_prior: float = 0.4,
                  gate_fixed: float = 0.5) -> tuple[torch.nn.Module, object, dict]:
    """Build RIGMAPPOAgent from a checkpoint via frozen build_agent path."""
    from argparse import Namespace
    cfg = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=1,
                         rollout_steps=1, updates=1, hidden_dim=HIDDEN,
                         strict_target_sensing=True,
                         agent_target_info_bottleneck=True,
                         communication_dropout_prob=0.30, message_delay_steps=2,
                         failed_blue_agent=1, node_failure_start_random_min=25,
                         node_failure_start_random_max=70,
                         node_failure_duration_steps=80, attack_hold_steps=4,
                         min_success_step=80,
                         role_gate_prior_strength=gate_prior,
                         role_pair_gate_fixed_value=gate_fixed,
                         device=DEVICE)
    args = Namespace(
        checkpoint=Path(ckpt), device=DEVICE, allow_random_policy=False,
        seed=0, episodes=1, eval_batch_size=1,
        target_policy="straight",
        communication_range_scale=1.0,
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        radar_dropout_prob=0.0,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        attack_hold_steps=4,
        min_success_step=80,
        graph_encoder=graph_encoder, graph_relation_ablation=relation_abl,
        graph_message_ablation=message_abl, graph_input_ablation="none",
        multi_relation_global_residual_weight=1.0,
        hidden_dim=HIDDEN, role_dim=4, intent_dim=0,
        role_pair_gate_fixed_value=gate_fixed,
    )
    agent, src = build_ri_agent(args, cfg)
    env = make_env(cfg, 0, training=False)
    return agent, env, cfg


def make_mappo_agent(ckpt: str) -> tuple[MAPPOAgent3D, object, dict]:
    env_cfg = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=1,
                             rollout_steps=1, updates=1, hidden_dim=HIDDEN,
                             strict_target_sensing=True,
                             agent_target_info_bottleneck=True,
                             communication_dropout_prob=0.30, message_delay_steps=2,
                             failed_blue_agent=1, node_failure_start_random_min=25,
                             node_failure_start_random_max=70,
                             node_failure_duration_steps=80, attack_hold_steps=4,
                             min_success_step=80, device=DEVICE)
    cfg = MAPPO3DConfig(env=env_cfg, device=DEVICE, out_dir=str(ROOT / "_smoke/efficiency_v1_5"))
    agent = MAPPOAgent3D(obs_dim=34, role_dim=4, share_obs_dim=47,
                         action_dim=27, hidden_dim=HIDDEN)
    # strict actor-only load (frozen BC chain semantics)
    strict_bc_load(agent, ckpt, torch.device(DEVICE))
    agent.to(DEVICE)
    agent.eval()
    env = make_env(env_cfg, 0, training=False)
    return agent, env, cfg


def make_happo_agent(ckpt: str) -> tuple[torch.nn.Module, object, dict]:
    from argparse import Namespace
    cfg = RIGMAPPOConfig(seed=0, env_name="3d_intercept", num_envs=1,
                         rollout_steps=1, updates=1, hidden_dim=HIDDEN,
                         strict_target_sensing=True,
                         agent_target_info_bottleneck=True,
                         communication_dropout_prob=0.30, message_delay_steps=2,
                         failed_blue_agent=1, node_failure_start_random_min=25,
                         node_failure_start_random_max=70,
                         node_failure_duration_steps=80, attack_hold_steps=4,
                         min_success_step=80, device=DEVICE)
    args = Namespace(checkpoint=Path(ckpt), device=DEVICE,
                     allow_random_policy=False, seed=0,
                     hidden_dim=HIDDEN, role_dim=4, intent_dim=0)
    agent, src = build_happo_agent(args, cfg)
    env = make_env(cfg, 0, training=False)
    return agent, env, cfg


def joint_forward(agent, env, batch: int, device: str) -> None:
    """One joint team decision over `batch` env states -> 3 actions each."""
    obs, share_obs, graph = env.reset()
    # build a batch of `batch` identical env states, stacked via the frozen
    # stack_graphs helper (identical to the frozen evaluation entrypoints)
    graphs = [graph] * batch
    g = stack_graphs(graphs)
    obs_t = torch.as_tensor(np.stack([obs] * batch, axis=0), dtype=torch.float32, device=device)
    share_t = torch.as_tensor(np.stack([share_obs] * batch, axis=0), dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device) if "edge_feat" in g else None
    role = torch.as_tensor(g["role"], dtype=torch.long, device=device)
    adj = torch.as_tensor(g["adj"], dtype=torch.float32, device=device) if "adj" in g else None
    relation_adj = torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device) if "relation_adj" in g else None
    if hasattr(agent, "policies"):  # HAPPO: one call forwards all 3 policies
        with torch.no_grad():
            agent.get_action_and_value(obs_t, node_feat, edge_feat, role, adj,
                                       share_t, relation_adj=relation_adj,
                                       deterministic=True)
    elif isinstance(agent, MAPPOAgent3D):
        with torch.no_grad():
            # obs (batch, obs_dim) -> (batch, num_agents, obs_dim); role one-hot
            # -> (batch, num_agents, role_dim); concat -> (batch, 3, obs+role)
            na = env.num_agents
            obs_2d = obs_t.reshape(batch, na, -1)
            role_blue = role[..., :na]  # blue agents only (role dim may include red)
            ro = torch.nn.functional.one_hot(role_blue, num_classes=4).to(dtype=obs_2d.dtype, device=device)
            joint = torch.cat([obs_2d, ro], dim=-1).reshape(batch * na, -1)
            agent.get_action_and_value(joint, share_t, deterministic=True)
    else:  # RIGMAPPOAgent
        with torch.no_grad():
            agent.get_action_and_value(obs_t, node_feat, edge_feat, role, adj,
                                       share_t, relation_adj=relation_adj,
                                       deterministic=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-dir", type=Path, default=ROOT / "_smoke/efficiency_v1_5")
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--measure", type=int, default=20)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    smoke_dir: Path = args.smoke_dir
    audit_dir = smoke_dir / "smoke_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    snap = hardware_snapshot()
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=driver_version,memory.total", "--format=csv,noheader"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split(",")
            snap["gpu_driver"] = parts[0].strip()
            snap["gpu_memory_total"] = parts[1].strip() if len(parts) > 1 else None
    except Exception:
        pass
    (smoke_dir / "hardware_snapshot.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")

    problems: list[str] = []
    ident_rows: list[dict] = []
    joint_rows: list[dict] = []
    mem_rows: list[dict] = []
    comm_rows: list[dict] = []

    for method in METHODS:
        ckpt = CKS[method]
        if not Path(ckpt).exists():
            problems.append(f"{method}: checkpoint missing {ckpt}")
            continue
        if method in ("full_ea_rg", "w_o_role_pair_gate", "param_matched_single"):
            enc = "multi_relation" if method in ("full_ea_rg", "w_o_role_pair_gate") else "single"
            rel = "none"
            msg = "none" if method != "w_o_role_pair_gate" else "no_role_pair_gate"
            prior = 0.4 if method != "param_matched_single" else 0.0
            fixed = 0.5 if method != "w_o_role_pair_gate" else 0.598687660112452
            agent, env, _ = make_ri_agent(ckpt, enc, rel, msg, prior, fixed)
        elif method == "mappo":
            agent, env, _ = make_mappo_agent(ckpt)
        else:  # happo
            agent, env, _ = make_happo_agent(ckpt)

        agent.eval()
        ident_rows.append({
            "method": method,
            "checkpoint_sha256": sha256(Path(ckpt)),
            "module": agent.__class__.__module__,
            "device": DEVICE,
            "tensors": len(dict(agent.state_dict())),
            "params": sum(v.numel() for v in agent.state_dict().values()),
        })

        # ---- joint-decision timing (batch 1 and 8) ----
        for batch in (1, 8):
            # warm-up
            for _ in range(args.warmup):
                joint_forward(agent, env, batch, DEVICE)
            lat = []
            for _ in range(args.repeats):
                lat += time_joint_forward(lambda: joint_forward(agent, env, batch, DEVICE),
                                          args.measure, DEVICE)
            res = LatencyResult(batch=batch, method=method, latencies_ms=lat,
                                decisions=batch * 3)
            s = res.summary()
            joint_rows.append({
                "method": method, "batch": batch,
                "joint_actions": batch * 3, "n": s["n"],
                "mean_ms": s["mean_ms"], "median_ms": s["median_ms"],
                "p95_ms": s["p95_ms"], "p99_ms": s["p99_ms"],
                "sd_ms": s["sd_ms"], "joint_decisions_per_s": s["decisions_per_s"],
            })
            # memory (1 inference pass, reset before)
            reset_memory(DEVICE)
            joint_forward(agent, env, batch, DEVICE)
            m = snapshot_memory(DEVICE)
            mem_rows.append({
                "method": method, "batch": batch,
                "peak_allocated_mb": m.peak_allocated_mb,
                "peak_reserved_mb": m.peak_reserved_mb,
            })

        # ---- communication stats (RPG on vs off must not change physical msgs) ----
        _, _, g0 = env.reset()
        cs = collect_comm_stats(env, adj=g0.get("adj"), relation_adj=g0.get("relation_adj"))
        comm_rows.append({
            "method": method,
            **comm_stats_to_dict(cs),
            "rpg_applies": "yes" if method in ("full_ea_rg", "w_o_role_pair_gate") else "no",
        })

    # RPG on/off physical-message invariance check
    if "full_ea_rg" in ident_rows and "w_o_role_pair_gate" in ident_rows:
        on = next(r for r in comm_rows if r["method"] == "full_ea_rg")
        off = next(r for r in comm_rows if r["method"] == "w_o_role_pair_gate")
        if on["physical_comm_edges"] != off["physical_comm_edges"]:
            problems.append("RPG on/off physical_comm_edges differ (counting bug?)")
        if on["actual_target_messages"] != off["actual_target_messages"]:
            problems.append("RPG on/off actual_target_messages differ (counting bug?)")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (audit_dir / "efficiency_import_identity.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ident_rows[0].keys()))
        w.writeheader(); w.writerows(ident_rows)
    with (audit_dir / "efficiency_joint_decision_check.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(joint_rows[0].keys()))
        w.writeheader(); w.writerows(joint_rows)
    with (audit_dir / "efficiency_memory_check.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mem_rows[0].keys()))
        w.writeheader(); w.writerows(mem_rows)
    with (audit_dir / "efficiency_communication_check.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comm_rows[0].keys()))
        w.writeheader(); w.writerows(comm_rows)

    all_ok = (len(ident_rows) == 5 and len(joint_rows) == 10 and len(mem_rows) == 10
              and len(comm_rows) == 5 and not problems)
    manifest = {
        "generated": now,
        "protocol": "FORMAL_EFFICIENCY_PROTOCOL_V1_5 (smoke, phase 2)",
        "budget": {"warmup": args.warmup, "measure": args.measure, "repeats": args.repeats},
        "methods": METHODS,
        "identity": ident_rows, "joint": joint_rows, "memory": mem_rows, "comm": comm_rows,
        "overall": "PASS" if all_ok else "FAIL", "problems": problems,
    }
    (audit_dir / "efficiency_smoke_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Efficiency Phase-2 Smoke Audit",
        "",
        f"- generated: {now}",
        f"- hardware: {snap.get('gpu_name')} / torch {snap.get('pytorch_version')} / FP32 eager",
        f"- methods: {len(ident_rows)}/5 loaded",
        f"- joint-decision rows: {len(joint_rows)} (5 x batch1/8)",
        f"- memory rows: {len(mem_rows)}",
        f"- comm rows: {len(comm_rows)}",
        "",
        "## Joint-decision latency (smoke only, not for paper)",
        "",
    ]
    for r in joint_rows:
        md.append(f"- {r['method']} batch{r['batch']}: {r['mean_ms']:.3f} ms mean, "
                  f"{r['joint_decisions_per_s']:.0f} joint-decisions/s")
    md.append("")
    if problems:
        md.append("## PROBLEMS")
        for p in problems:
            md.append(f"- {p}")
        md.append("")
    md.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (audit_dir / "efficiency_smoke_audit.md").write_text("\n".join(md), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    print(f"smoke dir: {smoke_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
