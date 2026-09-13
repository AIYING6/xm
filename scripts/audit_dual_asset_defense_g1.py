"""Zero-training decision-conflict audit for dual-asset UAV defense."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.dual_asset_defense_env import DualAssetDefenseConfig, DualAssetDefenseEnv


POLICIES = ("concentrated_intercept", "split_defense", "delayed_response")
CONTEXTS = {
    "C0_centered": {},
    "C1_negative_approach": {"initial_red_y": -2600.0, "blue_init_rotation_deg": -18.0},
    "C2_positive_approach": {"initial_red_y": 2600.0, "blue_init_rotation_deg": 18.0},
    "C3_wide_formation": {"blue_init_spacing_scale": 1.25, "asset_lateral": 9000.0},
}


def waypoint_action(env: DualAssetDefenseEnv, agent: int, goal: np.ndarray) -> int:
    delta = np.asarray(goal, dtype=np.float32) - env.base.blue_pos[agent]
    horizontal = float(np.linalg.norm(delta[:2]))
    desired = float(env.base.blue_heading[agent]) if horizontal < 1.0 else math.atan2(float(delta[1]), float(delta[0]))
    error = math.atan2(math.sin(desired - float(env.base.blue_heading[agent])), math.cos(desired - float(env.base.blue_heading[agent])))
    turn = int(np.sign(error)) if abs(error) > 0.035 else 0
    climb = int(np.sign(float(delta[2]))) if abs(float(delta[2])) > 250.0 else 0
    return int((turn + 1) * 9 + (climb + 1) * 3 + 2)


def actions_for(env: DualAssetDefenseEnv, policy: str) -> np.ndarray:
    red = env.base.red_pos[0].copy()
    negative, positive = env._asset_position(-1), env._asset_position(1)
    if policy == "concentrated_intercept":
        goals = (red, red, red)
    elif policy == "split_defense":
        # One vehicle protects each asset while the high-speed attacker tracks
        # the approach.  This is intentionally a transparent physical rule.
        goals = (negative, positive, red)
    elif policy == "delayed_response":
        goals = (red, red, red) if env.exit_choice is None else (env._asset_position(env.exit_choice),) * 3
    else:
        raise ValueError(policy)
    return np.asarray([waypoint_action(env, i, goal) for i, goal in enumerate(goals)], dtype=np.int64)


def run_cell(seed: int, context: str, policy: str) -> dict[str, object]:
    env = DualAssetDefenseEnv(DualAssetDefenseConfig(seed=seed, **CONTEXTS[context]))
    env.reset()
    total_return = 0.0
    info: dict[str, float] = {}
    for _ in range(env.defense_config.horizon):
        _, _, _, rewards, dones, info = env.step(actions_for(env, policy))
        total_return += float(np.mean(rewards))
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed,
        "context": context,
        "policy": policy,
        "return": total_return,
        "steps": env.base.step_count,
        "defense_success": int(info.get("defense_success", 0.0) > 0.5),
        "asset_breach": int(info.get("asset_breach", 0.0) > 0.5),
        "timeout": int(info.get("timeout", 0.0) > 0.5),
        "collision": int(info.get("collision", 0.0) > 0.5),
        "attacked_asset": int(info.get("attacked_asset", 0.0)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=97101)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute: this script runs no learning but writes a diagnostic")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    args.output_root.mkdir(parents=True)
    rows = [run_cell(args.seed_start + offset, context, policy) for offset in range(args.seeds) for context in CONTEXTS for policy in POLICIES]
    with (args.output_root / "DUAL_ASSET_DEFENSE_G1_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    def rank(row: dict[str, object]) -> tuple[int, int, float]:
        return (int(row["defense_success"]), -int(row["asset_breach"]), float(row["return"]))
    winners: dict[tuple[int, str], list[str]] = {}
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        for context in CONTEXTS:
            cell = [row for row in rows if row["seed"] == seed and row["context"] == context]
            best = max(rank(row) for row in cell)
            winners[(seed, context)] = [str(row["policy"]) for row in cell if rank(row) == best]
    unique = {policy: sum(winners[cell] == [policy] for cell in winners) for policy in POLICIES}
    breached = sum(int(row["asset_breach"]) for row in rows)
    succeeded = sum(int(row["defense_success"]) for row in rows)
    verdict = "DUAL_ASSET_DEFENSE_G1_NONDEGENERATE_SIGNAL" if sum(value > 0 for value in unique.values()) >= 2 and max(unique.values()) < len(winners) and 0 < breached < len(rows) and 0 < succeeded < len(rows) else "DUAL_ASSET_DEFENSE_G1_SIGNAL_NOT_ESTABLISHED"
    report = {
        "protocol": "DUAL-ASSET-DEFENSE-G1-V1",
        "verdict": verdict,
        "diagnostic_only": True,
        "training_started": False,
        "contexts": list(CONTEXTS),
        "policies": list(POLICIES),
        "unique_terminal_objective_win_counts": unique,
        "defense_success_rows": succeeded,
        "asset_breach_rows": breached,
        "interpretation": "The audit asks only whether the physical task presents non-degenerate action trade-offs. It neither evaluates a learned policy nor establishes a paper result.",
    }
    (args.output_root / "DUAL_ASSET_DEFENSE_G1_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
