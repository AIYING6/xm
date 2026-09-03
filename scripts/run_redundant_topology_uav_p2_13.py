"""P2.13 Scout-and-Terminal assigned baseline requalification runner."""
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

from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config
import scripts.run_redundant_topology_uav_p2r as core

PROTOCOL = "P2_13_SCOUT_TERMINAL_ASSIGNED_BASELINE_REQUALIFICATION_V1"
SEEDS = (67011, 67012, 67013, 67014, 67015)
ARMS = ("plain_scout_terminal_assigned_role_sg_mappo", "utr_scout_terminal_assigned_role_sg_mappo")
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_13_20260903/P2_13_ASSIGNED_BASELINE_REQUALIFICATION_CONTRACT.md"
AUTHORIZATION = ROOT / "docs/redundant_topology_uav_p2_13_20260903/P2_13_TRAINING_AUTHORIZATION.md"


def make_env(seed: int, group: str) -> RedundantTopologyUAVEnv:
    env = RedundantTopologyUAVEnv(scale_config(
        "main", seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000,
        assignment_observation=True, scout_assignment_observation=True,
    ))
    env._p2_group = group
    return env


def configure_core() -> None:
    core.make_env = make_env
    core.PROTOCOL = PROTOCOL
    core.SEEDS = SEEDS
    core.ARMS = ARMS
    core.CONTRACT = CONTRACT
    core.episode_eval.__globals__["make_env"] = make_env


def q0(out: Path, seed: int, device: torch.device) -> None:
    core.q0(out, seed, device)
    legacy = out / "diagnostics" / "P2_R_Q0.json"
    payload = json.loads(legacy.read_text(encoding="utf-8"))
    payload["protocol"] = PROTOCOL
    payload["verdict"] = "P2_13_Q0_PASS" if payload["verdict"] == "P2_R_Q0_PASS" else "P2_13_Q0_FAIL"
    target = out / "diagnostics" / "P2_13_Q0.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    legacy.unlink()
    print(json.dumps(payload, indent=2))
    if payload["verdict"] != "P2_13_Q0_PASS":
        raise RuntimeError("P2.13 Q0 failed")


def training_groups(arm: str) -> tuple[str, ...]:
    """Return the frozen collection distribution for a P2.13 arm."""
    if arm not in ARMS:
        raise ValueError("arm is outside the frozen P2.13 contract")
    return ("nominal",) if arm == ARMS[0] else tuple(core.GROUPS)


def train(out: Path, arm: str, seed: int, device: torch.device) -> None:
    """Train one frozen P2.13 trajectory without inheriting P2-R arm names."""
    if seed not in SEEDS:
        raise ValueError("seed is outside the frozen P2.13 contract")
    groups = training_groups(arm)
    core.set_seed(seed)
    cfg = core.SGMPPOConfig()
    run = out / "runs" / arm / f"seed{seed}"
    run.mkdir(parents=True, exist_ok=False)
    sampler_rng = np.random.default_rng(seed + 17)
    envs = [make_env(seed * 1000 + index, str(sampler_rng.choice(groups))) for index in range(cfg.num_envs)]
    share, graph = core.reset_many(envs)
    agent = core.build_agent(envs[0], cfg, device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    torch.save(core.checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], 0, seed), run / "runtime_0.pt")
    fields = ("update", "env_steps", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm", "episode_count", "episode_success")
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for update_index in range(1, cfg.updates + 1):
            batch, share, graph, episodes = core.collect(agent, envs, share, graph, cfg, device)
            health = core.update(agent, optimizer, batch, cfg, device)
            if not all(np.isfinite(value) for value in health.values()):
                raise RuntimeError("non-finite frozen PPO health scalar")
            for env in envs:
                env._p2_group = "nominal" if arm == ARMS[0] else str(sampler_rng.choice(core.GROUPS))
            writer.writerow({
                "update": update_index,
                "env_steps": update_index * cfg.num_envs * cfg.rollout_steps,
                **health,
                "episode_count": len(episodes),
                "episode_success": float(np.mean([item["success"] for item in episodes])) if episodes else "",
            })
            handle.flush()
            if update_index in core.MILESTONES:
                torch.save(core.checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], update_index, seed), run / f"runtime_{core.MILESTONES[update_index]}.pt")
    (run / "run_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL, "status": "completed", "arm": arm, "seed": seed,
        "groups": groups, "nominal_anchor": core.NOMINAL_ANCHOR, "updates": cfg.updates,
        "environment_steps": cfg.updates * cfg.num_envs * cfg.rollout_steps,
        "early_stopping": False, "best_checkpoint_promotion": False,
        "seed_replacement": False, "performance_rerun": False,
        "automatic_continuation": False,
    }, indent=2) + "\n", encoding="utf-8")


