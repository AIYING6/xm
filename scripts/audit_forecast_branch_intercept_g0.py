"""Legal-controller G0 calibration for forecast-branch 3DOF interception."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audit_intercept_3d_legal_baseline import legal_actions
from envs.forecast_branch_intercept_3d_env import ForecastBranchIntercept3DConfig, ForecastBranchIntercept3DEnv

SEEDS = (3301, 3302, 3303)
EPISODES = 16
CONTEXTS = {"reliable_right": 0.9, "ambiguous": 0.5, "reliable_left": 0.1}
CONTROLLERS = ("track", "forecast_commit")
OUT = ROOT / "results" / "development" / "forecast_branch_intercept_g0"


def actions(obs: np.ndarray, step: int, controller: str, branch_step: int) -> np.ndarray:
    """Use local emitted observation plus retained initial public advisory only."""
    planned = obs.copy()
    if controller == "forecast_commit" and step < branch_step:
        probability = float(obs[0, -2]) if step == 0 else 0.5
        # At later steps the actor would retain its initial two-value history;
        # this controller keeps that history explicitly rather than reading env.
        raise RuntimeError("forecast_commit requires retained advisory")
    return legal_actions(planned)


def run_one(context: str, controller: str, seed: int, episode: int) -> dict[str, object]:
    cfg = ForecastBranchIntercept3DConfig(
        seed=600_000 + 10_000 * list(CONTEXTS).index(context) + 1_000 * list(CONTROLLERS).index(controller) + 100 * (seed - SEEDS[0]) + episode,
        forecast_right_probability=CONTEXTS[context],
        branch_step=52,
        branch_turn_radians=0.62,
        communication_dropout_prob=0.25,
        radar_dropout_prob=0.15,
        message_delay_steps=4,
        max_steps=260,
    )
    env = ForecastBranchIntercept3DEnv(cfg)
    obs, _, _ = env.reset()
    advisory = float(obs[0, -2])
    total_reward = 0.0
    while True:
        planned = obs.copy()
        if controller == "forecast_commit" and env.step_count < cfg.branch_step and abs(advisory - 0.5) >= 0.30:
            # ``rel_y`` is a legal local target-relative coordinate.  The
            # signed shift is a fixed public kinematic anticipation rule, not
            # a read of future branch identity or target state.
            anticipated_right = advisory > 0.5
            planned[:, 9] += -0.16 if anticipated_right else 0.16
        action = legal_actions(planned)
        obs, _, _, reward, dones, info = env.step(action)
        total_reward += float(np.mean(reward))
        if bool(np.all(dones)):
            return {
                "context": context,
                "controller": controller,
                "seed": seed,
                "episode": episode,
                "success": int(info["success"]),
                "timeout": int(info["timeout"]),
                "collision": int(info["collision"]),
                "constraint_violation": int(info["constraint_violation"]),
                "reward_sum": total_reward,
                "steps": int(info["step"]),
                "physical_branch_right": int(info["branch_right_telemetry"]),
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("G0 requires --execute")
    if (args.out_dir / "raw_episode_metrics.csv").exists():
        raise FileExistsError(f"Refusing to overwrite {args.out_dir}")
    rows = [run_one(context, controller, seed, episode) for context in CONTEXTS for controller in CONTROLLERS for seed in SEEDS for episode in range(EPISODES)]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "raw_episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for context in CONTEXTS:
        for controller in CONTROLLERS:
            cell = [row for row in rows if row["context"] == context and row["controller"] == controller]
            summary.append({
                "context": context, "controller": controller, "episodes": len(cell),
                "success_rate": float(np.mean([row["success"] for row in cell])),
                "collision_rate": float(np.mean([row["collision"] for row in cell])),
                "mean_reward": float(np.mean([row["reward_sum"] for row in cell])),
            })
    with (args.out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    by = {(row["context"], row["controller"]): row for row in summary}
    aligned_gain = by[("reliable_right", "forecast_commit")]["success_rate"] - by[("reliable_right", "track")]["success_rate"]
    ambiguous_gain = by[("ambiguous", "forecast_commit")]["success_rate"] - by[("ambiguous", "track")]["success_rate"]
    payload = {
        "protocol": "FORECAST-BRANCH-INTERCEPT-G0-V1",
        "artifact_class": "DEVELOPMENT_ONLY_LEGAL_CONTROLLER_CALIBRATION",
        "legal_actor_information_only": True,
        "training_started": False,
        "canonical_data_used": False,
        "reliable_right_anticipation_success_gain": aligned_gain,
        "ambiguous_anticipation_success_gain": ambiguous_gain,
        "verdict": "EVIDENCE_REVIEW_REQUIRED",
    }
    (args.out_dir / "manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
