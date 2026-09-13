"""Zero-training decision-switch audit for the staged-handoff environment."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import (
    HANDOFF_BEACON_SLICE,
    HANDOFF_CONTEXTS,
    HANDOFF_SERVICE_BEACON_SLICE,
    TimedHandoffIntercept3DConfig,
    TimedHandoffIntercept3DEnv,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, angle_diff
from scripts.audit_intercept_3d_legal_baseline import legal_actions


PROTOCOL = "TIMED-HANDOFF-INTERCEPT-3D-G0-V1"
SEEDS = (71201, 71202, 71203, 71204, 71205, 71206)
MODES = ("relay_hold_current_bridge", "relay_follow_delivered_track")


def mode_actions(obs: np.ndarray, mode: str) -> np.ndarray:
    """Two primitive-action relay behaviours using only emitted observations."""
    choice = legal_actions(obs[:, :34])
    if mode == "relay_follow_delivered_track":
        # The public service context supplies the future corridor offset, but
        # not the future target branch.  The relay can therefore preposition
        # physically without reading target truth.
        desired = obs[1, HANDOFF_SERVICE_BEACON_SLICE][3:].copy()
        if np.linalg.norm(desired) > 0.0:
            heading = math.atan2(float(obs[1, 4]), float(obs[1, 5]))
            desired_heading = math.atan2(float(desired[1]), float(desired[0]))
            turn = np.clip(angle_diff(desired_heading, heading) / 0.030, -1.0, 1.0)
            gamma = math.atan2(float(obs[1, 6]), float(obs[1, 7]))
            desired_gamma = math.atan2(float(desired[2]), math.hypot(float(desired[0]), float(desired[1])) + 1e-6)
            climb = np.clip((desired_gamma - gamma) / 0.22, -1.0, 1.0)
            command = np.asarray((turn, climb, 0.0), dtype=np.float32)
            choice[1] = int(np.argmin(np.sum((ACTION3D_TABLE - command[None, :]) ** 2, axis=1)))
        return choice
    if mode != "relay_hold_current_bridge":
        raise ValueError(f"unsupported mode: {mode}")
    # The current service waypoint is a public mission command; no global
    # formation state or hidden target information is read.
    desired = obs[1, HANDOFF_SERVICE_BEACON_SLICE][:3].copy()
    if np.linalg.norm(desired) > 0.0:
        heading = math.atan2(float(obs[1, 4]), float(obs[1, 5]))
        desired_heading = math.atan2(float(desired[1]), float(desired[0]))
        turn = np.clip(angle_diff(desired_heading, heading) / 0.030, -1.0, 1.0)
        gamma = math.atan2(float(obs[1, 6]), float(obs[1, 7]))
        desired_gamma = math.atan2(float(desired[2]), math.hypot(float(desired[0]), float(desired[1])) + 1e-6)
        climb = np.clip((desired_gamma - gamma) / 0.22, -1.0, 1.0)
        command = np.asarray((turn, climb, 0.0), dtype=np.float32)
        choice[1] = int(np.argmin(np.sum((ACTION3D_TABLE - command[None, :]) ** 2, axis=1)))
    return choice


def run_episode(seed: int, context: str, mode: str) -> dict[str, object]:
    env = TimedHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context=context,
            # The early authorization window ends before a relay that heads
            # toward the announced later service corridor can return.  The
            # later refresh check is evaluated after the target branch.
            authorization_start_step=12,
            authorization_deadline=28,
            branch_step=40,
            authorization_hold_steps=8,
            refresh_hold_steps=8,
            # The original 3 km relocation reaches its service window only
            # when the independent chase controller is already collision-prone.
            # This 1.5 km alternate route remains physically distinct from
            # the 0.9 km current route, while allowing the staged service
            # choice to be evaluated before that downstream event.
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=1_500.0,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=0,
            max_target_message_age_steps=10,
            target_init_range_scale=0.65,
            # The G0 gate tests whether the staged relay decision is
            # meaningful.  Keep target motion learnable here; a harsher
            # post-stage evasion is a separate non-saturation question.
            postbranch_target_policy="weaving_mild",
            max_steps=260,
        )
    )
    obs, _, _ = env.reset()
    info: dict[str, object] = {}
    min_current_corridor_error = float("inf")
    min_future_corridor_error = float("inf")
    max_authorization_streak = 0
    max_refresh_streak = 0
    max_attacker_delivery_step = -1
    postbranch_relay_delivery_seen = 0
    for _ in range(env.config.max_steps):
        obs, _, _, _, dones, info = env.step(mode_actions(obs, mode))
        min_current_corridor_error = min(min_current_corridor_error, float(info["relay_current_corridor_error"]))
        min_future_corridor_error = min(min_future_corridor_error, float(info["relay_future_corridor_error"]))
        max_authorization_streak = max(max_authorization_streak, int(info["authorization_handoff_streak"]))
        max_refresh_streak = max(max_refresh_streak, int(info["postbranch_refresh_streak"]))
        max_attacker_delivery_step = max(max_attacker_delivery_step, int(env.target_cache_delivery_step[2]))
        if env.step_count >= env.handoff_config.branch_step and env._relay_mediated_fresh_attacker_track():
            postbranch_relay_delivery_seen = 1
        if bool(dones[0, 0]):
            break
    return {
        "seed": seed,
        "context": context,
        "mode": mode,
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "steps": int(float(info.get("step", 0.0))),
        "authorization_handoff_observed": int(float(info.get("authorization_handoff_observed", 0.0)) > 0.5),
        "postbranch_refresh_observed": int(float(info.get("postbranch_refresh_observed", 0.0)) > 0.5),
        "attacker_fresh_track": int(float(info.get("attacker_has_fresh_target_info", 0.0)) > 0.5),
        "min_current_corridor_error": min_current_corridor_error,
        "min_future_corridor_error": min_future_corridor_error,
        "max_authorization_streak": max_authorization_streak,
        "max_refresh_streak": max_refresh_streak,
        "max_attacker_delivery_step": max_attacker_delivery_step,
        "postbranch_relay_delivery_seen": postbranch_relay_delivery_seen,
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
    rows = [run_episode(seed, context, mode) for context in HANDOFF_CONTEXTS for seed in SEEDS for mode in MODES]
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "timed_handoff_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary: dict[str, dict[str, float]] = {}
    direction: list[int] = []
    for context in HANDOFF_CONTEXTS:
        cell = {mode: [row for row in rows if row["context"] == context and row["mode"] == mode] for mode in MODES}
        means = {mode: float(np.mean([row["success"] for row in values])) for mode, values in cell.items()}
        delta = means[MODES[1]] - means[MODES[0]]
        direction.append(int(np.sign(delta)))
        summary[context] = {
            "hold_success": means[MODES[0]],
            "follow_success": means[MODES[1]],
            "follow_minus_hold_success": delta,
            "hold_authorization_rate": float(np.mean([row["authorization_handoff_observed"] for row in cell[MODES[0]]])),
            "follow_authorization_rate": float(np.mean([row["authorization_handoff_observed"] for row in cell[MODES[1]]])),
            "hold_refresh_rate": float(np.mean([row["postbranch_refresh_observed"] for row in cell[MODES[0]]])),
            "follow_refresh_rate": float(np.mean([row["postbranch_refresh_observed"] for row in cell[MODES[1]]])),
        }
    reversal = len(set(direction)) > 1 and 0 not in direction
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_DECISION_SWITCH_AUDIT",
        "paper_evidence": False,
        "training_started": False,
        "contexts": list(HANDOFF_CONTEXTS),
        "modes": list(MODES),
        "summary": summary,
        "decision_preference_reversal_observed": reversal,
        "verdict": "G0_DECISION_SWITCH_PASS" if reversal else "G0_DECISION_SWITCH_NOT_YET_ESTABLISHED",
        "interpretation": "A pass verifies only a legal physical decision-switch task candidate. It does not support a learned-method claim.",
    }
    (args.out_dir / "timed_handoff_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
