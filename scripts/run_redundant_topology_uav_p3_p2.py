"""Frozen P3-P2 fresh-seed static-topology curriculum pilot (cloud only)."""
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

from algorithms.redundant_topology_staged_schedule import StaticTopologySchedule
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config
import scripts.run_redundant_topology_uav_p2r as core

PROTOCOL = "REDUNDANT-TOPOLOGY-UAV-P3-P2-STATIC-CURRICULUM-PILOT-V1"
SEEDS = (68011, 68012, 68013, 68014, 68015)
ARMS = ("utr_scout_terminal_assigned_role_sg_mappo", "staged_topology_scout_terminal_assigned_role_sg_mappo")
UTR, STAGED = ARMS
CONTRACT = ROOT / "docs/redundant_topology_uav_p3_20260903/P3_P2_FRESH_PILOT_CONTRACT.md"
AUTHORIZATION = ROOT / "docs/redundant_topology_uav_p3_20260903/P3_P2_TRAINING_AUTHORIZATION.md"


def make_env(seed: int, group: str) -> RedundantTopologyUAVEnv:
    env = RedundantTopologyUAVEnv(scale_config(
        "main", seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000,
        assignment_observation=True, scout_assignment_observation=True,
    ))
    env._p2_group = group
    return env


def configure_core() -> None:
    core.make_env = make_env
    core.episode_eval.__globals__["make_env"] = make_env


def assert_member(arm: str, seed: int) -> None:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("arm or seed is outside the frozen P3-P2 contract")


