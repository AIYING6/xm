"""Ground the P3B recovery choices in legal 3DOF behavior without training."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
    TRAINABLE_FAILURE_HYPOTHESES,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, angle_diff


def _legal_pursuit_action(env: ActiveDiagnosisTrainableUAVEnv, agent: int) -> int:
    """Use only the target-relative vector already present in legal actor obs."""
    obs = env.base._get_obs()[agent]
    rel = np.asarray(
        [
            obs[8] * env.base.config.world_radius,
            obs[9] * env.base.config.world_radius,
            obs[10] * env.base.config.max_altitude,
        ],
        dtype=np.float32,
    )
    desired = math.atan2(float(rel[1]), float(rel[0]))
    turn = float(np.sign(angle_diff(desired, float(env.base.blue_heading[agent]))))
    climb = float(np.sign(float(rel[2]))) if abs(float(rel[2])) > 100.0 else 0.0
    score = (
        np.abs(ACTION3D_TABLE[:, 0] - turn)
        + np.abs(ACTION3D_TABLE[:, 1] - climb)
        + 0.1 * np.abs(ACTION3D_TABLE[:, 2] - 1.0)
    )
    return int(np.argmin(score))


def _run(hypothesis: str, plan: str, seed: int) -> dict:
    env = ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(hypothesis, seed))
    env.reset()
    total = 0.0
    while not env.done:
        actions = np.full(env.num_agents, env.neutral_action, dtype=np.int64)
        if plan == "immediate_fallback":
            if env.fallback_count == 0 or env.fallback_remaining > 0:
                actions[env.attacker_id] = env.fallback_action
        elif plan == "probe_then_condition":
            if env.probe_count == 0 or env.probe_remaining > 0:
                actions[env.relay_id] = env.probe_action
            elif env.probe_ack_state < 0.0 and (
                env.fallback_count == 0 or env.fallback_remaining > 0
            ):
                actions[env.attacker_id] = env.fallback_action
            elif env.base._has_target_information(env.attacker_id):
                actions[env.attacker_id] = _legal_pursuit_action(env, env.attacker_id)
        else:
            raise ValueError(plan)
        _, _, graph, reward, done, info = env.step(actions)
        if not np.all(graph["action_masks"].sum(axis=1) >= 1):
            raise AssertionError("an agent lost every legal action")
        total += float(reward[0, 0])
        if bool(done.all()):
            break
    return {
        "hypothesis": hypothesis,
        "plan": plan,
        "return": total,
        "steps": env.step_count,
        "success": float(info["success"]),
        "timeout": float(info["timeout"]),
        "collision": float(info["collision"]),
        "constraint_violation": float(info["constraint_violation"]),
        "probe_count": env.probe_count,
        "fallback_count": env.fallback_count,
        "probe_ack_state": env.probe_ack_state,
    }


def run_grounding_audit(seed: int = 123) -> dict:
    rows = [
        _run(hypothesis, plan, seed)
        for hypothesis in TRAINABLE_FAILURE_HYPOTHESES
        for plan in ("immediate_fallback", "probe_then_condition")
    ]
    lookup = {(row["hypothesis"], row["plan"]): row for row in rows}
    fallback = [lookup[(h, "immediate_fallback")] for h in TRAINABLE_FAILURE_HYPOTHESES]
    conditional = [lookup[(h, "probe_then_condition")] for h in TRAINABLE_FAILURE_HYPOTHESES]
    balanced_gain = float(np.mean([r["return"] for r in conditional]) - np.mean([r["return"] for r in fallback]))
    checks = {
        "all_recovery_plans_complete_task": all(row["success"] == 1.0 for row in rows),
        "no_recovery_plan_timeout": all(row["timeout"] == 0.0 for row in rows),
        "no_collision_or_constraint_failure": all(
            row["collision"] == 0.0 and row["constraint_violation"] == 0.0 for row in rows
        ),
        "probe_ack_separates_modes": (
            lookup[(RECOVERABLE_RANGE_LOSS, "probe_then_condition")]["probe_ack_state"] == 1.0
            and lookup[(HARD_TERMINAL_COMM_FAILURE, "probe_then_condition")]["probe_ack_state"] == -1.0
        ),
        "conditional_plan_uses_distinct_recovery": (
            lookup[(RECOVERABLE_RANGE_LOSS, "probe_then_condition")]["fallback_count"] == 0
            and lookup[(HARD_TERMINAL_COMM_FAILURE, "probe_then_condition")]["fallback_count"] == 1
        ),
        "balanced_prior_probe_has_positive_net_task_value": balanced_gain > 0.0,
    }
    passed = all(checks.values())
    return {
        "protocol": "ACTIVE-DIAGNOSIS-P3B-RECOVERY-GROUNDING-V1",
        "verdict": "P3B_RECOVERY_GROUNDING_PASS" if passed else "P3B_RECOVERY_GROUNDING_FAIL",
        "checks": checks,
        "balanced_prior_return_gain": balanced_gain,
        "probe_cost_in_environment_reward": ActiveDiagnosisTrainableConfig().probe_utility_cost,
        "trajectories": rows,
        "environment_steps": int(sum(row["steps"] for row in rows)),
        "training_started": False,
        "performance_pilot_authorized": False,
        "automatic_continuation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_grounding_audit()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

