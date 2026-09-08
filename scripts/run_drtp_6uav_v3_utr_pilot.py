"""Frozen UTR-only learnability pilot for the independent 6-UAV V3 task.

This runner intentionally has one arm (UTR).  It is a qualification experiment,
not a DRTP comparison and not manuscript evidence.
"""
from __future__ import annotations

import argparse, csv, json, random, sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_sg_mappo import SGMPPOConfig, gae, set_seed
from algorithms.sustained_support_role_sg_mappo import SustainedSupportRoleSharedSGMPPO, v3_policy_spec
from scripts.run_drtp_6uav_v3_q0 import GROUPS, fault_spec, make_env

PROTOCOL = "DRTP-6UAV-V3-UTR-LEARNABILITY-PILOT-V1"
SEEDS = (94011, 94012, 94013)
UPDATES, NUM_ENVS, ROLLOUT_STEPS, EVAL_EPISODES = 3907, 4, 64, 40


def stack(graphs):
    return {"obs": np.stack([x["node_features"] for x in graphs]).astype(np.float32), "roles": np.stack([x["roles"] for x in graphs]).astype(np.int64), "adj": np.stack([x["active_adj"] for x in graphs]).astype(np.float32), "masks": np.stack([x["action_masks"] for x in graphs]).astype(np.float32)}


def ts(graph, share, device):
    return tuple(torch.as_tensor(graph[key], device=device) for key in ("obs", "roles", "adj", "masks")) + (torch.as_tensor(share, dtype=torch.float32, device=device),)


def reset_many(envs):
    values = [env.reset() for env in envs]
    return np.stack([x[1] for x in values]), stack([x[2] for x in values])


def fault(env, group):
    if group != "nominal" and env.step_count == env.semantic_config.fault_transition - 1:
        spec = fault_spec(env, group); env.set_failure(spec["edges"], spec["nodes"])


def collect(agent, envs, groups, share, graph, cfg, device):
    buffer = {key: [] for key in ("obs", "roles", "adj", "masks", "share", "actions", "logp", "values", "rewards", "dones")}
    records = []
    for _ in range(ROLLOUT_STEPS):
        with torch.no_grad(): actions, logp, _, values = agent.action_value(*ts(graph, share, device))
        next_share, next_graph, rewards, dones = [], [], [], []
        for index, env in enumerate(envs):
            fault(env, groups[index]); _, current_share, current_graph, reward, done, info = env.step(actions[index].cpu().numpy())
            if bool(done.all()):
                records.append({"group": groups[index], "success": int(info["success"]), "timeout": int(info["timeout"]), "collision": float(info["collision_pair"]), "score": float(reward[0, 0])})
                current_share, current_graph = env.reset()[1:]
            next_share.append(current_share); next_graph.append(current_graph); rewards.append(reward[:, 0]); dones.append(done[:, 0])
        for key in ("obs", "roles", "adj", "masks"): buffer[key].append(graph[key].copy())
        buffer["share"].append(share.copy()); buffer["actions"].append(actions.cpu().numpy()); buffer["logp"].append(logp.cpu().numpy()); buffer["values"].append(values.cpu().numpy()); buffer["rewards"].append(np.asarray(rewards)); buffer["dones"].append(np.asarray(dones))
        share, graph = np.stack(next_share), stack(next_graph)
    with torch.no_grad(): bootstrap = agent.critic(torch.as_tensor(share, dtype=torch.float32, device=device)).squeeze(-1).unsqueeze(-1).expand(-1, envs[0].n).cpu().numpy()
    for key in buffer: buffer[key] = np.asarray(buffer[key])
    buffer["advantages"], buffer["returns"] = gae(buffer["rewards"], buffer["dones"], buffer["values"], bootstrap, cfg.gamma, cfg.gae_lambda)
    return buffer, share, graph, records


