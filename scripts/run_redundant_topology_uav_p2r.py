"""Corrected-learner P2-R baseline requalification runner (cloud only)."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.redundant_topology_role_sg_mappo import RoleSharedSGMPPO
from algorithms.redundant_topology_sg_mappo import SGMPPOConfig, checkpoint_payload, set_seed
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv
from scripts.run_redundant_topology_uav_p2 import (
    EVAL_EPISODES, GROUPS, MILESTONES, NOMINAL_ANCHOR, collect, episode_eval,
    graph_stack, make_env, reset_many, sha, tensors, update, write,
)

PROTOCOL = "P2_R_CORRECTED_LEARNER_REQUALIFICATION_V1"
SEEDS = (65011, 65012, 65013, 65014, 65015)
ARMS = ("plain_role_sg_mappo", "utr_role_sg_mappo")
CONTRACT = ROOT / "docs/redundant_topology_uav_p2r_20260903/P2_R_EXECUTION_CONTRACT.md"


def build_agent(env: RedundantTopologyUAVEnv, cfg: SGMPPOConfig, device: torch.device) -> RoleSharedSGMPPO:
    return RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim, cfg.hidden_dim, cfg.role_dim).to(device)


def q0(out: Path, seed: int, device: torch.device) -> None:
    """Tiny interface check; it is not performance training."""
    set_seed(seed)
    cfg = SGMPPOConfig(num_envs=2, rollout_steps=4, updates=1, ppo_epochs=1, minibatch_graphs=8)
    envs = [make_env(seed + index, "nominal") for index in range(2)]
    share, graph = reset_many(envs)
    agent = build_agent(envs[0], cfg, device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    batch, share, graph, _ = collect(agent, envs, share, graph, cfg, device)
    health = update(agent, optimizer, batch, cfg, device)
    checkpoint = out / "q0" / "runtime.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], 1, seed), checkpoint)
    clone = build_agent(envs[0], cfg, device)
    clone.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=False)["model"])
    with torch.no_grad():
        before = agent.action_value(*tensors(graph, share, device), deterministic=True)[1]
        after = clone.action_value(*tensors(graph, share, device), deterministic=True)[1]
    payload = {
        "protocol": PROTOCOL,
        "verdict": "P2_R_Q0_PASS" if torch.allclose(before, after) and all(np.isfinite(value) for value in health.values()) else "P2_R_Q0_FAIL",
        "checkpoint_restore_exact": bool(torch.allclose(before, after)),
        "finite_ppo_health": all(np.isfinite(value) for value in health.values()),
        "health": health,
        "formal_training_started": False,
    }
    write(out / "diagnostics" / "P2_R_Q0.json", json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    if payload["verdict"] != "P2_R_Q0_PASS":
        raise RuntimeError("corrected learner Q0 failed")


def train(out: Path, arm: str, seed: int, device: torch.device) -> None:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("arm or seed is outside the frozen P2-R contract")
    set_seed(seed)
    cfg = SGMPPOConfig()
    run = out / "runs" / arm / f"seed{seed}"
    run.mkdir(parents=True, exist_ok=False)
    groups = ("nominal",) if arm == "plain_role_sg_mappo" else GROUPS
    sampler_rng = np.random.default_rng(seed + 17)
    envs = [make_env(seed * 1000 + index, str(sampler_rng.choice(groups))) for index in range(cfg.num_envs)]
    share, graph = reset_many(envs)
    agent = build_agent(envs[0], cfg, device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    torch.save(checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], 0, seed), run / "runtime_0.pt")
    fields = ("update", "env_steps", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm", "episode_count", "episode_success")
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for update_index in range(1, cfg.updates + 1):
            batch, share, graph, episodes = collect(agent, envs, share, graph, cfg, device)
            health = update(agent, optimizer, batch, cfg, device)
            if not all(np.isfinite(value) for value in health.values()):
                raise RuntimeError("non-finite frozen PPO health scalar")
            for env in envs:
                env._p2_group = "nominal" if arm == "plain_role_sg_mappo" else str(sampler_rng.choice(GROUPS))
            writer.writerow({
                "update": update_index,
                "env_steps": update_index * cfg.num_envs * cfg.rollout_steps,
                **health,
                "episode_count": len(episodes),
                "episode_success": float(np.mean([item["success"] for item in episodes])) if episodes else "",
            })
            handle.flush()
            if update_index in MILESTONES:
                torch.save(checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], update_index, seed), run / f"runtime_{MILESTONES[update_index]}.pt")
    (run / "run_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL, "status": "completed", "arm": arm, "seed": seed,
        "groups": groups, "nominal_anchor": NOMINAL_ANCHOR, "updates": cfg.updates,
        "environment_steps": cfg.updates * cfg.num_envs * cfg.rollout_steps,
        "early_stopping": False, "best_checkpoint_promotion": False,
        "seed_replacement": False, "performance_rerun": False,
        "automatic_continuation": False,
    }, indent=2) + "\n", encoding="utf-8")


def load_agent(checkpoint: Path, device: torch.device) -> RoleSharedSGMPPO:
    payload = torch.load(checkpoint, map_location=device, weights_only=False)
    env = make_env(1, "nominal")
    agent = RoleSharedSGMPPO(env.obs_dim, env.share_obs_dim, env.action_dim).to(device)
    agent.load_state_dict(payload["model"])
    agent.eval()
    return agent


def evaluate(out: Path, arm: str, seed: int, device: torch.device) -> None:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("arm or seed is outside the frozen P2-R contract")
    run = out / "runs" / arm / f"seed{seed}"
    rows: list[dict[str, object]] = []
    for update_index, label in MILESTONES.items():
        checkpoint = run / f"runtime_{label}.pt"
        if not checkpoint.exists():
            raise RuntimeError(f"missing frozen checkpoint: {checkpoint}")
        agent = load_agent(checkpoint, device)
        for group_index, group in enumerate(GROUPS):
            for row in episode_eval(agent, group, 850000 + 10000 * seed + 100 * update_index + group_index * EVAL_EPISODES, EVAL_EPISODES, device):
                row.update({"arm": arm, "seed": seed, "update": update_index, "milestone": label})
                rows.append(row)
    target = out / "evaluations" / arm / f"seed{seed}_development.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("arm", "seed", "update", "milestone", "group", "success", "score", "collision", "timeout", "L_route", "L_message", "L_task"))
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"status": "P2_R_EVALUATION_COMPLETE", "arm": arm, "seed": seed, "episodes": len(rows), "development_only": True}))


def aggregate(out: Path) -> None:
    files = sorted((out / "evaluations").glob("*/*_development.csv"))
    if len(files) != len(ARMS) * len(SEEDS):
        raise RuntimeError(f"expected ten P2-R evaluation files, found {len(files)}")
    rows: list[dict[str, str]] = []
    for file in files:
        with file.open(encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    endpoint = [row for row in rows if row["milestone"] == "1m"]
    summary: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            for group in GROUPS:
                values = [row for row in endpoint if row["arm"] == arm and int(row["seed"]) == seed and row["group"] == group]
                summary.append({
                    "arm": arm, "seed": seed, "group": group,
                    "success": float(np.mean([float(row["success"]) for row in values])),
                    "mission_score": float(np.mean([float(row["score"]) for row in values])),
                    "collision": float(np.mean([float(row["collision"]) for row in values])),
                    "timeout": float(np.mean([float(row["timeout"]) for row in values])),
                })
    diag = out / "diagnostics"
    diag.mkdir(parents=True, exist_ok=True)
    with (diag / "P2_R_CONDITION_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    curves: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in MILESTONES.values():
                values = [row for row in rows if row["arm"] == arm and int(row["seed"]) == seed and row["milestone"] == label]
                curves.append({"arm": arm, "seed": seed, "milestone": label, "success": float(np.mean([float(row["success"]) for row in values])), "mission_score": float(np.mean([float(row["score"]) for row in values]))})
    with (diag / "P2_R_MILESTONE_CURVES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curves[0])); writer.writeheader(); writer.writerows(curves)
    plain_nominal = [next(row for row in summary if row["arm"] == ARMS[0] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_nominal = [next(row for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_r = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and str(row["group"]).startswith("R_")])) for seed in SEEDS]
    r_class = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["group"] == group])) for group in ("R_upstream", "R_downstream")]
    threshold = 0.50
    plain_ok = sum(value >= threshold for value in plain_nominal) >= 3
    utr_ok = np.median(utr_nominal) >= threshold and sum(value >= threshold for value in utr_r) >= 3 and all(value >= 0.10 for value in r_class)
    verdict = "P2_R_BASELINE_LEARNABILITY_PASS" if plain_ok and utr_ok else ("P2_R_NOMINAL_LEARNABILITY_ONLY" if plain_ok else "P2_R_BASE_TASK_NOT_LEARNABLE")
    payload = {"protocol": PROTOCOL, "verdict": verdict, "plain_nominal_success": plain_nominal, "utr_nominal_success": utr_nominal, "utr_tier_r_success": utr_r, "r_class_success": r_class, "threshold": threshold, "independent_unit": "training_seed", "p3_authorized": False, "automatic_continuation": False}
    shutil.copyfile(CONTRACT, diag / "P2_R_EXECUTION_CONTRACT.md")
    write(diag / "P2_R_EVAL_TAPE_MANIFEST.md", "# P2-R frozen development tape\n\nGroups: " + ", ".join(GROUPS) + f". Episodes/group/milestone={EVAL_EPISODES}. Hash: `{sha({'groups': GROUPS, 'episodes': EVAL_EPISODES, 'milestones': MILESTONES})}`.\n")
    write(diag / "P2_R_FINAL_VERDICT.md", f"# P2-R final verdict\n\n`{verdict}`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n")
    write(diag / "P2_R_GATE_DECISION.json", json.dumps(payload, indent=2) + "\n")
    write(diag / "P2_R_BAD_SEED_REGISTER.md", "# P2-R bad-seed register\n\nAll ten frozen trajectories are retained; no seed replacement, rerun or best-checkpoint promotion occurred.\n")
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("q0", "train", "evaluate", "aggregate"))
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2r")
    parser.add_argument("--arm")
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "mode": args.mode, "execute_required": True, "cloud_only": True}, indent=2)); return
    out = Path(args.output_root)
    out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode == "q0": q0(out, args.seed, device)
    elif args.mode == "train": train(out, args.arm, args.seed, device)
    elif args.mode == "evaluate": evaluate(out, args.arm, args.seed, device)
    else: aggregate(out)


if __name__ == "__main__":
    main()