def q0(out: Path, seed: int, device: torch.device) -> None:
    core.q0(out, seed, device)
    legacy = out / "diagnostics" / "P2_R_Q0.json"
    payload = json.loads(legacy.read_text(encoding="utf-8"))
    payload.update({"protocol": PROTOCOL, "verdict": "P3_P2_Q0_PASS" if payload["verdict"] == "P2_R_Q0_PASS" else "P3_P2_Q0_FAIL", "formal_training_started": False})
    legacy.unlink()
    (out / "diagnostics" / "P3_P2_Q0.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["verdict"] != "P3_P2_Q0_PASS":
        raise RuntimeError("P3-P2 Q0 failed")


def group_for(arm: str, update_index: int, rng: np.random.Generator, schedule: StaticTopologySchedule) -> str:
    return str(rng.choice(core.GROUPS)) if arm == UTR else schedule.sample(update_index, rng)


def train(out: Path, arm: str, seed: int, device: torch.device) -> None:
    assert_member(arm, seed)
    core.set_seed(seed)
    cfg = core.SGMPPOConfig()
    if cfg.updates != 3907:
        raise RuntimeError("P3-P2 requires the frozen 3,907-update budget")
    run = out / "runs" / arm / f"seed{seed}"
    run.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(seed + 17)
    schedule = StaticTopologySchedule()
    envs = [make_env(seed * 1000 + index, group_for(arm, 0, rng, schedule)) for index in range(cfg.num_envs)]
    share, graph = core.reset_many(envs)
    agent = core.build_agent(envs[0], cfg, device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=cfg.lr)
    torch.save(core.checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], 0, seed), run / "runtime_0.pt")
    fields = ("update", "env_steps", "stage", "policy_loss", "value_loss", "entropy", "approx_kl", "clip_fraction", "grad_norm", "episode_count", "episode_success")
    with (run / "train_log.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for update_index in range(1, cfg.updates + 1):
            batch, share, graph, episodes = core.collect(agent, envs, share, graph, cfg, device)
            health = core.update(agent, optimizer, batch, cfg, device)
            if not all(np.isfinite(value) for value in health.values()):
                raise RuntimeError("non-finite PPO health scalar")
            next_index = min(update_index, cfg.updates - 1)
            for env in envs:
                env._p2_group = group_for(arm, next_index, rng, schedule)
            writer.writerow({"update": update_index, "env_steps": update_index * cfg.num_envs * cfg.rollout_steps,
                             "stage": "uniform_all" if arm == UTR else "|".join(schedule.groups_for_update(min(update_index - 1, cfg.updates - 1))),
                             **health, "episode_count": len(episodes),
                             "episode_success": float(np.mean([item["success"] for item in episodes])) if episodes else ""})
            handle.flush()
            if update_index in core.MILESTONES:
                torch.save(core.checkpoint_payload(agent, optimizer, [env.runtime_state_dict() for env in envs], update_index, seed), run / f"runtime_{core.MILESTONES[update_index]}.pt")
    manifest = {"protocol": PROTOCOL, "status": "completed", "arm": arm, "seed": seed,
                "updates": cfg.updates, "environment_steps": cfg.updates * cfg.num_envs * cfg.rollout_steps,
                "sampling": "uniform_all" if arm == UTR else schedule.manifest(), "early_stopping": False,
                "best_checkpoint_promotion": False, "seed_replacement": False, "performance_rerun": False,
                "automatic_continuation": False}
    (run / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def evaluate(out: Path, arm: str, seed: int, device: torch.device) -> None:
    assert_member(arm, seed)
    core.evaluate(out, arm, seed, device)


def aggregate(out: Path) -> None:
    files = sorted((out / "evaluations").glob("*/*_development.csv"))
    if len(files) != len(ARMS) * len(SEEDS):
        raise RuntimeError(f"expected ten P3-P2 evaluation files, found {len(files)}")
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
                summary.append({"arm": arm, "seed": seed, "group": group,
                                "success": float(np.mean([float(row["success"]) for row in values])),
                                "mission_score": float(np.mean([float(row["score"]) for row in values])),
                                "collision": float(np.mean([float(row["collision"]) for row in values])),
                                "timeout": float(np.mean([float(row["timeout"]) for row in values]))})
    diag = out / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    with (diag / "P3_P2_CONDITION_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    paired: list[dict[str, object]] = []
    for seed in SEEDS:
        def average(arm: str, key: str, groups: tuple[str, ...]) -> float:
            return float(np.mean([row[key] for row in summary if row["arm"] == arm and row["seed"] == seed and row["group"] in groups]))
        paired.append({"seed": seed, "all_success_delta": average(STAGED, "success", core.GROUPS) - average(UTR, "success", core.GROUPS),
                       "non_nominal_success_delta": average(STAGED, "success", tuple(group for group in core.GROUPS if group != "nominal")) - average(UTR, "success", tuple(group for group in core.GROUPS if group != "nominal")),
                       "nominal_success_delta": average(STAGED, "success", ("nominal",)) - average(UTR, "success", ("nominal",)),
                       "collision_delta": average(STAGED, "collision", core.GROUPS) - average(UTR, "collision", core.GROUPS)})
    with (diag / "P3_P2_PAIRED_SEED_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paired[0])); writer.writeheader(); writer.writerows(paired)
    mean_all = float(np.mean([row["all_success_delta"] for row in paired]))
    support = sum(row["all_success_delta"] > 0 for row in paired)
    nominal_ok = sum(row["nominal_success_delta"] >= -0.05 for row in paired) >= 4
    safety_ok = sum(row["collision_delta"] <= 0.05 for row in paired) >= 4
    verdict = "P3_P2_SAFETY_NO_GO" if not safety_ok else ("P3_P2_SIGNAL_PASS" if mean_all >= 0.05 and support >= 4 and nominal_ok else "P3_P2_NO_SIGNAL")
    payload = {"protocol": PROTOCOL, "verdict": verdict, "mean_all_group_success_delta": mean_all,
               "positive_all_group_seed_count": support, "nominal_nonharm_seed_count": sum(row["nominal_success_delta"] >= -0.05 for row in paired),
               "collision_nonworsening_seed_count": sum(row["collision_delta"] <= 0.05 for row in paired),
               "independent_unit": "training_seed", "evaluation": "fixed_development_tape_only",
               "p3_p3_authorized": False, "automatic_continuation": False}
    shutil.copyfile(CONTRACT, diag / "P3_P2_EXECUTION_CONTRACT.md")
    shutil.copyfile(AUTHORIZATION, diag / "P3_P2_TRAINING_AUTHORIZATION.md")
    (diag / "P3_P2_FINAL_VERDICT.md").write_text("# P3-P2 final verdict\n\n`" + verdict + "`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    (diag / "P3_P2_GATE_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("q0", "train", "evaluate", "aggregate"))
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p3_p2")
    parser.add_argument("--arm"); parser.add_argument("--seed", type=int, default=SEEDS[0]); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "mode": args.mode, "execute_required": True, "cloud_only": True}, indent=2)); return
    if not CONTRACT.is_file() or not AUTHORIZATION.is_file():
        raise RuntimeError("P3-P2 frozen contract or authorization artifact is missing")
    configure_core(); out = Path(args.output_root); out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode == "q0": q0(out, args.seed, device)
    elif args.mode == "train": train(out, args.arm, args.seed, device)
    elif args.mode == "evaluate": evaluate(out, args.arm, args.seed, device)
    else: aggregate(out)


if __name__ == "__main__":
    main()