def update(agent, optimizer, batch, cfg, device):
    steps, batches, agents = batch["actions"].shape; total = steps * batches
    source = {key: torch.as_tensor(batch[key].reshape(total, *batch[key].shape[2:]), device=device) for key in ("obs", "roles", "adj", "masks", "share", "actions", "logp", "returns")}
    advantage = torch.as_tensor(batch["advantages"].reshape(total, agents), dtype=torch.float32, device=device); advantage = (advantage - advantage.mean()) / (advantage.std() + 1e-8)
    indexes = np.arange(total); values = {key: [] for key in ("policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm")}
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indexes)
        for start in range(0, total, cfg.minibatch_graphs):
            chosen = indexes[start:start + cfg.minibatch_graphs]
            _, logp, entropy, predicted = agent.action_value(source["obs"][chosen].float(), source["roles"][chosen].long(), source["adj"][chosen].float(), source["masks"][chosen].float(), source["share"][chosen].float(), source["actions"][chosen].long())
            ratio = (logp - source["logp"][chosen].float()).exp(); unclipped = -advantage[chosen] * ratio; clipped = -advantage[chosen] * ratio.clamp(1 - cfg.clip_coef, 1 + cfg.clip_coef)
            policy = torch.maximum(unclipped, clipped).mean(); value = .5 * (source["returns"][chosen].float() - predicted).pow(2).mean(); loss = policy + cfg.value_coef * value - cfg.entropy_coef * entropy.mean()
            optimizer.zero_grad(); loss.backward(); norm = float(nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)); optimizer.step()
            values["policy_loss"].append(float(policy.detach())); values["value_loss"].append(float(value.detach())); values["entropy"].append(float(entropy.mean().detach())); values["approx_kl"].append(float((source["logp"][chosen].float() - logp).mean().detach())); values["clip_fraction"].append(float(((ratio - 1).abs() > cfg.clip_coef).float().mean().detach())); values["grad_norm"].append(norm)
    return {key: float(np.mean(value)) for key, value in values.items()}


def checkpoint(agent, optimizer, update, seed):
    return {"format": "drtp_6uav_v3_utr_pilot_runtime_v1", "protocol": PROTOCOL, "seed": seed, "update": update, "model": agent.state_dict(), "optimizer": optimizer.state_dict(), "torch_rng": torch.get_rng_state(), "numpy_rng": np.random.get_state(), "python_rng": random.getstate()}


