"""Static P1.5 audit for the one frozen TATG/CETM formula.

The audit intentionally implements only the algebraic update as NumPy, never
the actor, critic, rollout or PPO loop.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "tatg_mappo_p15_formula_freeze.json"


def load_freeze() -> dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def event_gate(delta: np.ndarray) -> float:
    return float(1.0 - np.exp(-np.mean(np.abs(np.asarray(delta, dtype=np.float64)))))


def cetm_update(previous_memory: np.ndarray, proposal: np.ndarray, delta: np.ndarray) -> np.ndarray:
    gate = event_gate(delta)
    return (1.0 - gate) * np.asarray(previous_memory) + gate * np.asarray(proposal)


def collect_checks(freeze: dict[str, Any]) -> dict[str, bool]:
    local = freeze["local_topology_state"]
    controls = freeze["mandatory_controls"]
    state = freeze["serialization_contract"]
    unchanged_memory = np.asarray([0.25, -0.5, 1.0], dtype=np.float64)
    changed_memory = cetm_update(unchanged_memory, np.zeros_like(unchanged_memory), np.zeros(9))
    active_memory = cetm_update(unchanged_memory, np.zeros_like(unchanged_memory), np.ones(9))
    return {
        "candidate_is_transition_residual_not_snapshot_gru": "x_i,t - x_i,t-1" in freeze["memory_formula"]["residual"],
        "local_topology_input_is_receiver_row_only": "receiver row i only" in local["legal_scope"],
        "existing_edge_age_proxy_retained": "edge_age" in local["x_i,t"],
        "no_hidden_failure_or_critic_input": all(token in local["forbidden"] for token in ["failure identity", "failure onset/duration schedule", "critic input"]),
        "zero_residual_memory_invariance": bool(np.array_equal(changed_memory, unchanged_memory)),
        "nonzero_residual_can_update_memory": bool(not np.array_equal(active_memory, unchanged_memory)),
        "generic_gru_control_is_capacity_matched": "exactly equal" in controls["capacity_rule"],
        "transition_information_ablation_frozen": "delta forced to zero" in controls["ablation"],
        "critic_and_ppo_are_unchanged": all(token in json.dumps(freeze["training_invariants"], sort_keys=True) for token in ["unchanged snapshot centralized critic", "unchanged objective"]),
        "runtime_state_serialization_is_explicit": state["per_environment_actor_state"] == ["m_i,t", "x_i,t-1", "a_i,t-1"],
        "no_legacy_stabilization_module": not any(
            token in freeze["candidate"].lower()
            for token in ["drtp", "egtr", "sampler", "gradient surgery", "distillation"]
        ),
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO P1.5 formula, fairness and serialization audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "CETM is frozen as an event-gated update of a local topology-transition residual. Its current-graph encoder and critic remain the existing snapshot components. The generic GNN+GRU control uses the same added GRUCell and head dimensions, but consumes a current topology vector rather than a transition residual and updates at every step.",
        "",
        "The audit is algebraic only. It does not instantiate a neural policy, read a checkpoint, step an environment, fit a probe, calculate return or run PPO.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "A pass authorizes only a separate C1 implementation and exact-serialization audit. It does not authorize any training or performance claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write P1.5 audit output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    freeze = load_freeze()
    checks = collect_checks(freeze)
    result = {
        "protocol": freeze["protocol"],
        "verdict": freeze["pass"] if all(checks.values()) else freeze["fail"],
        "checks": checks,
        "training_started": False,
        "evaluation_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "actor_or_critic_implemented": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_P15_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_P15_REPORT.md").write_bytes(render_report(result).replace("\r\n", "\n").encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
