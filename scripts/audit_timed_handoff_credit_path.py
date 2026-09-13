"""Read-only reward-path audit for the staged 3DOF handoff task.

This audit follows the two legal G0 controllers and records the reward that a
successful physical route actually exposes.  It does not train or alter an
environment.  Its purpose is to distinguish a task that is physically
reachable but credit-sparse from one whose successful route has observable,
task-aligned intermediate feedback.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS, TimedHandoffIntercept3DConfig, TimedHandoffIntercept3DEnv
from scripts.audit_timed_handoff_intercept_3d_g0 import MODES, SEEDS, mode_actions


PROTOCOL = "TIMED-HANDOFF-3D-CREDIT-PATH-AUDIT-V1"


def make_env(seed: int, context: str) -> TimedHandoffIntercept3DEnv:
    return TimedHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context=context,
            authorization_start_step=12,
            authorization_deadline=28,
            branch_step=40,
            authorization_hold_steps=8,
            refresh_hold_steps=8,
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=1_500.0,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=0,
            max_target_message_age_steps=10,
            target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild",
            max_steps=260,
        )
    )


def trace(seed: int, context: str, mode: str) -> dict[str, object]:
    env = make_env(seed, context)
    obs, _, _ = env.reset()
    totals = {"mean_return": 0.0, "base_return": 0.0, "route_shaping": 0.0, "relay_track_rate": 0.0, "route_score": 0.0}
    info: dict[str, object] = {}
    steps = 0
    for _ in range(env.config.max_steps):
        obs, _, _, rewards, dones, info = env.step(mode_actions(obs, mode))
        shaping = float(info["handoff_service_shaping_reward"])
        mean_reward = float(np.mean(rewards))
        totals["mean_return"] += mean_reward
        # The wrapper adds a common shaping term after the base environment's
        # role-specific rewards, so this subtraction is exact except for the
        # terminal completion bonus, which deliberately remains in base_return.
        totals["base_return"] += mean_reward - shaping
        totals["route_shaping"] += shaping
        totals["relay_track_rate"] += float(env._relay_mediated_fresh_attacker_track())
        totals["route_score"] += float(info["handoff_service_progress"])
        steps += 1
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed,
        "context": context,
        "mode": mode,
        "steps": steps,
        "success": float(info.get("handoff_success", 0.0)),
        "timeout": float(info.get("timeout", 0.0)),
        **totals,
        "mean_relay_track_rate": totals["relay_track_rate"] / max(steps, 1),
        "mean_route_score": totals["route_score"] / max(steps, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    rows = [trace(seed, context, mode) for context in HANDOFF_CONTEXTS for seed in SEEDS for mode in MODES]
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "credit_path_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for context in HANDOFF_CONTEXTS:
        summary[context] = {}
        for mode in MODES:
            cell = [row for row in rows if row["context"] == context and row["mode"] == mode]
            summary[context][mode] = {key: float(np.mean([row[key] for row in cell])) for key in ("success", "mean_return", "base_return", "route_shaping", "mean_relay_track_rate", "mean_route_score")}
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_READONLY_CREDIT_PATH_AUDIT",
        "training_started": False,
        "summary": summary,
        "interpretation": "This audit measures reward availability along legal scripted routes. It does not establish learnability or a method effect.",
    }
    (args.out_dir / "credit_path_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
