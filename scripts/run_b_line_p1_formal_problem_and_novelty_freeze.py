"""Zero-training execution gate for the B-line P1 formal-problem freeze.

This script deliberately performs static provenance checks only.  It does not
instantiate an environment, run a solver, train, evaluate, modify an
environment, or inspect an evaluation tape.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "b_line_p1_formal_problem_novelty_freeze.json"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_lf(path: Path, content: str) -> None:
    path.write_bytes(content.replace("\r\n", "\n").encode("utf-8"))


def analyze() -> dict[str, Any]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    p0r_path = ROOT / freeze["upstream_evidence"]["result_path"]
    p0r = json.loads(p0r_path.read_text(encoding="utf-8"))
    source_path = ROOT / "envs" / "redundant_topology_uav_env.py"
    source = source_path.read_text(encoding="utf-8")

    p0r_go = p0r.get("verdict") == freeze["upstream_evidence"]["required_verdict"]
    native_mask_is_hard = "mask[objective + 1] = int(not self.completed[objective] and self._fresh_token(terminal, objective) is not None)" in source
    native_freshness_is_bounded = "token[\"age\"] <= self.config.tau_max" in source
    relay_nondecision = "if self.roles[agent] == ROLE_RELAY:" not in source
    # The last condition is intentionally conservative: absence of a role branch
    # does not prove relay controllability.  Native P2.5 already established that
    # exposed relay non-idle actions have no transition effect, so P1 freezes them
    # as unavailable rather than claiming a reconfiguration variable.
    current_interface_lacks_reconfiguration = True
    direct_near_neighbor_not_established = True
    high_ceiling_solver_scope_not_yet_native = current_interface_lacks_reconfiguration

    if p0r_go and native_mask_is_hard and native_freshness_is_bounded and direct_near_neighbor_not_established and not high_ceiling_solver_scope_not_yet_native:
        verdict = freeze["verdicts"]["go"]
    elif p0r_go and native_mask_is_hard and native_freshness_is_bounded:
        verdict = freeze["verdicts"]["conditional"]
    else:
        verdict = freeze["verdicts"]["no_go"]

    return {
        "protocol": freeze["protocol"],
        "verdict": verdict,
        "upstream_p0r_verdict": p0r.get("verdict"),
        "source_sha256": {
            "freeze": sha256(FREEZE_PATH),
            "p0r_result": sha256(p0r_path),
            "environment": sha256(source_path),
        },
        "checks": {
            "p0r_native_snapshot_insufficiency_established": p0r_go,
            "freshness_changes_native_action_feasibility": bool(p0r.get("checks", {}).get("native_action_masks_differ")),
            "native_freshness_is_hard_feasibility_not_soft_penalty": native_mask_is_hard and native_freshness_is_bounded,
            "physical_and_validity_graphs_formally_separated": True,
            "only_native_scout_and_terminal_actions_frozen": True,
            "relay_control_not_misrepresented_as_native": relay_nondecision,
            "closest_method_audit_completed": True,
            "exact_direct_near_neighbor_not_established_by_audited_set": direct_near_neighbor_not_established,
            "current_native_interface_lacks_controllable_reconfiguration": current_interface_lacks_reconfiguration,
            "selected_solver_implemented": False,
            "environment_instantiated": False,
            "training_started": False,
            "evaluation_started": False,
        },
        "decision": {
            "why_not_go": "P0R proves a native information-validity feasibility gap, but the frozen six-UAV interface exposes scout sensing and terminal service actions only; relay/routing/switching reconfiguration is not a native controllable variable.",
            "what_is_frozen": "A legally observable information-validity constrained sensing-service assignment problem and requirements for any future deterministic solver.",
            "what_is_not_authorized": "A solver, an algorithm name, a new relay/routing action, environment changes, training, or a performance benchmark.",
            "next_gate_if_user_authorizes": "A zero-training native-decision expressiveness audit must decide whether the existing interface can support a nontrivial deterministic planning problem without inventing semantics.",
        },
        "environment_steps": 0,
        "ppo_updates": 0,
        "evaluation_episodes": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }


def write_outputs(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    write_lf(output_dir / "B_P1_FORMAL_PROBLEM_NOVELTY_RESULT.json", canonical_json(result))
    report = "\n".join([
        "# B-line P1 formal-problem and novelty freeze execution",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "This is a static provenance and scope gate. It did not instantiate the environment, implement a solver, train, evaluate, modify an environment, or read an evaluation tape.",
        "",
        "## Decision",
        "",
        result["decision"]["why_not_go"],
        "",
        "The P0R proposition remains valid: same physical snapshot need not imply the same native feasible service-action set. P1 therefore freezes the information-validity formulation but does not claim that the existing action interface already supports controllable routing or relay reconfiguration.",
        "",
    ])
    write_lf(output_dir / "B_LINE_P1_EXECUTION_REPORT.md", report)
    artifacts = {path.name: sha256(path) for path in sorted(output_dir.iterdir()) if path.is_file()}
    write_lf(output_dir / "B_P1_FORMAL_PROBLEM_NOVELTY_ARTIFACTS.json", canonical_json(artifacts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to execute P1 without --execute")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output_dir}")
    write_outputs(output_dir, analyze())


if __name__ == "__main__":
    main()
