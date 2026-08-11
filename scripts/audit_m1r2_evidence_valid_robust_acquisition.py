"""Read-only M1-R2 feasibility audit for evidence-valid robust range progress.

This is deliberately *not* an EV-RAP implementation.  It replays frozen L4
policies and asks whether a current, recipient-valid target cache admits a
one-step guidance command that reduces a conservative attack-range deficit.
No true target state, global detection state, evaluator geometry predicate, or
target-policy rollout is read by the certificate calculation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    ACTION3D_TABLE,
    GUIDANCE_ACTION_TABLE,
    ROLE_ATTACKER,
    ROLE_INTERCEPTOR,
    angle_diff,
    velocity_from_state,
    wrap_angle,
)
from scripts import run_l4_corrected_contract_requalification as l4r  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402


OUT = ROOT / "results" / "m1r2_evidence_valid_robust_acquisition_audit"
CHECKPOINT_ROOT = ROOT / "results" / "l4_corrected_contract_requalification"
STAGE_RECORDS = ROOT / "results" / "l4_mission_failure_stage_localization" / "stage_records.csv"
TRAIN_SEEDS = (8901, 8902)
EPISODE_SEEDS = tuple(range(890_000, 890_032))
PROTOCOL = "M1R2_EVIDENCE_VALID_ROBUST_ACQUISITION_FEASIBILITY_V1"
EPSILON_METERS = 1e-6
MIN_REPAIRABLE_STATE_FRACTION = 0.25
MIN_REPAIRABLE_EPISODE_FRACTION = 0.25


def robust_range_deficit(own_pos: np.ndarray, cached_target_pos: np.ndarray, age_steps: float,
                         target_max_speed: float, attack_range_max: float) -> float:
    """Worst-case distance-to-range deficit using only a cache and public bound.

    The possible target set is the closed ball centered at the delivered/cache
    packet position with radius ``age * max_speed``.  This is an intentionally
    conservative kinematic reachability envelope; no target-policy prediction
    or current target truth is involved.
    """
    radius = max(0.0, float(age_steps)) * max(0.0, float(target_max_speed))
    return max(0.0, float(np.linalg.norm(np.asarray(cached_target_pos) - np.asarray(own_pos))) + radius - attack_range_max)


def decode_guidance(env, attacker: int, command: np.ndarray) -> int:
    typ = env.config.blue_types[attacker]
    turn = float(np.clip(command[0], -1.0, 1.0))
    climb = float(np.clip(command[1], -1.0, 1.0))
    speed_mid = 0.5 * (typ.min_speed + typ.max_speed)
    speed_error = speed_mid - float(env.blue_speed[attacker])
    accel = 1.0 if speed_error > 0.5 * typ.max_accel else (-1.0 if speed_error < -0.5 * typ.max_accel else 0.0)
    return int(np.argmin(np.linalg.norm(ACTION3D_TABLE - np.asarray((turn, climb, accel), dtype=np.float32)[None, :], axis=1)))


def next_own_position(env, attacker: int, guidance: np.ndarray) -> np.ndarray:
    """Exact one-step own-state update matching _move_blue, without target reads."""
    typ = env.config.blue_types[attacker]
    turn_cmd, climb_cmd, accel_cmd = ACTION3D_TABLE[decode_guidance(env, attacker, guidance)]
    heading = wrap_angle(float(env.blue_heading[attacker]) + float(turn_cmd) * typ.max_turn_rate * env.config.dt)
    pos = np.asarray(env.blue_pos[attacker], dtype=np.float64).copy()
    speed = float(env.blue_speed[attacker])
    gamma = float(env.blue_gamma[attacker])
    xy_radius = float(np.linalg.norm(pos[:2]))
    if xy_radius >= env.config.world_radius - env.config.boundary_protection_margin:
        desired = math.atan2(float(-pos[1]), float(-pos[0]))
        heading = wrap_angle(heading + float(np.clip(angle_diff(desired, heading), -typ.max_turn_rate * env.config.dt, typ.max_turn_rate * env.config.dt)))
        accel_cmd = -1.0
    gamma = float(np.clip(gamma + float(climb_cmd) * 0.35 * typ.max_gamma * env.config.dt, -typ.max_gamma, typ.max_gamma))
    if pos[2] <= env.config.min_altitude + env.config.altitude_protection_margin and gamma < 0.0:
        gamma = 0.25 * typ.max_gamma
    elif pos[2] >= env.config.max_altitude - env.config.altitude_protection_margin and gamma > 0.0:
        gamma = -0.25 * typ.max_gamma
    speed = float(np.clip(speed + float(accel_cmd) * typ.max_accel * env.config.dt, typ.min_speed, typ.max_speed))
    return pos + velocity_from_state(speed, heading, gamma) * env.config.dt


def certificate(env, attacker: int, policy_guidance: np.ndarray) -> dict[str, object] | None:
    """Return legal-only progress fields, or None when legal target evidence is absent."""
    if not env._has_fresh_target_cache(attacker):
        return None
    age = env._local_target_cache_age(attacker)
    cached_pos = np.asarray(env.target_cache_pos[attacker], dtype=np.float64).copy()
    own_pos = np.asarray(env.blue_pos[attacker], dtype=np.float64).copy()
    typ = env.config.blue_types[attacker]
    baseline = robust_range_deficit(own_pos, cached_pos, age, env.config.target_type.max_speed, typ.attack_range_max)
    chosen_pos = next_own_position(env, attacker, policy_guidance)
    chosen = robust_range_deficit(chosen_pos, cached_pos, age + env.config.dt, env.config.target_type.max_speed, typ.attack_range_max)
    candidates = []
    for turn, climb in GUIDANCE_ACTION_TABLE:
        pos = next_own_position(env, attacker, np.asarray((turn, climb), dtype=np.float32))
        candidates.append(robust_range_deficit(pos, cached_pos, age + env.config.dt, env.config.target_type.max_speed, typ.attack_range_max))
    best = float(min(candidates))
    return {
        "cache_age_steps": float(age),
        "cache_confidence": float(env.target_cache_confidence[attacker]),
        "cache_source": int(env.target_cache_source[attacker]),
        "robust_deficit_before": baseline,
        "policy_robust_deficit_after": chosen,
        "best_robust_deficit_after": best,
        "policy_progress": int(chosen < baseline - EPSILON_METERS),
        "progress_action_exists": int(best < baseline - EPSILON_METERS),
        "repairable": int(best < baseline - EPSILON_METERS and chosen >= baseline - EPSILON_METERS),
    }


def target_truth_invariance_check(env, attacker: int, guidance: np.ndarray) -> None:
    """Guard that the certificate does not consume evaluator/global target truth."""
    before = certificate(env, attacker, guidance)
    if before is None:
        return
    red_pos = env.red_pos.copy(); red_speed = env.red_speed.copy(); red_heading = env.red_heading.copy(); red_gamma = env.red_gamma.copy()
    last_pos = None if env.last_detected_target_pos is None else env.last_detected_target_pos.copy()
    last_vel = None if env.last_detected_target_vel is None else env.last_detected_target_vel.copy()
    last_step = env.last_detection_step
    env.red_pos[:] += 123456.0; env.red_speed[:] += 11.0; env.red_heading[:] += 0.7; env.red_gamma[:] += 0.2
    env.last_detected_target_pos = np.full(3, -99999.0, dtype=np.float32)
    env.last_detected_target_vel = np.full(3, 99999.0, dtype=np.float32); env.last_detection_step = -999
    after = certificate(env, attacker, guidance)
    env.red_pos[:] = red_pos; env.red_speed[:] = red_speed; env.red_heading[:] = red_heading; env.red_gamma[:] = red_gamma
    env.last_detected_target_pos = last_pos; env.last_detected_target_vel = last_vel; env.last_detection_step = last_step
    if after is None or any(abs(float(before[k]) - float(after[k])) > 1e-9 for k in ("robust_deficit_before", "policy_robust_deficit_after", "best_robust_deficit_after")):
        raise AssertionError("certificate changed when only prohibited target truth changed")


def replay(cfg, training_seed: int, episode_seed: int, agent, failure_stage: str) -> list[dict[str, object]]:
    env = l0.make_env(cfg, episode_seed, training=False)
    obs, share, graph = env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR})
    records: list[dict[str, object]] = []
    while True:
        action = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.num_agents, 3)
        for i, typ in enumerate(env.config.blue_types):
            if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                action[i, 2] = -1.0
        evidence = certificate(env, attacker, action[attacker, :2])
        if evidence is not None:
            target_truth_invariance_check(env, attacker, action[attacker, :2])
            records.append({"training_seed": training_seed, "episode_seed": episode_seed, "step": int(env.step_count), **evidence})
        obs, share, graph, _reward, dones, info = env.step(action)
        if bool(np.all(dones)):
            outcome = l0.outcome(info)
            for row in records:
                row["terminal_outcome"] = outcome
                row["terminal_step"] = int(info["step"])
                # Evaluator-only label used solely to select previously
                # localized episodes.  It is never passed to the certificate.
                row["failure_stage"] = failure_stage
            return records


def run(output: Path) -> dict[str, object]:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite {output}")
    if not STAGE_RECORDS.exists():
        raise FileNotFoundError(STAGE_RECORDS)
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, object]] = []; hashes: dict[str, str] = {}
    stage_by_episode = {
        (int(row["training_seed"]), int(row["episode_seed"])): row["failure_stage"]
        for row in csv.DictReader(STAGE_RECORDS.open(encoding="utf-8"))
    }
    for training_seed in TRAIN_SEEDS:
        checkpoint = CHECKPOINT_ROOT / f"l4_corrected_contract_seed{training_seed}" / "actor_critic_latest.pt"
        if not checkpoint.exists(): raise FileNotFoundError(checkpoint)
        hashes[str(training_seed)] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        cfg = l4r.cfg(training_seed, output / "template", updates=1)
        agent = l0.load_agent(cfg, checkpoint)
        for episode_seed in EPISODE_SEEDS:
            rows.extend(replay(cfg, training_seed, episode_seed, agent, stage_by_episode[(training_seed, episode_seed)]))
    selected = [r for r in rows if r["failure_stage"] == "NO_ATTACK_RANGE_ACQUISITION"]
    by_seed = []
    for seed in TRAIN_SEEDS:
        group = [r for r in selected if r["training_seed"] == seed]
        repairable_episodes = {int(r["episode_seed"]) for r in group if r["repairable"]}
        failure_episodes = {int(r["episode_seed"]) for r in group}
        by_seed.append({
            "training_seed": seed,
            "legal_evidence_decision_states": len(group),
            "progress_feasible_state_fraction": float(np.mean([r["progress_action_exists"] for r in group])) if group else 0.0,
            "policy_progress_state_fraction": float(np.mean([r["policy_progress"] for r in group])) if group else 0.0,
            "repairable_state_fraction": float(np.mean([r["repairable"] for r in group])) if group else 0.0,
            "failure_episodes_with_legal_evidence": len(failure_episodes),
            "repairable_failure_episode_fraction": len(repairable_episodes) / len(failure_episodes) if failure_episodes else 0.0,
        })
    passes = all(r["repairable_state_fraction"] >= MIN_REPAIRABLE_STATE_FRACTION and r["repairable_failure_episode_fraction"] >= MIN_REPAIRABLE_EPISODE_FRACTION for r in by_seed)
    payload = {
        "protocol": PROTOCOL,
        "performance_use_prohibited": True,
        "checkpoint_hashes": hashes,
        "evaluator_selection_only": "NO_ATTACK_RANGE_ACQUISITION from prior stage-localization records; labels are not certificate inputs",
        "episode_seeds": list(EPISODE_SEEDS),
        "legal_target_set": "closed ball(cache_position, cache_age_steps * public_target_max_speed)",
        "certificate": "existence of a one-step guidance command that strictly lowers worst-case attack-range deficit; not a neutralization or safety guarantee",
        "candidate_guidance_actions": GUIDANCE_ACTION_TABLE.tolist(),
        "thresholds_frozen_before_replay": {"epsilon_meters": EPSILON_METERS, "minimum_repairable_state_fraction": MIN_REPAIRABLE_STATE_FRACTION, "minimum_repairable_failure_episode_fraction": MIN_REPAIRABLE_EPISODE_FRACTION},
        "by_training_seed": by_seed,
        "verdict": "M1R2_OFFLINE_FEASIBILITY_PASS__NOVELTY_REVIEW_STILL_REQUIRED" if passes else "M1R2_OFFLINE_FEASIBILITY_NO_GO__ROBUST_PROGRESS_SET_NOT_SUFFICIENTLY_AVAILABLE",
    }
    fieldnames = list(rows[0]) if rows else ["training_seed", "episode_seed", "step"]
    with (output / "state_records.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames); writer.writeheader(); writer.writerows(rows)
    (output / "M1R2_OFFLINE_FEASIBILITY_MANIFEST.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def self_test() -> None:
    deficit = robust_range_deficit(np.zeros(3), np.asarray((100., 0., 0.)), 2, 10, 90)
    assert deficit == 30.0
    assert robust_range_deficit(np.zeros(3), np.asarray((20., 0., 0.)), 0, 10, 20) == 0.0
    print("M1R2_ROBUST_ACQUISITION_STATIC_TEST: PASS (2 tests)")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=OUT); parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test: self_test(); return
    print(json.dumps(run(args.output), indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
