"""Method-independent N1 timing and reachability calibration.

This is not a policy baseline.  ``scripted_oracle`` is allowed true simulator
state solely to establish physical reachability; ``random_no_commit`` is a
deliberately non-completing control.  Neither controller is an actor contract
or a result for a future learning method.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    ACTION3D_TABLE,
    FLIGHT_ACTION_DIM,
    ROLE_ATTACKER,
    ROLE_INTERCEPTOR,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
    angle_diff,
    velocity_from_state,
)

OUTCOMES = ("NEUTRALIZED", "COLLISION", "CONSTRAINT_FAILURE", "TARGET_ESCAPE", "TIMEOUT")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run N1 non-learning mission timing calibration.")
    parser.add_argument("--episodes", type=int, default=48)
    parser.add_argument("--base-seed", type=int, default=610_000)
    parser.add_argument("--max-steps", type=int, default=360)
    parser.add_argument("--target-escape-radius", type=float, default=35_000.0)
    parser.add_argument("--target-policy", choices=("straight", "evasive"), default="evasive")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "new_project_n1_timing_calibration")
    return parser.parse_args()


def _signed_command(value: float, deadband: float) -> float:
    return 1.0 if value > deadband else (-1.0 if value < -deadband else 0.0)


def _flight_action(env: UAVIntercept3DEnv, agent_id: int, desired_pos: np.ndarray, desired_speed: float) -> int:
    typ = env.config.blue_types[agent_id]
    rel = desired_pos - env.blue_pos[agent_id]
    desired_heading = math.atan2(float(rel[1]), float(rel[0]))
    heading_error = angle_diff(desired_heading, float(env.blue_heading[agent_id]))
    desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2])) + 1e-6)
    command = np.asarray(
        [
            _signed_command(heading_error, 0.18 * typ.max_turn_rate),
            _signed_command(desired_gamma - float(env.blue_gamma[agent_id]), 0.20 * typ.max_gamma),
            _signed_command(float(desired_speed) - float(env.blue_speed[agent_id]), 4.0),
        ],
        dtype=np.float32,
    )
    return int(np.argmin(np.linalg.norm(ACTION3D_TABLE - command[None, :], axis=1)))


def scripted_oracle_actions(env: UAVIntercept3DEnv) -> np.ndarray:
    """True-state scripted controller used only to establish task reachability."""
    red_pos = env.red_pos[0]
    red_vel = velocity_from_state(float(env.red_speed[0]), float(env.red_heading[0]), float(env.red_gamma[0]))
    red_dir = red_vel / max(float(np.linalg.norm(red_vel)), 1e-6)
    actions = np.zeros(env.config.num_blue, dtype=np.int64)
    for i, typ in enumerate(env.config.blue_types):
        rel = red_pos - env.blue_pos[i]
        distance = float(np.linalg.norm(rel))
        lead_time = float(np.clip(distance / max(float(env.blue_speed[i]), 1.0), 6.0, 36.0))
        if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
            # Track a true kinematic standoff point rather than the target's
            # centre, then commit only once the evaluator envelope is legal.
            desired_pos = red_pos + red_vel * lead_time - red_dir * 3_200.0
            desired_speed = typ.max_speed if distance > 5_200.0 else min(typ.max_speed, float(env.red_speed[0]) + 18.0)
            flight_action = _flight_action(env, i, desired_pos.astype(np.float32), desired_speed)
            if env._in_true_standoff_envelope(i, typ):
                flight_action += FLIGHT_ACTION_DIM
            actions[i] = flight_action
        else:
            desired_pos = red_pos + red_vel * lead_time
            actions[i] = _flight_action(env, i, desired_pos.astype(np.float32), typ.max_speed)
    return actions


def _outcome(info: dict[str, float]) -> str:
    if info["collision"] > 0.5:
        return "COLLISION"
    if info["constraint_violation"] > 0.5:
        return "CONSTRAINT_FAILURE"
    if info["target_neutralized"] > 0.5:
        return "NEUTRALIZED"
    if info["target_escape"] > 0.5:
        return "TARGET_ESCAPE"
    return "TIMEOUT"


def run_episode(args: argparse.Namespace, controller: str, episode: int) -> dict[str, int | float | str]:
    seed = args.base_seed + episode
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            mission_neutralization_enabled=True,
            engage_commit_hold_steps=4,
            target_escape_radius=args.target_escape_radius,
            target_policy=args.target_policy,
            max_steps=args.max_steps,
            seed=seed,
        )
    )
    env.reset()
    rng = np.random.default_rng(seed + 90_001)
    while True:
        actions = (
            scripted_oracle_actions(env)
            if controller == "scripted_oracle"
            else rng.integers(0, FLIGHT_ACTION_DIM, size=env.config.num_blue, dtype=np.int64)
        )
        _obs, _share, _graph, _reward, dones, info = env.step(actions)
        if bool(np.all(dones)):
            return {
                "controller": controller,
                "episode": episode,
                "seed": seed,
                "outcome": _outcome(info),
                "event_step": int(info["step"]),
                "neutralized": int(info["target_neutralized"] > 0.5),
                "collision": int(info["collision"] > 0.5),
                "constraint_failure": int(info["constraint_violation"] > 0.5),
                "target_escape": int(info["target_escape"] > 0.5),
                "timeout": int(info["timeout"] > 0.5),
            }


def _write_csv(path: Path, rows: list[dict[str, int | float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _summary(rows: list[dict[str, int | float | str]]) -> list[dict[str, int | float | str]]:
    summary = []
    for controller in ("scripted_oracle", "random_no_commit"):
        group = [row for row in rows if row["controller"] == controller]
        neutralized = [int(row["event_step"]) for row in group if row["outcome"] == "NEUTRALIZED"]
        item: dict[str, int | float | str] = {"controller": controller, "episodes": len(group)}
        for outcome in OUTCOMES:
            item[f"{outcome.lower()}_rate"] = float(np.mean([row["outcome"] == outcome for row in group]))
        item["neutralization_time_min"] = min(neutralized) if neutralized else -1
        item["neutralization_time_median"] = float(np.median(neutralized)) if neutralized else -1.0
        item["neutralization_time_p90"] = float(np.quantile(neutralized, 0.90)) if neutralized else -1.0
        summary.append(item)
    return summary


def main() -> None:
    args = parse_args()
    if args.episodes < 1 or args.max_steps < 4:
        raise ValueError("episodes must be positive and max-steps must be at least four")
    rows = [
        run_episode(args, controller, episode)
        for controller in ("scripted_oracle", "random_no_commit")
        for episode in range(args.episodes)
    ]
    summary = _summary(rows)
    episodes_path = args.output_dir / "episode_outcomes.csv"
    summary_path = args.output_dir / "summary.csv"
    _write_csv(episodes_path, rows)
    _write_csv(summary_path, summary)
    print(f"N1_TIMING_CALIBRATION_COMPLETE: {episodes_path}")
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
