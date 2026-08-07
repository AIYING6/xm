# run_efficiency_v1_5.py
# Phase-3 formal efficiency profiling (FORMAL_EFFICIENCY_PROTOCOL_V1_5, frozen).
#
# Frozen budgets:
#   4.1  parameters / complexity      : static, from locked state_dicts
#   4.2A architecture-only latency    : warm-up 200, measure 1000, repeats 10,
#                                       batch 1 & 8, SAME fixed inputs replayed
#                                       for every method
#   4.3  end-to-end env throughput    : 8 envs x 128 steps, deterministic, no bp
#   4.4  memory                       : inference peak + training peak
#                                       (8 envs x 128 rollout, exactly 1 PPO update)
#   4.5  communication                : per-method episode message/edge statistics
#
# Deliverables (protocol section 8):
#   results/paper_config_runs/formal_efficiency_v1.5_20260807/
#     _operator_notes/final_efficiency_audit_v1_5/
#       efficiency_audit_report.md
#       efficiency_params.csv
#       efficiency_latency.csv
#       efficiency_throughput.csv
#       efficiency_memory.csv
#       efficiency_communication.csv
#       efficiency_outputs_sha256.txt
#       efficiency_evidence_manifest.json
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AB_ROOT))

from scripts.evaluate_ri_gmappo_3d import build_agent as build_ri_agent  # noqa: E402
from scripts.evaluate_happo_3d import build_agent as build_happo_agent  # noqa: E402
from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    collect_rollout as ri_collect_rollout,
    make_envs,
    make_optimizer,
    set_seed,
    stack_graphs,
    update_policy as ri_update_policy,
)
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    collect_rollout as mappo_collect_rollout,
    strict_bc_load,
    update_policy as mappo_update_policy,
)
from scripts.train_happo_baseline import (  # noqa: E402
    HAPPOBaselineAgent,
    update_happo_policy,
)
from _operator_scripts.efficiency_profiler import (  # noqa: E402
    CommStats,
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


# ------------------------------------------------------------ model builders ----
# (mirrors the phase-2 smoke entrypoints; locked seed-0 checkpoints only)

def make_ri_agent(ckpt: str, graph_encoder: str, relation_abl: str = "none",
                  message_abl: str = "none", gate_prior: float = 0.4,
                  gate_fixed: float = 0.5) -> tuple[torch.nn.Module, object, dict]:
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


def make_env(cfg: RIGMAPPOConfig, seed: int, training: bool):
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env as _me
    return _me(cfg, seed, training)


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
    strict_bc_load(agent, ckpt, torch.device(DEVICE))
    agent.to(DEVICE)
    agent.eval()
    env = make_env(env_cfg, 0, training=False)
    return agent, env, cfg


def make_happo_agent(ckpt: str) -> tuple[HAPPOBaselineAgent, object, dict]:
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


def method_cfg(method: str) -> dict:
    """Per-method graph/ablation switches (mirrors the locked configs)."""
    if method in ("full_ea_rg", "w_o_role_pair_gate", "param_matched_single"):
        enc = "multi_relation" if method in ("full_ea_rg", "w_o_role_pair_gate") else "single"
        rel = "none"
        msg = "none" if method != "w_o_role_pair_gate" else "no_role_pair_gate"
        prior = 0.4 if method != "param_matched_single" else 0.0
        fixed = 0.5 if method != "w_o_role_pair_gate" else 0.598687660112452
    else:
        enc = rel = msg = None
        prior = fixed = None
    return {"enc": enc, "rel": rel, "msg": msg, "prior": prior, "fixed": fixed}


# ------------------------------------------------------------ joint forward ----
# Frozen timing unit: ONE joint team decision = 3 blue agents acting from one env
# state. Protocol 4.2A replays the SAME fixed inputs for every method.

_CACHED_INPUTS: dict | None = None


def build_inputs(env, batch: int) -> dict:
    obs, share_obs, graph = env.reset()
    graphs = [graph] * batch
    g = stack_graphs(graphs)
    inputs = {
        "obs": torch.as_tensor(np.stack([obs] * batch, axis=0), dtype=torch.float32, device=DEVICE),
        "share": torch.as_tensor(np.stack([share_obs] * batch, axis=0), dtype=torch.float32, device=DEVICE),
        "node_feat": torch.as_tensor(g["node_feat"], dtype=torch.float32, device=DEVICE),
        "edge_feat": torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=DEVICE) if "edge_feat" in g else None,
        "role": torch.as_tensor(g["role"], dtype=torch.long, device=DEVICE),
        "adj": torch.as_tensor(g["adj"], dtype=torch.float32, device=DEVICE) if "adj" in g else None,
        "relation_adj": torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=DEVICE) if "relation_adj" in g else None,
        "na": env.num_agents,
    }
    return inputs


