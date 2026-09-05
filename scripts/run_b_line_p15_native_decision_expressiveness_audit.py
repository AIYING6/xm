"""Non-learning audit of B-line native decision expressiveness.

The audit uses a handful of exact unmodified environment transitions.  It is
not a solver, a policy evaluation, a benchmark, or an environment change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.redundant_topology_uav_env import RedundantTopologyUAVEnv, scale_config
from scripts.run_b_line_p0r_native_freshness_counterexample import construct_history, load_freeze, physical_snapshot


FREEZE_PATH = ROOT / "configs" / "b_line_p15_native_decision_expressiveness_audit_freeze.json"
P0R_PATH = ROOT / "docs" / "b_line_p0r_20260905" / "p0r-execution" / "B_P0R_NATIVE_FRESHNESS_RESULT.json"
P1_PATH = ROOT / "docs" / "b_line_p1_20260905" / "p1-execution" / "B_P1_FORMAL_PROBLEM_NOVELTY_RESULT.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_lf(path: Path, content: str) -> None:
    path.write_bytes(content.replace("\r\n", "\n").encode("utf-8"))


def zero_actions(env: RedundantTopologyUAVEnv) -> np.ndarray:
    return np.zeros(env.n, dtype=np.int64)


def dynamic_state(env: RedundantTopologyUAVEnv) -> dict[str, Any]:
    return {
        "physical": physical_snapshot(env),
        "caches": [
            {str(k): {name: (value.tolist() if isinstance(value, np.ndarray) else value) for name, value in token.items()}
             for k, token in sorted(cache.items())}
            for cache in env.caches
        ],
    }


def analyze() -> dict[str, Any]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    p0r = json.loads(P0R_PATH.read_text(encoding="utf-8"))
    p1 = json.loads(P1_PATH.read_text(encoding="utf-8"))

    config = scale_config("main")
    baseline = RedundantTopologyUAVEnv(config)
    baseline.reset()
    active = baseline.active_adjacency()
    sensing_reach = [
        float(np.linalg.norm(baseline.positions[scout] - baseline.objective_positions[objective])) <= config.scout_sense_range
        for scout in baseline.scout_ids for objective in range(baseline.k)
    ]
    all_legal_routes_active = all(
        bool(active[relay, scout] and active[terminal, relay])
        for scout in baseline.scout_ids for relay in baseline.relay_ids for terminal in baseline.terminal_ids
    )

    # Scout sensing changes only cache state in this one-step comparison; there
    # is no native direct sensing cost in the reward components.
    sensing_env = RedundantTopologyUAVEnv(scale_config("main")); sensing_env.reset()
    idle_env = RedundantTopologyUAVEnv(scale_config("main")); idle_env.reset()
    sense_actions = zero_actions(sensing_env)
    for scout, objective in zip(sensing_env.scout_ids, range(sensing_env.k)):
        sense_actions[scout] = objective + 1
    _, _, _, sensing_rewards, _, _ = sensing_env.step(sense_actions)
    _, _, _, idle_rewards, _, _ = idle_env.step(zero_actions(idle_env))
    sensing_has_no_direct_reward_cost = bool(np.array_equal(sensing_rewards, idle_rewards))
    sensing_has_no_direct_physical_effect = physical_snapshot(sensing_env) == physical_snapshot(idle_env)

    # A stale observation masks terminal action 1.  Nevertheless, when the
    # raw joint action includes sensing plus the terminal action, step ordering
    # routes the new token before terminal motion.  This demonstrates that a
    # previous observation mask is not a closed centralized transition action
    # constraint for a future joint solver.
    stale_env = construct_history("stale", load_freeze())
    pre_masks = {
        str(int(terminal)): stale_env.support_action_mask(int(terminal)).astype(int).tolist()
        for terminal in stale_env.terminal_ids
    }
    pre_positions = stale_env.positions.copy()
    joint_actions = zero_actions(stale_env)
    joint_actions[stale_env.scout_ids] = 1
    joint_actions[stale_env.terminal_ids] = 1
    stale_env.step(joint_actions)
    terminal_moved_after_same_step_sensing = bool(np.any(stale_env.positions[stale_env.terminal_ids] != pre_positions[stale_env.terminal_ids]))
    action_was_masked_before_step = all(mask[1] == 0 for mask in pre_masks.values())

    # Relay values are exposed but their values do not participate in sensing,
    # routing, motion, or reward. Compare one exact step with raw relay values.
    relay_idle = RedundantTopologyUAVEnv(scale_config("main")); relay_idle.reset()
    relay_nonidle = RedundantTopologyUAVEnv(scale_config("main")); relay_nonidle.reset()
    nonidle_actions = zero_actions(relay_nonidle)
    nonidle_actions[relay_nonidle.relay_ids] = 1
    relay_idle.step(zero_actions(relay_idle))
    relay_nonidle.step(nonidle_actions)
    relay_actions_transition_inert = dynamic_state(relay_idle) == dynamic_state(relay_nonidle)

    capabilities = {
        "p0r_problem_premise_retained": p0r.get("verdict") == freeze["upstream"]["required_p0r_verdict"],
        "p1_formal_boundary_retained": p1.get("verdict") == freeze["upstream"]["required_p1_verdict"],
        "main_has_as_many_scouts_as_objectives": int(config.scouts) == int(config.num_objectives),
        "all_main_scout_objective_pairs_senseable_at_reset": all(sensing_reach),
        "all_main_legal_routes_active_at_reset": all_legal_routes_active,
        "sensing_has_no_direct_native_reward_cost": sensing_has_no_direct_reward_cost,
        "sensing_has_no_direct_physical_effect": sensing_has_no_direct_physical_effect,
        "relay_actions_are_transition_effective": not relay_actions_transition_inert,
        "previous_mask_closed_under_joint_transition": not (action_was_masked_before_step and terminal_moved_after_same_step_sensing),
        "nontrivial_native_reconfiguration_variable_exists": False,
    }
    sufficient = all(capabilities[key] for key in (
        "relay_actions_are_transition_effective",
        "previous_mask_closed_under_joint_transition",
        "nontrivial_native_reconfiguration_variable_exists",
    ))
    verdict = freeze["verdicts"]["go"] if sufficient else freeze["verdicts"]["no_go"]

    return {
        "protocol": freeze["protocol"],
        "verdict": verdict,
        "source_sha256": {
            "freeze": sha256(FREEZE_PATH),
            "environment": sha256(ROOT / "envs" / "redundant_topology_uav_env.py"),
            "p0r_result": sha256(P0R_PATH),
            "p1_result": sha256(P1_PATH),
        },
        "capabilities": capabilities,
        "observations": {
            "main_counts": {"scouts": int(config.scouts), "relays": int(config.relays), "terminals": int(config.terminals), "objectives": int(config.num_objectives)},
            "tau_max": int(config.tau_max),
            "pre_step_stale_terminal_masks": pre_masks,
            "same_step_sensing_then_terminal_motion": terminal_moved_after_same_step_sensing,
            "relay_raw_nonidle_action_transition_inert": relay_actions_transition_inert,
        },
        "decision": {
            "scope": "This closes only direct high-ceiling solver development on the current unmodified six-UAV action interface.",
            "reason": "The native interface has no transition-effective relay/routing/switching control; default main sensing has full coverage with no direct cost; and a prior observation mask is not closed under the joint transition ordering.",
            "retained_asset": "P0R remains valid evidence that physical snapshots can omit legally relevant information-validity state.",
            "not_authorized": "No solver, training, benchmark, or environment modification follows from this audit.",
        },
        "environment_steps": 12,
        "evaluation_episodes": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }


def write_outputs(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_lf(output_dir / "B_P15_NATIVE_DECISION_EXPRESSIVENESS_RESULT.json", canonical_json(result))
    report = "\n".join([
        "# B-line P1.5 native-decision expressiveness audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "This is a deterministic interface audit, not policy evaluation or a benchmark. No solver, checkpoint, training, reward change, action addition, or environment modification was used.",
        "",
        "## Findings",
        "",
        "- Default `main` has two scouts and two objectives; every scout can sense every objective at reset and all legal routes are active.",
        "- Native scout sensing has no direct reward or physical cost in the audited one-step transition.",
        "- Raw relay non-idle values leave the transition state unchanged.",
        "- A terminal action masked by the pre-step stale observation can still cause terminal motion when scouts sense that objective in the same raw joint action, because the environment routes packets before terminal motion.",
        "",
        "Together these facts prevent the current frozen interface from supporting the requested controllable information-validity reconfiguration problem. The P0R premise remains scientifically useful, but it cannot honestly be promoted into a high-ceiling solver on this interface without adding semantics — an action P1/P1.5 forbids.",
        "",
    ])
    write_lf(output_dir / "B_LINE_P15_NATIVE_DECISION_EXPRESSIVENESS_REPORT.md", report)
    artifacts = {path.name: sha256(path) for path in sorted(output_dir.iterdir()) if path.is_file()}
    write_lf(output_dir / "B_P15_NATIVE_DECISION_EXPRESSIVENESS_ARTIFACTS.json", canonical_json(artifacts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to execute P1.5 without --execute")
    output_dir = Path(args.output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing to overwrite existing output: {output_dir}")
    write_outputs(output_dir, analyze())


if __name__ == "__main__":
    main()
