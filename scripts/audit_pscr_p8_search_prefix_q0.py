"""P8 zero-training physical witness for a search--localize--intercept prefix.

This audit uses the repository's unchanged 3DOF flight and communication
dynamics.  It compares two public pre-arrival team allocations: maintaining a
current service chain versus placing scout/relay in a forecast sector while an
executor continues the current service.  The future target's exact sector is
only instantiated inside counterfactual outcome branches and is never passed
to a pre-arrival controller.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_role_commitment_env import PSCRRoleCommitmentEnv


HORIZON, ARRIVAL, COMMIT = 160, 84, 36
# Absolute world coordinates: unlike a formation offset, these task locations
# must not be added to the initial UAV centroid (which would push altitude
# beyond the 3DOF flight envelope).
PRIMARY_POSITION = np.asarray((10_000.0, -3_000.0, 5_000.0), dtype=np.float32)
FORECAST_POSITION = np.asarray((11_000.0, 5_000.0, 5_000.0), dtype=np.float32)
LOCALIZATION_RADIUS = 4_000.0
EXECUTION_RADIUS = 4_800.0
SENSING_RADIUS = 9_000.0
HOLD_STEPS, MARGIN = 5, 0.05
X_OFFSETS = (-750.0, 0.0, 750.0)
URGENT_PROBABILITY = 0.55


def make_env(seed: int) -> PSCRRoleCommitmentEnv:
    env = PSCRRoleCommitmentEnv(PSCRConfig(seed=seed, horizon=HORIZON, future_arrival_step=ARRIVAL, commitment_start_step=COMMIT, commitment_lock_steps=ARRIVAL - COMMIT))
    env.reset()
    env.primary_position = PRIMARY_POSITION.copy()
    env._forecast_position = FORECAST_POSITION.copy()
    return env


def action_to_goals(env: PSCRRoleCommitmentEnv, mode: str, target: np.ndarray | None, localized: bool) -> list[np.ndarray]:
    if target is None:
        if mode == "stage":
            return [env._forecast_position, env._forecast_position, env.primary_position]
        return [env.primary_position] * env.num_agents
    if localized:
        return [target] * env.num_agents
    # Reactive search preserves the executor at current service.  The relay
    # follows the geometric midpoint needed to re-establish a legal chain.
    scout_goal = target
    relay_goal = 0.5 * (env.base.blue_pos[env.scout] + env.base.blue_pos[env.executor])
    return [scout_goal, relay_goal, env.primary_position]


def physical_step(env: PSCRRoleCommitmentEnv, goals: list[np.ndarray]) -> bool:
    primitive = np.asarray([env._autopilot_action(agent, goal) for agent, goal in enumerate(goals)], dtype=np.int64)
    env.base._move_blue(primitive)
    env.base._update_sensing_and_comm()
    env.step_count += 1
    return bool(env.base._has_collision() or env.base._has_constraint_violation())


def chain_at(env: PSCRRoleCommitmentEnv, target: np.ndarray) -> bool:
    scout_ok = float(np.linalg.norm(env.base.blue_pos[env.scout] - target)) <= SENSING_RADIUS
    executor_ok = float(np.linalg.norm(env.base.blue_pos[env.executor] - target)) <= EXECUTION_RADIUS
    adjacency = env.base.comm_adj
    relay_ok = bool(adjacency[env.relay, env.scout] > 0.5 and adjacency[env.executor, env.relay] > 0.5)
    return bool(scout_ok and executor_ok and relay_ok)


def localizes(env: PSCRRoleCommitmentEnv, target: np.ndarray) -> bool:
    adjacency = env.base.comm_adj
    return bool(
        float(np.linalg.norm(env.base.blue_pos[env.scout] - target)) <= LOCALIZATION_RADIUS
        and adjacency[env.relay, env.scout] > 0.5
        and adjacency[env.executor, env.relay] > 0.5
    )


def rollout(seed: int, mode: str, sector: int, urgent: bool, x_offset: float, urgent_deadline: int) -> dict[str, float]:
    env = make_env(seed)
    target = FORECAST_POSITION + np.asarray((x_offset, 0.0 if sector > 0 else -10_000.0, 0.0), dtype=np.float32)
    primary_hold = future_hold = 0
    primary_done = future_done = localized = False
    localization_step = -1
    failed = False
    routine_deadline = ARRIVAL + 66
    while env.step_count < HORIZON and not failed:
        future_active = env.step_count >= ARRIVAL
        if not future_active:
            goals = action_to_goals(env, mode, None, False)
        else:
            localized = localized or localizes(env, target)
            if localized and localization_step < 0:
                localization_step = env.step_count
            goals = action_to_goals(env, mode, target, localized)
        failed = physical_step(env, goals)
        if not primary_done and env.step_count <= 116:
            primary_hold = primary_hold + 1 if chain_at(env, env.primary_position) else 0
            primary_done = primary_done or primary_hold >= HOLD_STEPS
        if future_active and localized and not future_done and env.step_count <= (urgent_deadline if urgent else routine_deadline):
            future_hold = future_hold + 1 if chain_at(env, target) else 0
            future_done = future_done or future_hold >= HOLD_STEPS
        if primary_done and future_done:
            break
    value = float(primary_done) + (1.35 if urgent else 1.10) * float(future_done)
    return {"value": value, "primary_complete": float(primary_done), "future_complete": float(future_done), "localized": float(localized), "localization_step": float(localization_step), "failed_constraint_or_collision": float(failed), "energy_used": float(np.maximum(0.0, env._energy_at_reset - env.base.blue_energy).sum())}


def posterior(seed: int, mode: str, reliability: float, urgent_deadline: int) -> tuple[float, dict[str, float]]:
    weighted: dict[str, float] = {"value": 0.0, "primary_complete": 0.0, "future_complete": 0.0, "localized": 0.0, "failed_constraint_or_collision": 0.0, "energy_used": 0.0}
    for aligned, sector_probability in ((True, reliability), (False, 1.0 - reliability)):
        sector = 1 if aligned else -1
        for urgent, urgency_probability in ((True, URGENT_PROBABILITY), (False, 1.0 - URGENT_PROBABILITY)):
            for offset in X_OFFSETS:
                probability = sector_probability * urgency_probability / len(X_OFFSETS)
                outcome = rollout(seed, mode, sector, urgent, offset, urgent_deadline)
                for key in weighted:
                    weighted[key] += probability * outcome[key]
    return weighted["value"], weighted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--states", type=int, default=4)
    parser.add_argument("--urgent-deadline", type=int, default=120)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows: list[dict[str, object]] = []
    values = {(r, m): [] for r in (0.9, 0.1) for m in ("maintain", "stage")}
    high_support = low_support = 0
    for reliability in (0.9, 0.1):
        for offset in range(args.states):
            seed = 98_000 + offset
            per_mode = {}
            for mode in ("maintain", "stage"):
                value, metrics = posterior(seed, mode, reliability, args.urgent_deadline)
                values[(reliability, mode)].append(value)
                per_mode[mode] = value
                rows.append({"seed": seed, "reliability": reliability, "mode": mode, "public_posterior_value": value, **metrics})
            high_support += int(reliability == 0.9 and per_mode["stage"] > per_mode["maintain"] + MARGIN)
            low_support += int(reliability == 0.1 and per_mode["maintain"] > per_mode["stage"] + MARGIN)
    mean = {(r, m): float(np.mean(values[(r, m)])) for r in (0.9, 0.1) for m in ("maintain", "stage")}
    report = {"protocol": "PSCR-P8-SEARCH-PREFIX-Q0", "diagnostic_only": True, "states_per_reliability": args.states, "urgent_deadline": args.urgent_deadline, "physical_contract": {"primary_position": PRIMARY_POSITION.tolist(), "forecast_position": FORECAST_POSITION.tolist(), "commit_step": COMMIT, "arrival_step": ARRIVAL, "localization_radius": LOCALIZATION_RADIUS}, "high_reliability_stage_preferred": mean[(0.9, "stage")] > mean[(0.9, "maintain")] + MARGIN, "low_reliability_maintain_preferred": mean[(0.1, "maintain")] > mean[(0.1, "stage")] + MARGIN, "high_state_support": high_support, "low_state_support": low_support, "means": {f"r{r}_{m}": value for (r, m), value in mean.items()}, "verdict": "PSCR_P8_IDENTIFIABILITY_PASS" if high_support >= 3 and low_support >= 3 and mean[(0.9, "stage")] > mean[(0.9, "maintain")] + MARGIN and mean[(0.1, "maintain")] > mean[(0.1, "stage")] + MARGIN else "PSCR_P8_IDENTIFIABILITY_FAIL", "interpretation": "Pass establishes a physical public-belief allocation trade-off only; it does not establish a learned method."}
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P8_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "PSCR_P8_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