def joint_forward_from_inputs(agent, inputs: dict) -> None:
    """One joint team decision from pre-built (fixed) inputs. No env access."""
    obs_t, share_t = inputs["obs"], inputs["share"]
    node_feat, edge_feat = inputs["node_feat"], inputs["edge_feat"]
    role, adj = inputs["role"], inputs["adj"]
    relation_adj = inputs["relation_adj"]
    na = inputs["na"]
    if isinstance(agent, MAPPOAgent3D):
        batch = obs_t.shape[0]
        obs_2d = obs_t.reshape(batch, na, -1)
        role_blue = role[..., :na]
        ro = torch.nn.functional.one_hot(role_blue, num_classes=4).to(dtype=obs_2d.dtype, device=DEVICE)
        joint = torch.cat([obs_2d, ro], dim=-1).reshape(batch * na, -1)
        with torch.no_grad():
            agent.get_action_and_value(joint, share_t, deterministic=True)
    else:  # RIGMAPPOAgent / HAPPOBaselineAgent (3 policies forward internally)
        with torch.no_grad():
            agent.get_action_and_value(obs_t, node_feat, edge_feat, role, adj,
                                       share_t, relation_adj=relation_adj,
                                       deterministic=True)


# ------------------------------------------------------------ communication ----

def count_blue_edges(graph: dict, na: int) -> tuple[int, int]:
    """(candidate edges incl self-loop, physical i!=j edges) over the blue block."""
    adj = np.asarray(graph["adj"])
    if adj.ndim == 3:
        adj = adj[0]
    adj_blue = adj[:na, :na]
    mask = ~np.eye(na, dtype=bool)
    cand = int((adj_blue != 0).sum())
    phys = int((mask & (adj_blue != 0)).sum())
    return cand, phys


def message_queue_len(env) -> int:
    for attr in ("pending_target_messages", "target_msg_queue", "message_queue"):
        if hasattr(env, attr):
            q = getattr(env, attr)
            return len(q) if isinstance(q, (list, dict)) else int(q)
    return 0


def comm_rollout_stats(train_cfg, steps: int, episodes: int, base_seed: int,
                       rng_seed: int) -> dict:
    """Run `episodes` fixed-seed episodes (max `steps` each); aggregate per-step
    candidate/physical edges and in-flight target-message count.

    Protocol 5 (fixed input distribution): ALL methods share the SAME fixed
    pseudo-random action sequence (rng_seed), so the trajectory is identical
    across methods and communication cost is decoupled from policy behavior.
    This is what makes the RPG on/off comparison valid: the Role-Pair Gate is
    multiplicative modulation (verified in source) and must not change the
    physical message count on the same trajectory.
    """
    cand_tot = phys_tot = msgs_tot = n_steps = 0
    done_cnt = 0
    env_cfg = train_cfg.env if isinstance(train_cfg, MAPPO3DConfig) else train_cfg
    rng = np.random.default_rng(rng_seed)
    for ep in range(episodes):
        env = make_env(env_cfg, base_seed + ep, training=False)
        obs, share_obs, graph = env.reset()
        for _ in range(steps):
            act = rng.integers(0, 27, size=(env.num_agents,))
            obs, share_obs, graph, r, d, _ = env.step(act)
            c, p = count_blue_edges(graph, env.num_agents)
            cand_tot += c
            phys_tot += p
            msgs_tot += message_queue_len(env)
            n_steps += 1
            if np.all(d):
                done_cnt += 1
                break
    mean_msgs = msgs_tot / max(n_steps, 1)
    return {
        "trajectory_source": "fixed_action_rng",
        "episodes": episodes,
        "episodes_completed": done_cnt,
        "steps_total": n_steps,
        "mean_candidate_edges_per_step": cand_tot / max(n_steps, 1),
        "mean_physical_comm_edges_per_step": phys_tot / max(n_steps, 1),
        "mean_inflight_messages_per_step": mean_msgs,
        "mean_payload_scalars_per_step": mean_msgs * 7,   # pos3+vel3+confidence
        "mean_payload_scalars_per_step_incl_meta": mean_msgs * 11,  # +4 int metadata
    }


