"""Zero-training G0 audit for V8's branch-value commitment task.

V8 preserves the early legal authorisation as a compulsory public mission
precondition.  Its only learned relay action occurs at the later public branch,
where the optimal choice reverses: retain the current bridge for current-value
profiles and reconstruct the announced future bridge for future-value profiles.
The check uses fixed legal controllers only and is development evidence, never
paper evidence.
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


PROTOCOL = "COMMITMENT-HANDOFF-3D-V8-BRANCH-VALUE-G0-V1"
SEEDS = (83_501, 83_502, 83_503, 83_504, 83_505, 83_506)
MODES = ("always_retain", "always_reconstruct", "public_value_rule")


def relay_action(env: CommitmentHandoffIntercept3DEnv, mode: str) -> int:
    if mode == "always_retain":
        return RETAIN_CURRENT
    if mode == "always_reconstruct":
        return RECONSTRUCT_FUTURE
    if mode == "public_value_rule":
        # _future_service_required is a deterministic function only of the
        # public envelope fields appended to the actor observation.  It never
        # reads a profile identity, target state, peer-hidden state, or future
        # manoeuvre truth.
        return RECONSTRUCT_FUTURE if env._future_service_required() else RETAIN_CURRENT
    raise ValueError(mode)


def run_episode(seed: int, profile: str, mode: str, *, max_steps: int, branch_step: int) -> dict[str, object]:
    env = CommitmentHandoffIntercept3DEnv(
        TimedHandoffIntercept3DConfig(
            seed=seed,
            handoff_context="current_authorization",
            authorization_start_step=0,
            authorization_deadline=16,
            branch_step=branch_step,
            authorization_hold_steps=8,
            refresh_hold_steps=16,
            handoff_corridor_radius=900.0,
            future_corridor_lateral_offset=900.0,
            commitment_action_repeat=8,
            commitment_decision_mode="branch_value_v8",
            commitment_authorization_decision_step=0,
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
    decision_trace: list[dict[str, int]] = []
    for _ in range(env.config.max_steps):
        action = relay_action(env, mode)
        _, _, _, _, dones, info = env.step(np.asarray((RETAIN_CURRENT, action, RETAIN_CURRENT), dtype=np.int64))
        if float(info.get("commitment_relay_decision_active", 0.0)) > 0.5:
            decision_trace.append({"sampled_action": int(action), "effective_action": int(info["commitment_relay_effective_action"])})
        if bool(np.all(dones)):
            break
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
        "decision_trace": decision_trace,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=260)
    parser.add_argument("--branch-step", type=int, default=24)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    rows = [
        run_episode(seed, profile, mode, max_steps=args.max_steps, branch_step=args.branch_step)
        for profile in SERVICE_ENVELOPE_PROFILES for seed in SEEDS for mode in MODES
    ]
    summary: dict[str, dict[str, object]] = {}
    passed = True
    for profile in SERVICE_ENVELOPE_PROFILES:
        cell = [row for row in rows if row["profile"] == profile]
        rates = {mode: float(np.mean([row["success"] for row in cell if row["mode"] == mode])) for mode in MODES}
        future = bool(cell[0]["future_required"])
        # In a per-profile cell, the public rule intentionally coincides with
        # one fixed controller: retain for a current-value envelope and
        # reconstruct for a future-value envelope.  The causal-conflict test
        # is therefore the *reversal* of the two fixed controllers, plus
        # success of the one public rule across both kinds of envelope—not a
        # nonsensical strict comparison between identical actions.
        profile_pass = (
            rates["always_retain"] > rates["always_reconstruct"]
            if not future
            else rates["always_reconstruct"] > rates["always_retain"]
        ) and rates["public_value_rule"] > 0.0
        passed = passed and profile_pass
        summary[profile] = {"future_required": int(future), "success_rate": rates, "passes_profile": profile_pass}
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "v8_g0_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_BRANCH_VALUE_AUDIT",
        "paper_evidence": False,
        "training_started": False,
        "decision_schedule": {"authorization": "compulsory_retain", "branch": args.branch_step},
        "profiles": list(SERVICE_ENVELOPE_PROFILES),
        "modes": list(MODES),
        "summary": summary,
        "verdict": "V8_G0_BRANCH_VALUE_PASS" if passed else "V8_G0_NOT_YET_ESTABLISHED",
    }
    (args.out_dir / "v8_g0_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
