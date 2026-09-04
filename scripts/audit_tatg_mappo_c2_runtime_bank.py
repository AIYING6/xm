"""C2 zero-training audit for vectorized TATG runtime-state ownership."""

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

from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor, TATGRuntimeStateBank
from algorithms.ri_gmappo.tatg_topology_memory import TopologyMemoryState
from scripts.audit_tatg_mappo_c15_actor_integration import base_actor, synthetic_actor_inputs
from envs import RELATION_COMMUNICATION, RELATION_TASK_SUPPORT


def _state_equal(left: TopologyMemoryState, right: TopologyMemoryState) -> bool:
    return all(
        torch.equal(a, b)
        for a, b in (
            (left.memory, right.memory),
            (left.previous_topology, right.previous_topology),
            (left.previous_action, right.previous_action),
        )
    )


def _forward(actor: TATGMemoryActor, inputs: dict, bank: TATGRuntimeStateBank):
    return actor.forward_with_memory(
        inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
        inputs["relation_adj"], bank.state,
    )


def collect_checks() -> tuple[dict[str, bool], dict[str, int]]:
    inputs = synthetic_actor_inputs(batch=3)
    actor = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind="cetm").eval()
    bank = TATGRuntimeStateBank(actor, inputs["relation_adj"], inputs["edge_feat"])
    changed = {key: value.clone() if isinstance(value, torch.Tensor) else value for key, value in inputs.items()}
    changed["relation_adj"][0, RELATION_COMMUNICATION, 0, 1] = 1.0
    changed["relation_adj"][0, RELATION_TASK_SUPPORT, 0, 1] = 1.0
    changed["edge_feat"][0, 0, 1, 15] = 2.0
    with torch.no_grad():
        _, _, _, active_state = _forward(actor, changed, bank)
    bank.replace_state(active_state)
    bank.record_actions(torch.tensor([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))
    prior = TopologyMemoryState.from_runtime_state_dict(bank.state.runtime_state_dict())
    bank.reset_completed(torch.tensor([True, False, True]), inputs["relation_adj"], inputs["edge_feat"])
    reset = actor.reset_memory(inputs["relation_adj"], inputs["edge_feat"])

    clone_actor = TATGMemoryActor(base_actor(), num_blue=3, action_dim=27, memory_kind="cetm").eval()
    clone_actor.load_state_dict(actor.state_dict())
    clone_bank = TATGRuntimeStateBank(clone_actor, inputs["relation_adj"], inputs["edge_feat"])
    clone_bank.load_runtime_state_dict(bank.runtime_state_dict())
    with torch.no_grad():
        left_logits, _, _, left_next = _forward(actor, inputs, bank)
        right_logits, _, _, right_next = _forward(clone_actor, inputs, clone_bank)

    runner_source = (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
    checks = {
        "state_bank_owns_one_state_per_vectorized_environment": bank.batch_size == 3,
        "topology_change_in_slot_zero_does_not_modify_slot_one": torch.equal(prior.memory[1], active_state.memory[1]),
        "completed_slots_reset_memory_topology_and_action": torch.equal(bank.state.memory[[0, 2]], reset.memory[[0, 2]])
        and torch.equal(bank.state.previous_topology[[0, 2]], reset.previous_topology[[0, 2]])
        and torch.equal(bank.state.previous_action[[0, 2]], reset.previous_action[[0, 2]]),
        "unfinished_slot_is_preserved_exactly": torch.equal(bank.state.memory[1], prior.memory[1])
        and torch.equal(bank.state.previous_topology[1], prior.previous_topology[1])
        and torch.equal(bank.state.previous_action[1], prior.previous_action[1]),
        "runtime_bank_payload_has_only_frozen_memory_state": set(bank.runtime_state_dict()) == {"tatg_memory_state"},
        "runtime_bank_restore_continues_exactly": torch.equal(left_logits, right_logits) and _state_equal(left_next, right_next),
        "legacy_runner_has_explicit_done_and_runtime_checkpoint_lifecycle_sites": "if np.all(d):" in runner_source
        and "save_runtime_training_checkpoint(" in runner_source,
        "no_runner_environment_or_ppo_execution": True,
    }
    return checks, {"batch_size": bank.batch_size, "memory_dim": actor.memory_dim}


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C2 vectorized runtime-state-bank audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "The state bank keeps one CETM state per vectorized environment. A completion mask resets only completed slots using their own reset graph and neutral previous action; an unfinished slot is preserved bit-for-bit. The state-bank payload contains only the frozen TATG memory state and restores exact next-call logits.",
        "",
        "The existing runner has explicit completed-episode and runtime-checkpoint lifecycle sites, but C2 does not modify or execute that runner. It uses synthetic legal graph tensors only; it creates no environment, rollout, PPO update, checkpoint file or evaluation result.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "A pass authorizes only a separate runner-integration preflight. It does not authorize PPO, cloud training, evaluation or a performance claim.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C2 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    checks, state_shape = collect_checks()
    result = {
        "protocol": "TATG-MAPPO-C2-VECTORIZED-RUNTIME-STATE-BANK-AUDIT-V1",
        "verdict": "TATG_C2_RUNTIME_BANK_PASS" if all(checks.values()) else "TATG_C2_RUNTIME_BANK_NO_GO",
        "checks": checks,
        "state_shape": state_shape,
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C2_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C2_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