def aggregate(out: Path) -> None:
    files = sorted((out / "evaluations").glob("*/*_development.csv"))
    if len(files) != len(ARMS) * len(SEEDS):
        raise RuntimeError(f"expected ten P2.13 evaluation files, found {len(files)}")
    rows: list[dict[str, str]] = []
    for file in files:
        with file.open(encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    endpoint = [row for row in rows if row["milestone"] == "1m"]
    summary: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            for group in core.GROUPS:
                values = [row for row in endpoint if row["arm"] == arm and int(row["seed"]) == seed and row["group"] == group]
                summary.append({"arm": arm, "seed": seed, "group": group, "success": float(np.mean([float(row["success"]) for row in values])), "mission_score": float(np.mean([float(row["score"]) for row in values])), "collision": float(np.mean([float(row["collision"]) for row in values])), "timeout": float(np.mean([float(row["timeout"]) for row in values]))})
    diag = out / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    with (diag / "P2_13_CONDITION_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    curves: list[dict[str, object]] = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in core.MILESTONES.values():
                values = [row for row in rows if row["arm"] == arm and int(row["seed"]) == seed and row["milestone"] == label]
                curves.append({"arm": arm, "seed": seed, "milestone": label, "success": float(np.mean([float(row["success"]) for row in values])), "mission_score": float(np.mean([float(row["score"]) for row in values]))})
    with (diag / "P2_13_MILESTONE_CURVES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curves[0])); writer.writeheader(); writer.writerows(curves)
    plain = [next(row for row in summary if row["arm"] == ARMS[0] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_nominal = [next(row for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_r = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and str(row["group"]).startswith("R_")])) for seed in SEEDS]
    r_class = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["group"] == group])) for group in ("R_upstream", "R_downstream")]
    threshold = 0.50
    plain_ok = sum(value >= threshold for value in plain) >= 3
    utr_ok = np.median(utr_nominal) >= threshold and sum(value >= threshold for value in utr_r) >= 3 and all(value >= 0.10 for value in r_class)
    verdict = "P2_13_BASELINE_LEARNABILITY_PASS" if plain_ok and utr_ok else ("P2_13_NOMINAL_LEARNABILITY_ONLY" if plain_ok else "P2_13_BASE_TASK_NOT_LEARNABLE")
    payload = {"protocol": PROTOCOL, "verdict": verdict, "plain_nominal_success": plain, "utr_nominal_success": utr_nominal, "utr_tier_r_success": utr_r, "r_class_success": r_class, "threshold": threshold, "independent_unit": "training_seed", "p3_authorized": False, "automatic_continuation": False}
    shutil.copyfile(CONTRACT, diag / "P2_13_EXECUTION_CONTRACT.md")
    shutil.copyfile(AUTHORIZATION, diag / "P2_13_TRAINING_AUTHORIZATION.md")
    tape_hash = core.sha({"groups": core.GROUPS, "episodes": core.EVAL_EPISODES, "milestones": core.MILESTONES})
    (diag / "P2_13_EVAL_TAPE_MANIFEST.md").write_text(f"# P2.13 frozen development tape\n\nGroups: {', '.join(core.GROUPS)}. Episodes/group/milestone={core.EVAL_EPISODES}. Hash: `{tape_hash}`.\n", encoding="utf-8")
    (diag / "P2_13_BAD_SEED_REGISTER.md").write_text("# P2.13 bad-seed register\n\nAll ten frozen trajectories are retained; no seed replacement, rerun, or best-checkpoint promotion occurred.\n", encoding="utf-8")
    (diag / "P2_13_FINAL_VERDICT.md").write_text("# P2.13 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    (diag / "P2_13_GATE_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("q0", "train", "evaluate", "aggregate"))
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_13")
    parser.add_argument("--arm")
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "mode": args.mode, "execute_required": True, "cloud_only": True}, indent=2)); return
    if not AUTHORIZATION.is_file():
        raise RuntimeError("P2.13 explicit training authorization artifact is missing")
    configure_core()
    out = Path(args.output_root); out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode == "q0": q0(out, args.seed, device)
    elif args.mode == "train": train(out, args.arm, args.seed, device)
    elif args.mode == "evaluate": core.evaluate(out, args.arm, args.seed, device)
    else: aggregate(out)


if __name__ == "__main__":
    main()