# ------------------------------------------------------------ training memory ----

def profile_training(agent, method: str, out_dir: Path, train_cfg) -> dict:
    """8 envs x 128 rollout + exactly 1 PPO update; peak allocated/reserved memory.
    Uses the SAME locked checkpoint weights; no model saving, no eval."""
    agent.train()
    if isinstance(agent, MAPPOAgent3D):
        cfg = train_cfg  # MAPPO3DConfig
        envs = make_envs(cfg.env)
        obs_list, share_list, role_list = [], [], []
        for env in envs:
            obs, share_obs, graph = env.reset()
            obs_list.append(obs)
            share_list.append(share_obs)
            role_list.append(np.asarray(graph["role"], dtype=np.int64)[: env.num_agents])
        obs = np.stack(obs_list)
        share_obs = np.stack(share_list)
        role = np.stack(role_list)
        actor_opt = optim.Adam(agent.actor.parameters(), lr=cfg.actor_lr, eps=1e-5)
        critic_opt = optim.Adam(agent.critic.parameters(), lr=cfg.critic_lr, eps=1e-5)
        reset_memory(DEVICE)
        t0 = time.perf_counter()
        batch = mappo_collect_rollout(agent, envs, obs, share_obs, role, cfg, DEVICE)
        info = mappo_update_policy(agent, actor_opt, critic_opt, batch, cfg, DEVICE)
        if DEVICE == "cuda":
            torch.cuda.synchronize()
        wall_ms = (time.perf_counter() - t0) * 1000.0
        mem = snapshot_memory(DEVICE)
    else:
        cfg = train_cfg  # RIGMAPPOConfig
        envs = make_envs(cfg)
        obs_list, share_list, graph_list = [], [], []
        for env in envs:
            obs, share_obs, graph = env.reset()
            obs_list.append(obs)
            share_list.append(share_obs)
            graph_list.append(graph)
        obs = np.stack(obs_list)
        share_obs = np.stack(share_list)
        graph_obs = stack_graphs(graph_list)
        if isinstance(agent, HAPPOBaselineAgent):
            optimizers = [optim.Adam(p.parameters(), lr=cfg.lr, eps=1e-5) for p in agent.policies]
            reset_memory(DEVICE)
            t0 = time.perf_counter()
            batch = ri_collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, DEVICE)
            info = update_happo_policy(agent, optimizers, batch, cfg, DEVICE)
            if DEVICE == "cuda":
                torch.cuda.synchronize()
            wall_ms = (time.perf_counter() - t0) * 1000.0
            mem = snapshot_memory(DEVICE)
        else:  # RIGMAPPOAgent
            optimizer = make_optimizer(agent, cfg)
            reset_memory(DEVICE)
            t0 = time.perf_counter()
            batch = ri_collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, DEVICE)
            info = ri_update_policy(agent, optimizer, batch, cfg, DEVICE, 1)
            if DEVICE == "cuda":
                torch.cuda.synchronize()
            wall_ms = (time.perf_counter() - t0) * 1000.0
            mem = snapshot_memory(DEVICE)
    rollout_steps = cfg.env.rollout_steps if isinstance(agent, MAPPOAgent3D) else cfg.rollout_steps
    num_envs = cfg.env.num_envs if isinstance(agent, MAPPOAgent3D) else cfg.num_envs
    samples = rollout_steps * num_envs * 3
    return {
        "method": method,
        "peak_allocated_mb": mem.peak_allocated_mb,
        "peak_reserved_mb": mem.peak_reserved_mb,
        "wall_ms": wall_ms,
        "samples": samples,
        "samples_per_s": samples / (wall_ms / 1000.0),
        "update_loss": info.get("loss", float("nan")),
    }


