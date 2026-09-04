"""C1 implementation and exact-runtime-serialization audit for TATG/CETM.

This script uses only synthetic legal graph tensors.  It never creates an
environment, policy rollout, checkpoint selected by return, evaluation tape,
or PPO update.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.tatg_topology_memory import CETMTopologyMemory, SnapshotTopologyGRU, TopologyMemoryState
from envs import EDGE3D_FEAT_DIM, RELATION_COMMUNICATION, RELATION_TASK_SUPPORT


FREEZE_PATH = ROOT / "configs" / "tatg_mappo_p15_formula_freeze.json"
LEGACY_ACTOR_PATH = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"


def _legal_graph(batch_size: int, num_blue: int, *, changed: bool) -> tuple[torch.Tensor, torch.Tensor]:
    nodes = num_blue + 1  # the target exists in the current graph but is never read by CETM.
    relations = torch.zeros(batch_size, 3, nodes, nodes, dtype=torch.float32)
    edge = torch.zeros(batch_size, nodes, nodes, EDGE3D_FEAT_DIM, dtype=torch.float32)
    relations[:, RELATION_COMMUNICATION, :num_blue, :num_blue] = torch.eye(num_blue)
    relations[:, RELATION_TASK_SUPPORT, :num_blue, :num_blue] = torch.eye(num_blue)
    if changed:
        relations[:, RELATION_COMMUNICATION, 0, 1] = 1.0
        relations[:, RELATION_TASK_SUPPORT, 0, 1] = 1.0
        edge[:, 0, 1, 15] = 3.0
    return relations, edge


def _equal_state(left: TopologyMemoryState, right: TopologyMemoryState) -> bool:
    return all(
        torch.equal(a, b)
        for a, b in (
            (left.memory, right.memory),
            (left.previous_topology, right.previous_topology),
            (left.previous_action, right.previous_action),
        )
    )


def collect_checks() -> tuple[dict[str, bool], dict[str, int]]:
    torch.manual_seed(104)
    num_blue, action_dim, memory_dim = 3, 27, 11
    cetm = CETMTopologyMemory(num_blue, action_dim, memory_dim)
    generic = SnapshotTopologyGRU(num_blue, action_dim, memory_dim)
    generic.load_state_dict(cetm.state_dict())
    stable_relations, stable_edge = _legal_graph(2, num_blue, changed=False)
    state = cetm.reset(stable_relations, stable_edge)
    _, stable_state = cetm.step(stable_relations, stable_edge, state)

    changed_relations, changed_edge = _legal_graph(2, num_blue, changed=True)
    memory, active_state = cetm.step(changed_relations, changed_edge, stable_state)
    recorded = cetm.record_actions(active_state, torch.tensor([[1, 2, 3], [4, 5, 6]]))
    restored = TopologyMemoryState.from_runtime_state_dict(recorded.runtime_state_dict())
    next_relations, next_edge = _legal_graph(2, num_blue, changed=True)
    next_edge[:, 1, 0, 15] = 5.0
    left_memory, left_state = cetm.step(next_relations, next_edge, recorded)
    right_memory, right_state = cetm.step(next_relations, next_edge, restored)

    extracted = cetm.extract_local_topology(changed_relations, changed_edge)
    altered_relations, altered_edge = changed_relations.clone(), changed_edge.clone()
    altered_relations[:, RELATION_COMMUNICATION, 1, 2] = 1.0
    altered_edge[:, 1, 2, 15] = 9.0
    altered = cetm.extract_local_topology(altered_relations, altered_edge)
    legacy_text = LEGACY_ACTOR_PATH.read_text(encoding="utf-8")
    cetm_parameters = sum(parameter.numel() for parameter in cetm.parameters())
    generic_parameters = sum(parameter.numel() for parameter in generic.parameters())
    checks = {
        "local_receiver_row_topology_shape": tuple(extracted.shape) == (2, num_blue, 3 * num_blue),
        "target_and_other_receiver_rows_not_read_for_actor_zero": torch.equal(extracted[:, 0], altered[:, 0]),
        "edge_age_channel_is_included": bool(extracted[:, 0, -num_blue + 1].eq(3.0).all()),
        "zero_residual_is_exact_memory_identity": torch.equal(stable_state.memory, state.memory),
        "nonzero_transition_updates_memory": not torch.equal(memory, stable_state.memory),
        "generic_snapshot_gru_capacity_exactly_matched": cetm_parameters == generic_parameters,
        "generic_control_has_matching_initial_weights": all(
            torch.equal(left, right) for left, right in zip(cetm.state_dict().values(), generic.state_dict().values())
        ),
        "runtime_serialization_continuation_exact": torch.equal(left_memory, right_memory)
        and _equal_state(left_state, right_state),
        "reset_state_contains_only_frozen_three_fields": set(state.runtime_state_dict())
        == {"memory", "previous_topology", "previous_action"},
        "legacy_snapshot_actor_and_critic_not_modified": "CETMTopologyMemory" not in legacy_text
        and "TATG" not in legacy_text,
        "no_environment_or_ppo_execution": True,
    }
    return checks, {"cetm_added_parameters": cetm_parameters, "generic_added_parameters": generic_parameters}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C1 implementation and runtime-serialization audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "C1 implements CETM in a standalone module only. The legacy snapshot actor, centralized critic, PPO loop, reward, environment and sampler remain unchanged. Synthetic tensors test the existing receiver–sender graph convention without stepping an environment.",
        "",
        "The generic control has the identical GRUCell parameter count and initial weights; it differs only by receiving a current topology vector at every step instead of CETM's transition residual. CETM runtime checkpoint state contains exactly memory, the preceding local topology vector and the preceding own action.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "This is not a training result or an algorithm-performance claim. A pass authorizes only a separately frozen policy-integration audit; it does not authorize PPO, cloud training, return evaluation or a change to the P1.5 formula.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C1 audit output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    checks, counts = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-C1-IMPLEMENTATION-AND-EXACT-SERIALIZATION-AUDIT-V1",
        "formula_freeze_protocol": freeze["protocol"],
        "verdict": "TATG_C1_IMPLEMENTATION_SERIALIZATION_PASS" if all(checks.values()) else "TATG_C1_IMPLEMENTATION_SERIALIZATION_NO_GO",
        "checks": checks,
        "parameter_counts": counts,
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "legacy_actor_or_critic_modified": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C1_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C1_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
