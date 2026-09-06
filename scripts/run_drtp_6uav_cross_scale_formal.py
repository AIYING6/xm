"""Isolated formal 6-UAV UTR versus Original-DRTP runner.

The historical P2/P3 artifacts stay untouched.  This runner uses the corrected
role-separated learner and records the *full accumulated episode return* before
passing it to the reset-side DRTP sampler.  It never uses a development tape
during training, promotes no checkpoint, and evaluates only the fixed 10M end
point.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_drtp_sampler import ALL_GROUPS, SixUAVDRTPSelection, SixUAVDRTPTopologySampler
from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from algorithms.redundant_topology_sg_mappo import SGMPPOConfig, checkpoint_payload, set_seed
from scripts.run_redundant_topology_uav_p2 import (
    EVAL_EPISODES, fault_spec, graph_stack, make_env, maybe_fault, reset_many,
    tensors, update,
)

PROTOCOL = "DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-V1"
FREEZE = ROOT / "configs/drtp_6uav_cross_scale_formal_freeze_20260906.json"
ARMS = {
    "utr_scout_terminal_assigned_role_sg_mappo": "utr",
    "drtp_scout_terminal_assigned_role_sg_mappo": "drtp",
}
SEEDS = (69011, 69012, 69013, 69014, 69015)
UPDATES, NUM_ENVS, ROLLOUT = 39063, 4, 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT
MILESTONES = {3907: "1m", 11719: "3m", 39063: "10m"}
EVALUATION_EPISODES = 100


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_spec() -> dict:
    spec = json.loads(FREEZE.read_text(encoding="utf-8"))
    training = spec["training"]
    if tuple(training["seeds"]) != SEEDS or training["environment_steps_per_trajectory"] != STEPS:
        raise RuntimeError("six-UAV formal freeze does not match this runner")
    return spec


def build_agent(env, cfg: SGMPPOConfig, device: torch.device) -> RoleSharedSGMPPO:
    return RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim, cfg.hidden_dim, cfg.role_dim).to(device)


def _new_group(sampler: SixUAVDRTPTopologySampler, update: int, env_index: int, episode_index: int) -> str:
    return sampler.select(update, env_index, episode_index).group


def collect_full_return(agent, envs, share, graph, cfg, device, sampler, update_index, episode_indices, returns):
    """Collect one PPO rollout and return complete, not terminal-step, rewards."""
    from algorithms.redundant_topology_sg_mappo import gae

    buf = {key: [] for key in ("obs", "roles", "adj", "masks", "share", "actions", "logp", "values", "rewards", "dones")}
    completed = []
    for _ in range(cfg.rollout_steps):
        with torch.no_grad():
            actions, logp, _, values = agent.action_value(*tensors(graph, share, device))
        next_share, next_graphs, rewards, dones = [], [], [], []
        for index, env in enumerate(envs):
            maybe_fault(env)
            _, share_i, graph_i, reward, done, info = env.step(actions[index].cpu().numpy())
            returns[index] += float(reward[0, 0])
            if bool(done.all()):
                completed.append({"group": env._p2_group, "return": float(returns[index]), "success": int(info["success"])})
                # Preserve the group actually used during the just-completed
                # episode; do not resample after the trajectory has occurred.
                sampler.record_completed_return(SixUAVDRTPSelection(env._p2_group), returns[index])
                episode_indices[index] += 1
                returns[index] = 0.0
                env._p2_group = _new_group(sampler, update_index, index, episode_indices[index])
                _, share_i, graph_i = env.reset()
            next_share.append(share_i); next_graphs.append(graph_i)
            rewards.append(reward[:, 0]); dones.append(done[:, 0])
        for key in ("obs", "roles", "adj", "masks"):
            buf[key].append(graph[key].copy())
        buf["share"].append(share.copy()); buf["actions"].append(actions.cpu().numpy())
        buf["logp"].append(logp.cpu().numpy()); buf["values"].append(values.cpu().numpy())
        buf["rewards"].append(np.asarray(rewards)); buf["dones"].append(np.asarray(dones))
        share, graph = np.stack(next_share), graph_stack(next_graphs)
    with torch.no_grad():
        bootstrap = agent.critic(torch.as_tensor(share, dtype=torch.float32, device=device)).squeeze(-1).unsqueeze(-1).expand(-1, envs[0].n).cpu().numpy()
    for key in buf:
        buf[key] = np.asarray(buf[key])
    buf["advantages"], buf["returns"] = gae(buf["rewards"], buf["dones"], buf["values"], bootstrap, cfg.gamma, cfg.gae_lambda)
    return buf, share, graph, completed, episode_indices, returns


def payload(agent, optimizer, envs, update_index, seed, sampler, episode_indices, returns):
    state = checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], update_index, seed)
    state.update({"protocol": PROTOCOL, "sampler": sampler.state_dict(), "episode_indices": list(episode_indices), "episode_returns": list(returns)})
    return state


def train(out: Path, arm: str, seed: int, device: torch.device) -> None:
    frozen_spec()
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("arm or seed is outside the frozen six-UAV contract")
    run = out / "runs" / arm / f"seed{seed}"
    if run.exists():
        raise FileExistsError(f"refusing to overwrite {run}")
    set_seed(seed); run.mkdir(parents=True)
    cfg = SGMPPOConfig(num_envs=NUM_ENVS, rollout_steps=ROLLOUT, updates=UPDATES)
    sampler = SixUAVDRTPTopologySampler(ARMS[arm], seed, UPDATES)
    episode_indices = [0] * NUM_ENVS
    envs = [make_env(seed * 1000 + index, _new_group(sampler, 0, index, 0)) for index in range(NUM_ENVS)]
    share, graph = reset_many(envs)
    agent = build_agent(envs[0], cfg, device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    returns = [0.0] * NUM_ENVS
    torch.save(payload(agent, optimizer, envs, 0, seed, sampler, episode_indices, returns), run / "actor_critic_runtime_state_0.pt")
    fields = ("update", "env_steps", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm", "completed_episodes", "mean_completed_return", "sampler_adapted")
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as handle, (run / "drtp_topology_sampler_log.csv").open("w", newline="", encoding="utf-8") as sampler_log:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        sampler_writer = None
        for update_index in range(1, UPDATES + 1):
            batch, share, graph, completed, episode_indices, returns = collect_full_return(agent, envs, share, graph, cfg, device, sampler, update_index, episode_indices, returns)
            health = update(agent, optimizer, batch, cfg, device)
            if not all(math.isfinite(value) for value in health.values()):
                raise RuntimeError("non-finite PPO scalar")
            sampler_row = sampler.maybe_update(update_index)
            if sampler_row is not None:
                if sampler_writer is None:
                    sampler_writer = csv.DictWriter(sampler_log, fieldnames=list(sampler_row)); sampler_writer.writeheader()
                sampler_writer.writerow(sampler_row); sampler_log.flush()
            writer.writerow({"update": update_index, "env_steps": update_index * NUM_ENVS * ROLLOUT, **health, "completed_episodes": len(completed), "mean_completed_return": float(np.mean([row["return"] for row in completed])) if completed else "", "sampler_adapted": bool(sampler_row and sampler_row["adapted"])})
            handle.flush()
            if update_index in MILESTONES:
                runtime = payload(agent, optimizer, envs, update_index, seed, sampler, episode_indices, returns)
                torch.save(runtime, run / f"actor_critic_runtime_state_milestone_{MILESTONES[update_index]}.pt")
                torch.save({"model": agent.state_dict(), "update": update_index, "seed": seed, "protocol": PROTOCOL}, run / f"actor_critic_milestone_{MILESTONES[update_index]}.pt")
    torch.save(payload(agent, optimizer, envs, UPDATES, seed, sampler, episode_indices, returns), run / "actor_critic_runtime_state_latest.pt")
    torch.save({"model": agent.state_dict(), "update": UPDATES, "seed": seed, "protocol": PROTOCOL}, run / "actor_critic_latest.pt")
    (run / "drtp_topology_sampler_manifest.json").write_text(json.dumps(sampler.manifest(), indent=2) + "\n", encoding="utf-8")
    manifest = {"protocol": PROTOCOL, "status": "completed", "arm": arm, "seed": seed, "updates": UPDATES, "environment_steps": STEPS, "sampler_mode": ARMS[arm], "completed_return_signal": True, "from_scratch": True, "resume": False, "early_stopping": False, "checkpoint_promotion": False, "evaluation_during_training": False, "checkpoint_sha256": digest(run / "actor_critic_latest.pt")}
    (run / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed}, indent=2), flush=True)


def load_agent(checkpoint: Path, device: torch.device) -> RoleSharedSGMPPO:
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    env = make_env(1, "nominal")
    agent = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim).to(device)
    agent.load_state_dict(state["model"]); agent.eval()
    return agent


def evaluate_episode(agent: RoleSharedSGMPPO, group: str, seed: int, device: torch.device) -> dict:
    env = make_env(seed, group); _, share, graph = env.reset(); total = 0.0
    while not env.done:
        maybe_fault(env)
        with torch.no_grad():
            action = agent.action_value(*tensors(graph_stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
        _, share, graph, reward, _, info = env.step(action); total += float(reward[0, 0])
    return {"group": group, "score": total, "success": int(info["success"]), "collision": float(info["collision_pair"]), "timeout": int(info["timeout"])}


def evaluate(out: Path, arm: str, seed: int, device: torch.device) -> None:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("arm or seed is outside the frozen six-UAV contract")
    run = out / "runs" / arm / f"seed{seed}"
    checkpoint = run / "actor_critic_latest.pt"
    manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("checkpoint_sha256") != digest(checkpoint):
        raise RuntimeError("invalid frozen 10M run")
    agent = load_agent(checkpoint, device)
    rows = []
    for group_index, group in enumerate(ALL_GROUPS):
        for episode in range(EVALUATION_EPISODES):
            row = evaluate_episode(agent, group, 690000 + seed * 1000 + group_index * EVALUATION_EPISODES + episode, device)
            row.update({"arm": arm, "seed": seed, "episode": episode, "checkpoint_sha256": manifest["checkpoint_sha256"]}); rows.append(row)
    target = out / "evaluations" / arm / f"seed{seed}_final_10m.csv"; target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed, "episodes": len(rows)}, indent=2), flush=True)


def aggregate(out: Path) -> None:
    files = sorted((out / "evaluations").glob("*/*_final_10m.csv"))
    if len(files) != len(ARMS) * len(SEEDS):
        raise RuntimeError(f"expected ten endpoint files, found {len(files)}")
    raw = []
    for file in files:
        with file.open(newline="", encoding="utf-8") as handle: raw.extend(csv.DictReader(handle))
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for group in ALL_GROUPS:
                rows = [row for row in raw if row["arm"] == arm and int(row["seed"]) == seed and row["group"] == group]
                summary.append({"arm": arm, "seed": seed, "group": group, "episodes": len(rows), **{key: float(np.mean([float(row[key]) for row in rows])) for key in ("score", "success", "collision", "timeout")}})
    diag = out / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    for name, rows in (("DRTP_6UAV_CONDITION_ENDPOINTS.csv", summary),):
        with (diag / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    paired = []
    for seed in SEEDS:
        for group in ALL_GROUPS:
            utr = next(row for row in summary if row["arm"].startswith("utr_") and row["seed"] == seed and row["group"] == group)
            drtp = next(row for row in summary if row["arm"].startswith("drtp_") and row["seed"] == seed and row["group"] == group)
            paired.append({"seed": seed, "group": group, **{f"delta_{key}": drtp[key] - utr[key] for key in ("score", "success", "collision", "timeout")}})
    with (diag / "DRTP_6UAV_PAIRED_ENDPOINT_DELTAS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paired[0])); writer.writeheader(); writer.writerows(paired)
    report = {"protocol": PROTOCOL, "verdict": "DRTP_6UAV_CROSS_SCALE_ENDPOINT_REPORTED", "independent_unit": "training_seed", "training_seeds": list(SEEDS), "endpoint": "fixed_10m", "groups": list(ALL_GROUPS), "automatic_algorithm_revision": False, "automatic_continuation": False}
    (diag / "DRTP_6UAV_FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (diag / "DRTP_6UAV_FINAL_REPORT.md").write_text("# DRTP 6-UAV cross-scale endpoint report\n\n`DRTP_6UAV_CROSS_SCALE_ENDPOINT_REPORTED`\n\nThis is a matched fixed-endpoint report. Interpret mean, median, lower tail, paired directions, collision and timeout jointly; no automatic method revision follows.\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate", "aggregate"))
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode == "train": train(args.output_root, str(args.arm), int(args.seed), device)
    elif args.mode == "evaluate": evaluate(args.output_root, str(args.arm), int(args.seed), device)
    else: aggregate(args.output_root)


if __name__ == "__main__": main()
