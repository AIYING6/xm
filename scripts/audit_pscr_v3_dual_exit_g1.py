"""Zero-training G1 audit for PSCR-v3 dual-exit interception.

This script is deliberately not a learner benchmark.  It checks whether the
new physical task produces non-identical outcome regions for three transparent
primitive-flight controllers before a method or a training budget is proposed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_v3_dual_exit_interception_env import PSCRV3Config, PSCRV3DualExitInterceptionEnv


POLICIES = ("concentrate", "split", "defer")


def waypoint_action(env: PSCRV3DualExitInterceptionEnv, agent: int, waypoint: np.ndarray) -> int:
    position = env.base.blue_pos[agent]
    delta = waypoint - position
    horizontal = float(np.linalg.norm(delta[:2]))
    desired = float(env.base.blue_heading[agent]) if horizontal < 1.0 else math.atan2(float(delta[1]), float(delta[0]))
    error = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(error)) if abs(error) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)  # max acceleration


def primitive_policy(env: PSCRV3DualExitInterceptionEnv, name: str) -> np.ndarray:
    red = env.base.red_pos[0].copy()
    left, right = env._egress_position(-1), env._egress_position(+1)
    if name == "concentrate":
        goals = (red, red, red)
    elif name == "split":
        # A fixed two-exit hedge: scout/relay cover opposite lanes and the
        # attacker remains on the approach line.  No privileged exit label.
        goals = (left, right, red)
    elif name == "defer":
        if env.exit_choice is None:
            goals = (red, red, red)
        else:
            chosen = env._egress_position(env.exit_choice)
            goals = (chosen, chosen, chosen)
    else:
        raise ValueError(name)
    return np.asarray([waypoint_action(env, i, np.asarray(goal, dtype=np.float32)) for i, goal in enumerate(goals)], dtype=np.int64)


def run_one(seed: int, policy: str) -> dict[str, object]:
    env = PSCRV3DualExitInterceptionEnv(PSCRV3Config(seed=seed))
    env.reset()
    total_return = 0.0
    info: dict[str, object] = {}
    for _ in range(env.config.horizon):
        _, _, _, rewards, dones, info = env.step(primitive_policy(env, policy))
        total_return += float(np.mean(rewards))
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed,
        "policy": policy,
        "return": total_return,
        "steps": env.base.step_count,
        "success": int(float(info.get("success", 0.0)) > 0.5),
        "escape": int(float(info.get("evader_escape", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "exit_choice": int(float(info.get("exit_choice", 0.0))),
        "coverage_negative": float(info.get("branch_coverage_negative", float("nan"))),
        "coverage_positive": float(info.get("branch_coverage_positive", float("nan"))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=96101)
    parser.add_argument("--seeds", type=int, default=18)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing dry run: pass --execute for this zero-training audit")
    output = args.output_root
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    rows = [run_one(args.seed_start + offset, policy) for offset in range(args.seeds) for policy in POLICIES]
    with (output / "PSCR_V3_G1_CONTROLLER_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    winners: dict[int, list[str]] = {}
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        subset = [row for row in rows if row["seed"] == seed]
        # The physical terminal objective ranks above shaped return.  An
        # escaping evader must never be declared the better controller merely
        # because it accumulated dense pursuit shaping for longer.  Return is
        # only a tie-breaker among identical terminal outcomes.
        def rank(row: dict[str, object]) -> tuple[int, int, float]:
            return (int(row["success"]), -int(row["escape"]), float(row["return"]))
        best_rank = max(rank(row) for row in subset)
        winners[seed] = [str(row["policy"]) for row in subset if rank(row) == best_rank]
    win_counts = {policy: sum(policy in winners[seed] for seed in winners) for policy in POLICIES}
    # A pass requires at least two controllers to win at least one realisation
    # and neither universal success nor universal escape.  It is an
    # identifiability screen, not an estimate of a learning algorithm's value.
    success_total = sum(int(row["success"]) for row in rows)
    escape_total = sum(int(row["escape"]) for row in rows)
    verdict = "PSCR_V3_G1_NONDEGENERATE_SIGNAL" if sum(count > 0 for count in win_counts.values()) >= 2 and 0 < success_total < len(rows) and 0 < escape_total < len(rows) else "PSCR_V3_G1_SIGNAL_NOT_ESTABLISHED"
    report = {
        "protocol": "PSCR-V3-DUAL-EXIT-G1-V1",
        "verdict": verdict,
        "diagnostic_only": True,
        "training_started": False,
        "evaluation_started": False,
        "seeds": list(range(args.seed_start, args.seed_start + args.seeds)),
        "controllers": list(POLICIES),
        "controller_win_counts": win_counts,
        "success_rows": success_total,
        "escape_rows": escape_total,
        "interpretation": "Transparent controllers establish only whether physical action choices are non-degenerate; they do not validate a method or provide paper performance evidence.",
    }
    (output / "PSCR_V3_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