def make_train_cfg(method: str, out_dir: Path):
    m = method_cfg(method)
    env_cfg = RIGMAPPOConfig(
        seed=0, env_name="3d_intercept", num_envs=8, rollout_steps=128,
        updates=1, hidden_dim=HIDDEN, strict_target_sensing=True,
        agent_target_info_bottleneck=True, communication_dropout_prob=0.30,
        message_delay_steps=2, failed_blue_agent=1,
        node_failure_start_random_min=25, node_failure_start_random_max=70,
        node_failure_duration_steps=80, attack_hold_steps=4, min_success_step=80,
        role_gate_prior_strength=m["prior"] if m["prior"] is not None else 0.4,
        role_pair_gate_fixed_value=m["fixed"] if m["fixed"] is not None else 0.5,
        device=DEVICE,
    )
    if method == "mappo":
        return MAPPO3DConfig(env=env_cfg, device=DEVICE, out_dir=str(out_dir),
                             eval_interval=10**9, save_interval=10**9,
                             save_snapshots=False)
    return env_cfg


# ------------------------------------------------------------------- main ----

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "results/paper_config_runs/formal_efficiency_v1.5_20260807/_operator_notes/final_efficiency_audit_v1_5")
    parser.add_argument("--warmup", type=int, default=200)
    parser.add_argument("--measure", type=int, default=1000)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--batch-sizes", type=str, default="1,8")
    parser.add_argument("--e2e-envs", type=int, default=8)
    parser.add_argument("--e2e-steps", type=int, default=128)
    parser.add_argument("--comm-episodes", type=int, default=3)
    parser.add_argument("--comm-steps", type=int, default=200)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]

    snap = hardware_snapshot()
    import subprocess
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=driver_version,memory.total", "--format=csv,noheader"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split(",")
            snap["gpu_driver"] = parts[0].strip()
            snap["gpu_memory_total"] = parts[1].strip() if len(parts) > 1 else None
    except Exception:
        pass

    problems: list[str] = []
    params_rows: list[dict] = []
    latency_rows: list[dict] = []
    throughput_rows: list[dict] = []
    memory_rows: list[dict] = []
    comm_rows: list[dict] = []
    raw_latencies: dict[str, dict] = {}   # method -> {batch -> [ms,...]} retained

    for method in METHODS:
        ckpt = CKS[method]
        if not Path(ckpt).exists():
            problems.append(f"{method}: checkpoint missing {ckpt}")
            continue
        m = method_cfg(method)
        if method in ("full_ea_rg", "w_o_role_pair_gate", "param_matched_single"):
            agent, env, _ = make_ri_agent(ckpt, m["enc"], m["rel"], m["msg"], m["prior"], m["fixed"])
        elif method == "mappo":
            agent, env, _ = make_mappo_agent(ckpt)
        else:
            agent, env, _ = make_happo_agent(ckpt)
        agent.eval()
        sd = agent.state_dict()
        params_rows.append({
            "method": method,
            "checkpoint_sha256": sha256(Path(ckpt)),
            "checkpoint_kb": round(Path(ckpt).stat().st_size / 1024.0, 1),
            "tensors": len(sd),
            "params": sum(v.numel() for v in sd.values()),
        })

        # ---- 4.2A architecture-only latency: SAME fixed inputs per batch ----
        for batch in batch_sizes:
            inputs = build_inputs(env, batch)  # identical for every method
            for _ in range(args.warmup):
                joint_forward_from_inputs(agent, inputs)
            lat: list[float] = []
            for _ in range(args.repeats):
                lat += time_joint_forward(
                    lambda: joint_forward_from_inputs(agent, inputs),
                    args.measure, DEVICE,
                )
            a = np.array(lat, dtype=float)
            latency_rows.append({
                "method": method, "batch": batch,
                "joint_actions": batch * 3, "n": int(a.size),
                "mean_ms": float(a.mean()), "median_ms": float(np.median(a)),
                "p95_ms": float(np.percentile(a, 95)), "p99_ms": float(np.percentile(a, 99)),
                "sd_ms": float(a.std(ddof=1)) if a.size > 1 else 0.0,
                "joint_decisions_per_s": 1000.0 / float(a.mean()),
            })
            raw_latencies.setdefault(method, {})[batch] = lat
            # inference peak memory (reset before a single pass)
            reset_memory(DEVICE)
            joint_forward_from_inputs(agent, inputs)
            mem = snapshot_memory(DEVICE)
            memory_rows.append({
                "kind": "inference", "method": method, "batch": batch,
                "peak_allocated_mb": mem.peak_allocated_mb,
                "peak_reserved_mb": mem.peak_reserved_mb,
            })

        # ---- 4.3 end-to-end env throughput (8 envs x 128, deterministic) ----
        train_cfg = make_train_cfg(method, out_dir)
        if isinstance(agent, MAPPOAgent3D):
            envs = make_envs(train_cfg.env)
            o_list, s_list, r_list = [], [], []
            for e in envs:
                o, s, g = e.reset()
                o_list.append(o); s_list.append(s)
                r_list.append(np.asarray(g["role"], dtype=np.int64)[: e.num_agents])
            obs = np.stack(o_list); share_obs = np.stack(s_list); role = np.stack(r_list)
            reset_memory(DEVICE)
            t0 = time.perf_counter()
            mappo_collect_rollout(agent, envs, obs, share_obs, role, train_cfg, DEVICE)
            if DEVICE == "cuda":
                torch.cuda.synchronize()
            wall_ms = (time.perf_counter() - t0) * 1000.0
        else:
            envs = make_envs(train_cfg)
            o_list, s_list, g_list = [], [], []
            for e in envs:
                o, s, g = e.reset()
                o_list.append(o); s_list.append(s); g_list.append(g)
            obs = np.stack(o_list); share_obs = np.stack(s_list); graph_obs = stack_graphs(g_list)
            reset_memory(DEVICE)
            t0 = time.perf_counter()
            ri_collect_rollout(agent, envs, obs, share_obs, graph_obs, train_cfg, DEVICE)
            if DEVICE == "cuda":
                torch.cuda.synchronize()
            wall_ms = (time.perf_counter() - t0) * 1000.0
        env_steps = args.e2e_envs * args.e2e_steps
        throughput_rows.append({
            "method": method,
            "envs": args.e2e_envs, "rollout_steps": args.e2e_steps,
            "env_steps": env_steps,
            "wall_ms": wall_ms,
            "env_steps_per_s": env_steps / (wall_ms / 1000.0),
            "decision_steps_per_s": env_steps / (wall_ms / 1000.0),
            "wall_per_10k_env_steps_ms": wall_ms * 10000.0 / env_steps,
        })
        # ---- 4.4 training peak memory (8env x 128, 1 PPO update) ----
        try:
            mem_row = profile_training(agent, method, out_dir, train_cfg)
            memory_rows.append({
                "kind": "training", **mem_row,
            })
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{method}: training-memory profiling failed: {exc!r}")
        agent.eval()

        # ---- 4.5 communication (fixed matched episodes, shared trajectory) ----
        cs = comm_rollout_stats(train_cfg, args.comm_steps,
                                args.comm_episodes, base_seed=1000,
                                rng_seed=20260807)
        comm_rows.append({
            "method": method,
            "rpg_applies": "yes" if method in ("full_ea_rg", "w_o_role_pair_gate") else "no",
            **cs,
            "edge_feature_dim": 17,
            "continuous_payload_dim": 7,
            "metadata_fields": 4,
        })

    # RPG on/off message-count invariance (protocol 4.5)
    on = next((r for r in comm_rows if r["method"] == "full_ea_rg"), None)
    off = next((r for r in comm_rows if r["method"] == "w_o_role_pair_gate"), None)
    if on and off:
        for k in ("mean_physical_comm_edges_per_step", "mean_inflight_messages_per_step"):
            if abs(float(on[k]) - float(off[k])) > 1e-9:
                problems.append(f"RPG on/off {k} differ (counting bug?)")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ---- write deliverables ----
    def write_csv(name: str, rows: list[dict]) -> Path:
        p = out_dir / name
        fieldnames = list(dict.fromkeys(k for r in rows for k in r.keys()))
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        return p

    p_params = write_csv("efficiency_params.csv", params_rows)
    p_lat = write_csv("efficiency_latency.csv", latency_rows)
    p_thr = write_csv("efficiency_throughput.csv", throughput_rows)
    p_mem = write_csv("efficiency_memory.csv", memory_rows)
    p_comm = write_csv("efficiency_communication.csv", comm_rows)

    all_ok = (len(params_rows) == 5 and len(latency_rows) == 5 * len(batch_sizes)
              and len(throughput_rows) == 5 and len(memory_rows) >= 10
              and len(comm_rows) == 5 and not problems)
    manifest = {
        "generated": now,
        "protocol": "FORMAL_EFFICIENCY_PROTOCOL_V1_5 (formal, phase 3)",
        "budget": {"warmup": args.warmup, "measure": args.measure,
                   "repeats": args.repeats, "batch_sizes": batch_sizes,
                   "e2e": {"envs": args.e2e_envs, "steps": args.e2e_steps},
                   "comm": {"episodes": args.comm_episodes, "steps": args.comm_steps}},
        "hardware": snap,
        "methods": METHODS,
        "overall": "PASS" if all_ok else "FAIL",
        "problems": problems,
        "raw_latency_sample_sha256": {
            m: {str(b): hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()[:16]
                for b, v in raw.items()} for m, raw in raw_latencies.items()
        },
    }
    p_manifest = out_dir / "efficiency_evidence_manifest.json"
    p_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Efficiency Phase-3 Formal Audit",
        "",
        f"- generated: {now}",
        f"- hardware: {snap.get('gpu_name')} / driver {snap.get('gpu_driver')} / "
        f"CUDA {snap.get('cuda_version')} / torch {snap.get('pytorch_version')} / FP32 eager",
        f"- methods: {len(params_rows)}/5",
        f"- OVERALL: {'PASS' if all_ok else 'FAIL'}",
        "",
        "## 4.1 Parameters",
        "",
    ]
    for r in params_rows:
        md.append(f"- {r['method']}: {r['params']:,} params, {r['tensors']} tensors, "
                  f"{r['checkpoint_kb']} KB, sha {r['checkpoint_sha256'][:12]}...")
    md.append("")
    md.append("## 4.2A Architecture-only latency (ms, warmup={} measure={} repeats={})".format(
        args.warmup, args.measure, args.repeats))
    md.append("")
    for r in latency_rows:
        md.append(f"- {r['method']} batch{r['batch']}: mean {r['mean_ms']:.3f} "
                  f"(median {r['median_ms']:.3f}, P95 {r['p95_ms']:.3f}, P99 {r['p99_ms']:.3f}) "
                  f"=> {r['joint_decisions_per_s']:.0f} joint-decisions/s")
    md.append("")
    md.append("## 4.3 End-to-end throughput (8 envs x 128)")
    md.append("")
    for r in throughput_rows:
        md.append(f"- {r['method']}: {r['env_steps_per_s']:.0f} env-steps/s, "
                  f"{r['wall_per_10k_env_steps_ms']:.0f} ms / 10k env-steps")
    md.append("")
    md.append("## 4.4 Memory (peak MB)")
    md.append("")
    for r in memory_rows:
        md.append(f"- {r['kind']} {r['method']} batch{r.get('batch', '')}: "
                  f"allocated {r['peak_allocated_mb']:.1f} / reserved {r['peak_reserved_mb']:.1f}")
    md.append("")
    md.append("## 4.5 Communication (shared fixed-action trajectory)")
    md.append("")
    md.append("Fixed pseudo-random action sequence shared by ALL methods; "
              "communication cost is therefore decoupled from policy behavior "
              "and the RPG on/off comparison is exact (protocol 4.5/5).")
    md.append("")
    for r in comm_rows:
        md.append(f"- {r['method']}: candidate {r['mean_candidate_edges_per_step']:.2f}/step, "
                  f"physical {r['mean_physical_comm_edges_per_step']:.2f}/step, "
                  f"in-flight msgs {r['mean_inflight_messages_per_step']:.2f}/step")
    md.append("")
    if problems:
        md.append("## PROBLEMS")
        for p in problems:
            md.append(f"- {p}")
        md.append("")
    md.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    p_report = out_dir / "efficiency_audit_report.md"
    p_report.write_text("\n".join(md), encoding="utf-8")

    # output sha256 ledger
    lines = []
    for p in sorted(out_dir.glob("efficiency_*")):
        lines.append(f"{sha256(p)}  {p.name}")
    p_sha = out_dir / "efficiency_outputs_sha256.txt"
    p_sha.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    print(f"output dir: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