def train(root, seed, device):
    run = root / "runs" / "utr_v3" / f"seed{seed}"
    run.mkdir(parents=True, exist_ok=False); set_seed(seed); cfg = SGMPPOConfig(num_envs=NUM_ENVS, rollout_steps=ROLLOUT_STEPS, updates=UPDATES)
    rng = np.random.default_rng(seed + 17); groups = [str(rng.choice(GROUPS)) for _ in range(NUM_ENVS)]; envs = [make_env(seed * 1000 + index) for index in range(NUM_ENVS)]; share, graph = reset_many(envs); agent = SustainedSupportRoleSharedSGMPPO(envs[0].obs_dim, envs[0].share_obs_dim, cfg.hidden_dim, cfg.role_dim).to(device); optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    fields = ["update", "env_steps", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm", "episodes", "success"]
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for number in range(1, UPDATES + 1):
            batch, share, graph, episodes = collect(agent, envs, groups, share, graph, cfg, device); health = update(agent, optimizer, batch, cfg, device)
            groups = [str(rng.choice(GROUPS)) for _ in range(NUM_ENVS)]
            writer.writerow({"update": number, "env_steps": number * NUM_ENVS * ROLLOUT_STEPS, **health, "episodes": len(episodes), "success": float(np.mean([x["success"] for x in episodes])) if episodes else ""}); handle.flush()
    torch.save(checkpoint(agent, optimizer, UPDATES, seed), run / "actor_critic_latest.pt")
    (run / "run_manifest.json").write_text(json.dumps({"protocol": PROTOCOL, "status": "completed", "arm": "utr_v3", "seed": seed, "updates": UPDATES, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS, "groups": GROUPS, "selection": "fixed_final_endpoint_only", "drtp_training_started": False}, indent=2) + "\n", encoding="utf-8")


def load_agent(root, seed, device):
    env = make_env(seed)
    agent = SustainedSupportRoleSharedSGMPPO(env.obs_dim, env.share_obs_dim).to(device)
    state = torch.load(root / "runs" / "utr_v3" / f"seed{seed}" / "actor_critic_latest.pt", map_location=device, weights_only=False)
    if state.get("protocol") != PROTOCOL or state.get("update") != UPDATES:
        raise RuntimeError("pilot evaluation requires the fixed final endpoint")
    agent.load_state_dict(state["model"]); agent.eval(); return agent


def evaluate(root, seed, device):
    agent = load_agent(root, seed, device); rows = []
    for group_index, group in enumerate(GROUPS):
        for episode_number in range(EVAL_EPISODES):
            env = make_env(1_200_000 + seed * 1_000 + group_index * EVAL_EPISODES + episode_number); _, share, graph = env.reset(); total = 0.0
            while not env.done:
                fault(env, group)
                with torch.no_grad(): action = agent.action_value(*ts(stack([graph]), share[None], device), deterministic=True)[0][0].cpu().numpy()
                _, share, graph, reward, _, info = env.step(action); total += float(reward[0, 0])
            rows.append({"seed": seed, "group": group, "episode": episode_number, "score": total, "success": int(info["success"]), "timeout": int(info["timeout"]), "collision": float(info["collision_pair"])})
    target = root / "evaluations" / f"seed{seed}_final.csv"; target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def aggregate(root):
    files = [root / "evaluations" / f"seed{seed}_final.csv" for seed in SEEDS]
    if not all(path.is_file() for path in files): raise RuntimeError("missing fixed-endpoint pilot evaluation")
    rows = [row for path in files for row in csv.DictReader(path.open(encoding="utf-8"))]
    summary = []
    for seed in SEEDS:
        for group in GROUPS:
            values = [row for row in rows if int(row["seed"]) == seed and row["group"] == group]
            summary.append({"seed": seed, "group": group, "mean_score": float(np.mean([float(x["score"]) for x in values])), "success": float(np.mean([float(x["success"]) for x in values])), "timeout": float(np.mean([float(x["timeout"]) for x in values])), "collision": float(np.mean([float(x["collision"]) for x in values]))})
    nominal = [row["success"] for row in summary if row["group"] == "nominal"]
    perturbed = [row["success"] for row in summary if row["group"] != "nominal"]
    checks = {"nominal_learnable_two_of_three": sum(x >= .50 for x in nominal) >= 2, "perturbed_not_ceiling": float(np.mean(perturbed)) < .90, "perturbed_not_global_failure": float(np.mean(perturbed)) > .10}
    payload = {"protocol": PROTOCOL, "verdict": "V3_UTR_LEARNABILITY_PILOT_PASS" if all(checks.values()) else "V3_UTR_LEARNABILITY_PILOT_FAIL", "training_seeds": SEEDS, "fixed_endpoint_updates": UPDATES, "checks": checks, "summary": summary, "drtp_training_started": False, "automatic_continuation": False}
    diag = root / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    with (diag / "V3_UTR_PILOT_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle: writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    (diag / "V3_UTR_PILOT_VERDICT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "V3_UTR_PILOT_REPORT.md").write_text("# V3 UTR learnability pilot\n\n`" + payload["verdict"] + "`\n\nThis UTR-only qualification does not compare DRTP or authorize a manuscript claim.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate", "aggregate")); parser.add_argument("--seed", type=int, choices=SEEDS); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode in {"train", "evaluate"} and args.seed is None: raise SystemExit("--seed required for train/evaluate")
    if args.mode == "train": train(args.output_root, args.seed, device); print(json.dumps({"protocol": PROTOCOL, "status": "completed", "seed": args.seed, "drtp_training_started": False}))
    elif args.mode == "evaluate": evaluate(args.output_root, args.seed, device)
    else: aggregate(args.output_root)


if __name__ == "__main__": main()
