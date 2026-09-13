"""Zero-training G0 audit for the timed-handoff 3DOF task foundation.

This audit does not train a policy and does not propose a method.  It runs two
legal-observation scripted relay behaviours in the existing strict
relay-dependent interception plant.  Its sole purpose is to determine whether
the current plant already contains a terminally meaningful handoff choice.
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

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv
from scripts.audit_intercept_3d_legal_baseline import legal_actions


PROTOCOL = "INTERCEPT-3D-HANDOFF-VALUE-G0-V1"
SEEDS = (71101, 71102, 71103, 71104, 71105, 71106)
MODES = ("relay_hold_current_bridge", "relay_preposition_future_corridor")
CONTEXTS = {
    # At 0.70 the initial scout--relay--attacker bridge remains physically
    # reachable, but relay departure can break the attacker-facing hop.  This
    # makes current-track delivery a real opportunity cost rather than merely
    # a weaker version of following the target.
    "urgent_current_track": {
        "max_target_message_age_steps": 24,
        "target_policy": "weaving_mild",
        "communication_range_scale": 0.70,
        "target_init_bearing_offset_deg": 0.0,
    },
    "refresh_sensitive_track": {
        "max_target_message_age_steps": 6,
        "target_policy": "break_turn_param",
        "communication_range_scale": 1.00,
        "target_init_bearing_offset_deg": 22.0,
    },
}


def forward_action() -> int:
    """Keep heading/altitude and accelerate; this is an existing primitive action."""
    return int(np.flatnonzero(np.all(np.isclose(ACTION3D_TABLE, (0.0, 0.0, 1.0)), axis=1))[0])


def preposition_action() -> int:
    """Turn the relay toward the declared future corridor using a primitive action."""
    return int(np.flatnonzero(np.all(np.isclose(ACTION3D_TABLE, (1.0, 0.0, 1.0)), axis=1))[0])


def actions(obs: np.ndarray, mode: str) -> np.ndarray:
    """Return only primitive actions derived from each agent's emitted observation."""
    choice = legal_actions(obs)
    if mode == "relay_hold_current_bridge":
        choice[1] = forward_action()
    elif mode == "relay_preposition_future_corridor":
        choice[1] = preposition_action()
    else:
        raise ValueError(f"unsupported mode: {mode}")
    return choice


def run_episode(seed: int, context: str, mode: str) -> dict[str, object]:
    knobs = CONTEXTS[context]
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed,
            target_policy=str(knobs["target_policy"]),
            target_break_turn_amp_rad=np.pi * 0.5,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            communication_dropout_prob=0.0,
            radar_dropout_prob=0.0,
            message_delay_steps=2,
            communication_range_scale=float(knobs["communication_range_scale"]),
            target_init_bearing_offset_deg=float(knobs["target_init_bearing_offset_deg"]),
            max_target_message_age_steps=int(knobs["max_target_message_age_steps"]),
            min_target_confidence=0.2,
            max_steps=260,
        )
    )
    obs, _, _ = env.reset()
    telemetry = {
        "attacker_fresh_steps": 0,
        "relay_required_fresh_steps": 0,
        "attack_window_with_info_steps": 0,
        "chain_support_steps": 0,
    }
    info: dict[str, object] = {}
    for _ in range(env.config.max_steps):
        obs, _, _, _, done, info = env.step(actions(obs, mode))
        telemetry["attacker_fresh_steps"] += int(float(info["attacker_has_fresh_target_info"]) > 0.5)
        telemetry["relay_required_fresh_steps"] += int(float(info["attacker_relay_required_fresh_information_t"]) > 0.5)
        telemetry["attack_window_with_info_steps"] += int(float(info["attacker_info_attack_window"]) > 0.5)
        telemetry["chain_support_steps"] += int(float(info["chain_support_t"]) > 0.5)
        if bool(done[0, 0]):
            break
    return {
        "seed": seed,
        "context": context,
        "mode": mode,
        "success": int(float(info.get("success", 0.0)) > 0.5),
        "timeout": int(float(info.get("timeout", 0.0)) > 0.5),
        "collision": int(float(info.get("collision", 0.0)) > 0.5),
        "steps": int(float(info.get("step", 0.0))),
        **telemetry,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("G0 changes only its diagnostic output; pass --execute.")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")

    rows = [run_episode(seed, context, mode) for context in CONTEXTS for seed in SEEDS for mode in MODES]
    args.out_dir.mkdir(parents=True)
    with (args.out_dir / "handoff_g0_rows.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary: dict[str, dict[str, float]] = {}
    switch_directions: list[int] = []
    for context in CONTEXTS:
        by_mode = {mode: [r for r in rows if r["context"] == context and r["mode"] == mode] for mode in MODES}
        success = {mode: float(np.mean([r["success"] for r in cell])) for mode, cell in by_mode.items()}
        fresh = {mode: float(np.mean([r["attacker_fresh_steps"] for r in cell])) for mode, cell in by_mode.items()}
        delta = success[MODES[1]] - success[MODES[0]]
        switch_directions.append(int(np.sign(delta)))
        summary[context] = {
            "hold_success": success[MODES[0]],
            "follow_success": success[MODES[1]],
            "follow_minus_hold_success": delta,
            "hold_mean_attacker_fresh_steps": fresh[MODES[0]],
            "follow_mean_attacker_fresh_steps": fresh[MODES[1]],
        }

    reversal = len(set(switch_directions)) > 1 and 0 not in switch_directions
    result = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_ZERO_TRAINING_DECISION_SWITCH_AUDIT",
        "paper_evidence": False,
        "training_started": False,
        "actor_information": "emitted local observation only; relay hold is a primitive action, follow uses the same local geometric controller",
        "contexts": CONTEXTS,
        "rows": len(rows),
        "summary": summary,
        "decision_preference_reversal_observed": reversal,
        "verdict": "G0_DECISION_SWITCH_PASS" if reversal else "G0_DECISION_SWITCH_NOT_YET_ESTABLISHED",
        "interpretation": (
            "A pass only establishes a physical decision-switch candidate for subsequent task implementation; it is not a learned-method result. "
            "A non-pass means the current plant lacks a demonstrated terminal preference reversal for these two legal relay behaviours."
        ),
    }
    (args.out_dir / "handoff_g0_report.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
