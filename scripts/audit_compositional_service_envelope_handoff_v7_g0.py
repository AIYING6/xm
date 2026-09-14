"""Zero-training audit for V7's two-decision staged commitment interface.

This development-only check establishes that the new interface preserves a
real decision conflict before any learning begins.  It compares fixed legal
controllers, not learned policies: retaining throughout, reconstructing at
both decisions, and retaining early then reconstructing after the public
branch.  The latter is the only controller allowed to succeed on future-route
profiles; early reconstruction must fail their irrevocable authorization.
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

from envs.commitment_handoff_intercept_3d_env import (  # noqa: E402
    RECONSTRUCT_FUTURE,
    RETAIN_CURRENT,
    CommitmentHandoffIntercept3DEnv,
)
from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES, TimedHandoffIntercept3DConfig  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V7-TWO-DECISION-G0-V1"
SEEDS = (83_301, 83_302, 83_303, 83_304, 83_305, 83_306)
BRANCH_STEP = 40
AUTHORIZATION_DECISION_STEP = 0
FUTURE_CORRIDOR_LATERAL_OFFSET = 900.0
MODES = ("always_retain", "always_reconstruct", "staged_public_rule")


def relay_action(env: CommitmentHandoffIntercept3DEnv, mode: str) -> int:
    if mode == "always_retain":
        return RETAIN_CURRENT
    if mode == "always_reconstruct":
        return RECONSTRUCT_FUTURE
    if mode == "staged_public_rule":
        # This controller sees only the public clock.  Current profiles finish
        # at the authorization stage; future profiles require the post-branch
        # route, so the same retain-then-reconstruct rule is legal for every
        # profile and never reads a profile label or target state.
        return RECONSTRUCT_FUTURE if env.step_count >= env.handoff_config.branch_step else RETAIN_CURRENT
    raise ValueError(mode)


def run_episode(
    seed: int,
    profile: str,
    mode: str,
    *,
    future_offset: float,
    authorization_decision_step: int,
    max_steps: int,
    authorization_deadline: int,
    branch_step: int,
) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context="current_authorization",
            authorization_start_step=0,
            authorization_deadline=authorization_deadline,
            branch_step=branch_step,
            authorization_hold_steps=8,
            refresh_hold_steps=16,
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=future_offset,
            commitment_action_repeat=8,
            commitment_decision_mode="staged_latched_v7",
            commitment_authorization_decision_step=authorization_decision_step,
            handoff_safety_mode="blue_team_only",
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=0,
            max_target_message_age_steps=10,
            target_init_range_scale=0.65,
            postbranch_target_policy="weaving_mild",
            max_steps=max_steps,
            service_envelope_mode="compositional_v6_staged",
            service_envelope_profile=profile,
        )
    )
    env.reset()
    info: dict[str, object] = {}
    decision_rows: list[dict[str, object]] = []
    for _ in range(env.config.max_steps):
        action = relay_action(env, mode)
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, action, RETAIN_CURRENT), dtype=np.int64))
        if float(info.get("commitment_relay_decision_active", 0.0)) > 0.5:
            decision_rows.append(
                {
                    "stage": "authorization" if float(info["commitment_relay_authorization_decision"]) > 0.5 else "branch",
                    "sampled_action": int(action),
                    "effective_action": int(info["commitment_relay_effective_action"]),
                }
            )
        if bool(dones[0, 0]):
            break
    blue_history = np.asarray(env.history["blue_pos"], dtype=np.float32)
    min_blue_pair_distance = min(
        float(np.linalg.norm(frame[i] - frame[j]))
        for frame in blue_history
        for i in range(env.num_agents)
        for j in range(i + 1, env.num_agents)
    )
    return {
        "seed": seed,
        "profile": profile,
        "mode": mode,
        "future_required": int(env._future_service_required()),
        "success": int(float(info.get("handoff_success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "authorization_observed": int(float(info.get("authorization_handoff_observed", 0.0)) > 0.5),
        "refresh_observed": int(float(info.get("postbranch_refresh_observed", 0.0)) > 0.5),
        "terminal_step": int(float(info.get("step", env.step_count))),
        "min_blue_pair_distance": min_blue_pair_distance,
        "decision_trace": decision_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--future-corridor-lateral-offset", type=float, default=FUTURE_CORRIDOR_LATERAL_OFFSET)
    parser.add_argument("--authorization-decision-step", type=int, default=AUTHORIZATION_DECISION_STEP)
    parser.add_argument("--max-steps", type=int, default=260)
    parser.add_argument("--authorization-deadline", type=int, default=28)
    parser.add_argument("--branch-step", type=int, default=BRANCH_STEP)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    rows = [
        run_episode(
            seed, profile, mode,
            future_offset=args.future_corridor_lateral_offset,
            authorization_decision_step=args.authorization_decision_step,
            max_steps=args.max_steps,
            authorization_deadline=args.authorization_deadline,
            branch_step=args.branch_step,
        )
        for profile in SERVICE_ENVELOPE_PROFILES for seed in SEEDS for mode in MODES
    ]
    summary: dict[str, dict[str, object]] = {}
    passed = True
    for profile in SERVICE_ENVELOPE_PROFILES:
        cell = [row for row in rows if row["profile"] == profile]
        rates = {mode: float(np.mean([row["success"] for row in cell if row["mode"] == mode])) for mode in MODES}
        future = bool(cell[0]["future_required"])
        profile_pass = (
            rates["always_retain"] > rates["always_reconstruct"]
            if not future
            else (
                rates["staged_public_rule"] > 0.0
                and rates["staged_public_rule"] > rates["always_retain"]
                and rates["staged_public_rule"] > rates["always_reconstruct"]
            )
        )
        passed = passed and profile_pass
        summary[profile] = {"future_required": int(future), "success_rate": rates, "passes_profile": profile_pass}
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v7_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_TWO_DECISION_AUDIT",
        "training_started": False,
        "decision_schedule": {"authorization": args.authorization_decision_step, "branch": args.branch_step},
        "future_corridor_lateral_offset": args.future_corridor_lateral_offset,
        "max_steps": args.max_steps,
        "profiles": list(SERVICE_ENVELOPE_PROFILES),
        "modes": list(MODES),
        "summary": summary,
        "verdict": "V7_G0_TWO_DECISION_PASS" if passed else "V7_G0_NOT_YET_ESTABLISHED",
    }
    (args.out_dir / "v7_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
