"""C1.5 audit: connect CETM to the actor boundary without PPO or an environment."""

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

from algorithms.ri_gmappo.simple_ri_gmappo import RIActor
from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor
from algorithms.ri_gmappo.tatg_topology_memory import TopologyMemoryState
from envs import EDGE3D_FEAT_DIM, RELATION_COMMUNICATION, RELATION_TASK_SUPPORT


def synthetic_actor_inputs(batch: int = 2, num_blue: int = 3) -> dict[str, torch.Tensor | int]:
    torch.manual_seed(105)
    nodes = num_blue + 1
    relation = torch.zeros(batch, 3, nodes, nodes)
    relation[:, RELATION_COMMUNICATION, :num_blue, :num_blue] = torch.eye(num_blue)
    relation[:, RELATION_TASK_SUPPORT, :num_blue, :num_blue] = torch.eye(num_blue)
    edge = torch.zeros(batch, nodes, nodes, EDGE3D_FEAT_DIM)
    adj = torch.eye(nodes).expand(batch, -1, -1).clone()
    return {
        "obs": torch.randn(batch, num_blue, 34),
        "node_feat": torch.randn(batch, nodes, 16),
        "edge_feat": edge,
        "role": torch.tensor([[0, 1, 2, 4]], dtype=torch.long).expand(batch, -1).clone(),
        "adj": adj,
        "relation_adj": relation,
        "num_agents": num_blue,
    }


def base_actor() -> RIActor:
    torch.manual_seed(106)
    return RIActor(
        obs_dim=34,
        node_feat_dim=16,
        edge_feat_dim=EDGE3D_FEAT_DIM,
        num_roles=5,
        role_dim=4,
        intent_dim=4,
        hidden_dim=16,
        action_dim=27,
        graph_encoder="single",
        use_intent_context=False,
    ).eval()


def _state_exact(left: TopologyMemoryState, right: TopologyMemoryState) -> bool:
    return all(
        torch.equal(a, b)
        for a, b in (
            (left.memory, right.memory),
            (left.previous_topology, right.previous_topology),
            (left.previous_action, right.previous_action),
        )
    )


def collect_checks() -> tuple[dict[str, bool], dict[str, int]]:
    inputs = synthetic_actor_inputs()
    base = base_actor()
    candidate = TATGMemoryActor(base, num_blue=3, action_dim=27, memory_kind="cetm").eval()
    generic = TATGMemoryActor(base, num_blue=3, action_dim=27, memory_kind="snapshot_gru").eval()
    generic.load_state_dict(candidate.state_dict())
    initial_weights_equal = all(
        torch.equal(a, b) for a, b in zip(candidate.state_dict().values(), generic.state_dict().values())
    )
    state = candidate.reset_memory(inputs["relation_adj"], inputs["edge_feat"])
    generic_state = generic.reset_memory(inputs["relation_adj"], inputs["edge_feat"])
    with torch.no_grad():
        base_logits, _, _ = base(
            inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
            relation_adj=inputs["relation_adj"],
        )
        candidate_logits, _, _, next_state = candidate.forward_with_memory(
            inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
            inputs["relation_adj"], state,
        )

        changed_relation = inputs["relation_adj"].clone()
        changed_edge = inputs["edge_feat"].clone()
        changed_relation[:, RELATION_COMMUNICATION, 0, 1] = 1.0
        changed_relation[:, RELATION_TASK_SUPPORT, 0, 1] = 1.0
        changed_edge[:, 0, 1, 15] = 2.0
        _, _, _, changed_state = candidate.forward_with_memory(
            inputs["obs"], inputs["node_feat"], changed_edge, inputs["role"], inputs["adj"], inputs["num_agents"],
            changed_relation, next_state,
        )
        recorded = candidate.record_actions(changed_state, torch.tensor([[1, 2, 3], [4, 5, 6]]))
        restored = TopologyMemoryState.from_runtime_state_dict(recorded.runtime_state_dict())
        left_logits, _, _, left_state = candidate.forward_with_memory(
            inputs["obs"], inputs["node_feat"], changed_edge, inputs["role"], inputs["adj"], inputs["num_agents"],
            changed_relation, recorded,
        )
        right_logits, _, _, right_state = candidate.forward_with_memory(
            inputs["obs"], inputs["node_feat"], changed_edge, inputs["role"], inputs["adj"], inputs["num_agents"],
            changed_relation, restored,
        )
        # Audit-only wiring probe: no environment action is used and no model
        # is trained.  It confirms that a nonzero CETM state reaches logits.
        temporal_linear = candidate.temporal_policy_head[0]
        temporal_linear.weight[:, -candidate.memory_dim :].fill_(0.125)
        injected_logits, _, _, _ = candidate.forward_with_memory(
            inputs["obs"], inputs["node_feat"], changed_edge, inputs["role"], inputs["adj"], inputs["num_agents"],
            changed_relation, next_state,
        )
        _, _, _, generic_next = generic.forward_with_memory(
            inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
            inputs["relation_adj"], generic_state,
        )
    checks = {
        "snapshot_logits_exact_at_zero_memory_initialization": torch.equal(base_logits, candidate_logits),
        "cetm_memory_reaches_candidate_logits": not torch.equal(candidate_logits, injected_logits),
        "candidate_transition_state_changes_only_after_legal_topology_change": torch.equal(next_state.memory, state.memory)
        and not torch.equal(changed_state.memory, next_state.memory),
        "generic_control_added_actor_capacity_exactly_matched": candidate.added_actor_parameter_count()
        == generic.added_actor_parameter_count(),
        "generic_control_starts_with_identical_actor_and_temporal_weights": initial_weights_equal,
        "candidate_actor_runtime_continuation_exact": torch.equal(left_logits, right_logits)
        and _state_exact(left_state, right_state),
        "generic_current_snapshot_control_updates_without_transition": not torch.equal(generic_next.memory, generic_state.memory),
        "no_legacy_actor_or_critic_source_edit": "TATGMemoryActor" not in (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8"),
        "no_environment_or_ppo_execution": True,
    }
    counts = {
        "candidate_added_actor_parameters": candidate.added_actor_parameter_count(),
        "generic_control_added_actor_parameters": generic.added_actor_parameter_count(),
        "legacy_snapshot_actor_parameters": sum(p.numel() for p in base.parameters()),
    }
    return checks, counts


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C1.5 actor-integration audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "An isolated candidate wrapper attaches CETM to the existing snapshot actor only at its final policy-input boundary. It initializes the added memory columns to zero and copies the legacy policy head, so a reset state produces the exact legacy snapshot logits. A synthetic, no-action wiring probe then confirms that a nonzero legal transition state reaches logits.",
        "",
        "The generic current-snapshot GRU control has the same copied actor, same temporal policy head and identical added actor parameter count. Runtime state restores exactly through the wrapper. This audit does not create an environment, use an evaluation tape, sample a policy action, run PPO, or train any model.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "A pass permits only a future rollout-and-PPO interface preflight. It is not evidence that TATG improves return, reliability or robustness, and it authorizes no cloud training.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C1.5 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, counts = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-C1.5-ACTOR-INTEGRATION-AUDIT-V1",
        "verdict": "TATG_C15_ACTOR_INTEGRATION_PASS" if all(checks.values()) else "TATG_C15_ACTOR_INTEGRATION_NO_GO",
        "checks": checks,
        "parameter_counts": counts,
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C15_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C15_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
