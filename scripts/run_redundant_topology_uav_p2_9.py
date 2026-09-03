"""P2.9 assigned-observation baseline qualification runner (cloud only)."""
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
from algorithms.redundant_topology_sg_mappo import SGMPPOConfig, checkpoint_payload
from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config
import scripts.run_redundant_topology_uav_p2r as core

PROTOCOL = "P2_9_ASSIGNED_BASELINE_QUALIFICATION_V1"
SEEDS = (66011, 66012, 66013, 66014, 66015)
ARMS = ("plain_assigned_role_sg_mappo", "utr_assigned_role_sg_mappo")
CONTRACT = ROOT / "docs/redundant_topology_uav_p2_9_20260903/P2_9_ASSIGNED_BASELINE_QUALIFICATION_CONTRACT.md"


def make_env(seed: int, group: str) -> RedundantTopologyUAVEnv:
    env = RedundantTopologyUAVEnv(scale_config("main", seed_env=seed, seed_comm=seed + 100_000, seed_topology=seed + 200_000, assignment_observation=True))
    env._p2_group = group
    return env


def configure_core() -> None:
    # Reuse only tested rollout/PPO accounting; replace its environment factory,
    # contract identity, arms and seed registry before every execution mode.
    core.make_env = make_env
    core.PROTOCOL = PROTOCOL
    core.SEEDS = SEEDS
    core.ARMS = ARMS
    core.CONTRACT = CONTRACT
    # ``episode_eval`` originates in the P2 runner, so its function globals
    # otherwise retain P2's unassigned environment factory. Bind the P2.9
    # factory before every evaluation.
    core.episode_eval.__globals__["make_env"] = make_env


def q0(out: Path, seed: int, device: torch.device) -> None:
    """Run the inherited smoke check but preserve P2.9-only provenance."""
    core.q0(out, seed, device)
    legacy = out / "diagnostics" / "P2_R_Q0.json"
    payload = json.loads(legacy.read_text(encoding="utf-8"))
    payload["protocol"] = PROTOCOL
    payload["verdict"] = "P2_9_Q0_PASS" if payload["verdict"] == "P2_R_Q0_PASS" else "P2_9_Q0_FAIL"
    target = out / "diagnostics" / "P2_9_Q0.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    legacy.unlink()
    print(json.dumps(payload, indent=2))
    if payload["verdict"] != "P2_9_Q0_PASS":
        raise RuntimeError("P2.9 Q0 failed")


def aggregate(out: Path) -> None:
    files = sorted((out / "evaluations").glob("*/*_development.csv"))
    if len(files) != 10:
        raise RuntimeError(f"expected ten P2.9 evaluation files, found {len(files)}")
    rows = []
    for file in files:
        with file.open(encoding="utf-8") as handle: rows.extend(csv.DictReader(handle))
    endpoint = [row for row in rows if row["milestone"] == "1m"]
    summary = []
    for arm in ARMS:
        for seed in SEEDS:
            for group in core.GROUPS:
                values = [row for row in endpoint if row["arm"] == arm and int(row["seed"]) == seed and row["group"] == group]
                summary.append({"arm": arm, "seed": seed, "group": group, "success": float(np.mean([float(row["success"]) for row in values])), "mission_score": float(np.mean([float(row["score"]) for row in values])), "collision": float(np.mean([float(row["collision"]) for row in values])), "timeout": float(np.mean([float(row["timeout"]) for row in values]))})
    diag = out / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    with (diag / "P2_9_CONDITION_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    curves = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in core.MILESTONES.values():
                values = [row for row in rows if row["arm"] == arm and int(row["seed"]) == seed and row["milestone"] == label]
                curves.append({"arm": arm, "seed": seed, "milestone": label, "success": float(np.mean([float(row["success"]) for row in values])), "mission_score": float(np.mean([float(row["score"]) for row in values]))})
    with (diag / "P2_9_MILESTONE_CURVES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curves[0])); writer.writeheader(); writer.writerows(curves)
    plain = [next(row for row in summary if row["arm"] == ARMS[0] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_nominal = [next(row for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and row["group"] == "nominal")["success"] for seed in SEEDS]
    utr_r = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["seed"] == seed and str(row["group"]).startswith("R_")])) for seed in SEEDS]
    r_class = [float(np.mean([row["success"] for row in summary if row["arm"] == ARMS[1] and row["group"] == group])) for group in ("R_upstream", "R_downstream")]
    threshold = 0.50
    plain_ok = sum(value >= threshold for value in plain) >= 3
    utr_ok = np.median(utr_nominal) >= threshold and sum(value >= threshold for value in utr_r) >= 3 and all(value >= 0.10 for value in r_class)
    verdict = "P2_9_BASELINE_LEARNABILITY_PASS" if plain_ok and utr_ok else ("P2_9_NOMINAL_LEARNABILITY_ONLY" if plain_ok else "P2_9_BASE_TASK_NOT_LEARNABLE")
    payload = {"protocol": PROTOCOL, "verdict": verdict, "plain_nominal_success": plain, "utr_nominal_success": utr_nominal, "utr_tier_r_success": utr_r, "r_class_success": r_class, "threshold": threshold, "independent_unit": "training_seed", "p3_authorized": False, "automatic_continuation": False}
    shutil.copyfile(CONTRACT, diag / "P2_9_EXECUTION_CONTRACT.md")
    tape_hash = core.sha({"groups": core.GROUPS, "episodes": core.EVAL_EPISODES, "milestones": core.MILESTONES})
    (diag / "P2_9_EVAL_TAPE_MANIFEST.md").write_text(
        "# P2.9 frozen development tape\n\n"
        f"Groups: {', '.join(core.GROUPS)}. Episodes/group/milestone={core.EVAL_EPISODES}. Hash: `{tape_hash}`.\n",
        encoding="utf-8",
    )
    (diag / "P2_9_BAD_SEED_REGISTER.md").write_text(
        "# P2.9 bad-seed register\n\n"
        "All ten frozen trajectories are retained; no seed replacement, rerun, or best-checkpoint promotion occurred.\n",
        encoding="utf-8",
    )
    (diag / "P2_9_FINAL_VERDICT.md").write_text(f"# P2.9 final verdict\n\n`{verdict}`\n\n```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    (diag / "P2_9_GATE_DECISION.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("q0", "train", "evaluate", "aggregate"))
    parser.add_argument("--output-root", default="results/development/redundant_topology_uav_p2_9")
    parser.add_argument("--arm")
    parser.add_argument("--seed", type=int, default=SEEDS[0])
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"protocol": PROTOCOL, "mode": args.mode, "execute_required": True, "cloud_only": True}, indent=2)); return
    configure_core()
    out = Path(args.output_root); out.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.mode == "q0": q0(out, args.seed, device)
    elif args.mode == "train": core.train(out, args.arm, args.seed, device)
    elif args.mode == "evaluate": core.evaluate(out, args.arm, args.seed, device)
    else: aggregate(out)


if __name__ == "__main__":
    main()
