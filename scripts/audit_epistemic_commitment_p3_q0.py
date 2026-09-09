"""Zero-training Q0 audit for the P3 epistemic-commitment task.

The audit uses scripted actions only.  It establishes task reachability,
information boundaries, trajectory-derived outcome diversity, live safety
telemetry, and exact runtime restoration; it is not a performance experiment.
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.epistemic_commitment_p3_env import (
    MODE_COMMIT,
    MODE_DEFER,
    MODE_FALLBACK,
    EpistemicCommitmentP3Env,
    P3CommunicationSpec,
)


CONTRACT = ROOT / "configs" / "epistemic_commitment_p3_task_contract_20260909.json"


def _spec(cell: str) -> P3CommunicationSpec:
    plan, ack, freshness = cell.split("|")
    return P3CommunicationSpec(plan, ack, freshness)


def _actions(modes: Iterable[int]) -> np.ndarray:
    value = np.zeros((3, 3), dtype=np.float32)
    value[:, 0] = np.asarray(tuple(modes), dtype=np.float32)
    return value


DEFER = _actions((MODE_DEFER,) * 3)
COMMIT = _actions((MODE_COMMIT,) * 3)
FALLBACK = _actions((MODE_FALLBACK,) * 3)
UNILATERAL = _actions((MODE_COMMIT, MODE_DEFER, MODE_FALLBACK))


def _run(spec: P3CommunicationSpec, schedule: list[np.ndarray], seed: int = 20260909):
    env = EpistemicCommitmentP3Env(spec, seed=seed)
    final_info: dict[str, Any] = {}
    for action in schedule:
        *_, final_info = env.step(action)
        if env.done:
            break
    return env, final_info


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        return bool(np.array_equal(np.asarray(left), np.asarray(right)))
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _communication_reachability(cells: list[str]) -> tuple[bool, dict[str, dict[str, Any]]]:
    rows: dict[str, dict[str, Any]] = {}
    passed = True
    for cell in cells:
        spec = _spec(cell)
        env, _ = _run(spec, [DEFER] * 5)
        expected_plan_epoch = {"delivered": 2, "lost": -1, "delayed": 4}[spec.plan_delivery]
        expected_ack_epoch = 3 if spec.ack_delivery == "delivered" else -1
        expected_version = -1 if spec.plan_delivery == "lost" else (1 if spec.plan_freshness == "current" else 0)
        cell_pass = (
            env.plan_receipt_epoch == expected_plan_epoch
            and env.ack_receipt_epoch == expected_ack_epoch
            and env.follower_plan_version == expected_version
        )
        passed = passed and cell_pass
        rows[cell] = {
            "plan_receipt_epoch": env.plan_receipt_epoch,
            "ack_receipt_epoch": env.ack_receipt_epoch,
            "locally_received_plan_version": env.follower_plan_version,
            "pass": cell_pass,
        }
    return passed, rows


def _privacy_relations() -> tuple[bool, dict[str, bool]]:
    delivered = EpistemicCommitmentP3Env(P3CommunicationSpec("delivered", "delivered", "current"))
    ack_lost = EpistemicCommitmentP3Env(P3CommunicationSpec("delivered", "lost", "current"))
    plan_lost = EpistemicCommitmentP3Env(P3CommunicationSpec("lost", "not_applicable", "current"))
    initial = [env.reset()[0] for env in (delivered, ack_lost, plan_lost)]
    initial_actor_equal = np.array_equal(initial[0], initial[1]) and np.array_equal(initial[1], initial[2])
    relay_private_zero = all(np.count_nonzero(obs[1, 34 + 3 : 34 + 8]) == 0 for obs in initial)

    observations = []
    for env in (delivered, ack_lost, plan_lost):
        obs = None
        for _ in range(3):
            obs, *_ = env.step(DEFER)
        observations.append(obs)
    leader_pre_ack_equal = np.array_equal(observations[0][0], observations[2][0])
    follower_receipt_private = not np.array_equal(observations[0][2], observations[2][2])
    relay_message_blind = np.array_equal(observations[0][1], observations[2][1])

    obs_delivered, *_ = delivered.step(DEFER)
    obs_ack_lost, *_ = ack_lost.step(DEFER)
    leader_ack_private = not np.array_equal(obs_delivered[0], obs_ack_lost[0])
    relations = {
        "initial_actor_observations_equal_under_hidden_truth": initial_actor_equal,
        "leader_cannot_observe_plan_delivery_before_ack": leader_pre_ack_equal,
        "follower_observes_only_local_plan_receipt": follower_receipt_private,
        "leader_observes_only_local_ack_receipt": leader_ack_private,
        "relay_does_not_receive_plan_or_ack_truth": relay_message_blind,
        "relay_private_vector_contains_only_public_time_context_and_own_mode": relay_private_zero,
    }
    return all(relations.values()), relations


def _runtime_restore() -> bool:
    spec = P3CommunicationSpec("delivered", "delivered", "current")
    original = EpistemicCommitmentP3Env(spec)
    for action in (DEFER, COMMIT, COMMIT):
        original.step(action)
    state = deepcopy(original.state_dict())
    expected = [original.step(action) for action in (COMMIT, FALLBACK)]
    restored = EpistemicCommitmentP3Env(spec)
    restored.load_state_dict(state)
    actual = [restored.step(action) for action in (COMMIT, FALLBACK)]
    return _same(expected, actual) and _same(original.state_dict(), restored.state_dict())


def audit() -> dict[str, Any]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    cells = contract["frozen_training_cells"] + contract["heldout_compositional_cells"]
    reachable, reachability = _communication_reachability(cells)
    privacy, privacy_detail = _privacy_relations()

    nominal = P3CommunicationSpec("delivered", "delivered", "current")
    lost = P3CommunicationSpec("lost", "not_applicable", "current")
    safe_env, safe = _run(nominal, [COMMIT] * 8)
    failure_env, failure = _run(lost, [UNILATERAL] * 8)
    recovery_env, recovery = _run(lost, [UNILATERAL] * 2 + [FALLBACK] * 6)

    guidance_env = EpistemicCommitmentP3Env(nominal)
    checkpoint = guidance_env.state_dict()
    guidance_positions = []
    for action in (COMMIT, DEFER, FALLBACK):
        branch = EpistemicCommitmentP3Env(nominal)
        branch.load_state_dict(checkpoint)
        branch.step(action)
        guidance_positions.append(branch.base.blue_pos.copy())
    mode_changes_trajectory = len({value.tobytes() for value in guidance_positions}) == 3

    constant_values: dict[str, list[float]] = {"commit": [], "defer": [], "fallback": []}
    scripted_values: list[float] = []
    for cell in cells:
        spec = _spec(cell)
        for name, action in (("commit", COMMIT), ("defer", DEFER), ("fallback", FALLBACK)):
            _, info = _run(spec, [action] * 8)
            constant_values[name].append(float(info["task_value"]))
        is_current_receipt = spec.plan_freshness == "current" and spec.plan_delivery != "lost"
        _, info = _run(spec, [COMMIT] * 8 if is_current_receipt else [FALLBACK] * 8)
        scripted_values.append(float(info["task_value"]))
    constant_means = {key: float(np.mean(value)) for key, value in constant_values.items()}
    scripted_mean = float(np.mean(scripted_values))
    constant_modes_do_not_dominate = scripted_mean > max(constant_means.values())

    same_condition_values = []
    for action in (COMMIT, DEFER, FALLBACK, UNILATERAL):
        _, info = _run(nominal, [action] * 8)
        same_condition_values.append(float(info["task_value"]))
    nominal_not_saturated = len(set(same_condition_values)) >= 3

    collision_env = EpistemicCommitmentP3Env(lost)
    collision_env.base.blue_pos[collision_env.follower_id] = collision_env.base.blue_pos[
        collision_env.leader_id
    ].copy()
    collision_env.base._update_sensing_and_comm()
    *_, collision_info = collision_env.step(DEFER)
    constraint_env = EpistemicCommitmentP3Env(lost)
    constraint_env.base.blue_pos[constraint_env.leader_id, 2] = 900.0
    constraint_env.base._update_sensing_and_comm()
    *_, constraint_info = constraint_env.step(DEFER)

    checks = {
        "all_communication_cells_reachable": reachable,
        "private_observation_relations_exact": privacy,
        "at_least_four_decision_epochs_before_termination": safe_env.epoch == 8,
        "mode_changes_alter_closed_loop_guidance": mode_changes_trajectory,
        "unilateral_entry_emerges_from_trajectory": bool(failure["unilateral_risk_observed"]),
        "scripted_safe_success_exists": safe.get("endpoint") == "joint_task_success",
        "scripted_unilateral_failure_exists": failure.get("endpoint") == "unsupported_corridor_entry",
        "scripted_recovery_exists": recovery.get("endpoint") == "recovery_after_mismatch",
        "constant_modes_do_not_dominate": constant_modes_do_not_dominate,
        "nominal_not_saturated": nominal_not_saturated,
        "collision_and_constraint_telemetry_live": collision_info.get("endpoint") == "collision"
        and constraint_info.get("endpoint") == "constraint_violation",
        "runtime_restore_exact": _runtime_restore(),
    }
    required = contract["q0_required_checks"]
    exact_check_registry = list(checks) == required
    passed = exact_check_registry and all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P3-Q0-ZERO-TRAINING-AUDIT-V1",
        "verdict": "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT" if passed else "P3_Q0_STOP",
        "checks": checks,
        "exact_check_registry": exact_check_registry,
        "communication_reachability": reachability,
        "privacy_relations": privacy_detail,
        "scripted_endpoints": {
            "safe": safe,
            "unilateral_failure": failure,
            "recovery": recovery,
        },
        "constant_mode_mean_task_value": constant_means,
        "scripted_oracle_feasibility_mean_task_value": scripted_mean,
        "training_started": False,
        "ppo_updates": 0,
        "next_authorized_action": "build a bounded tiny learnability pilot; no submission experiment",
        "evidence_boundary": (
            "Scripted Q0 trajectories establish reachability, non-degeneracy, information privacy, "
            "trajectory-derived endpoints, live telemetry, and exact restoration. They do not show "
            "that any learned policy can solve the task or that the proposed method is superior."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if report["verdict"] != "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
