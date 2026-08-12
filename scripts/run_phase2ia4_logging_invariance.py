"""One-episode ON/OFF instrumentation invariance test on a development checkpoint."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_ri_gmappo_3d import evaluate


def args(checkpoint: Path, trace=None):
    return SimpleNamespace(checkpoint=checkpoint, method="full_gate", episodes=1, eval_batch_size=1, seed=101,
        base_seed=411000, episode_id_base=411000, target_policy="straight", communication_range_scale=1.0,
        communication_dropout_prob=.30, message_delay_steps=2, radar_dropout_prob=0.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, target_prior_position=(10000., 0., 5000.), max_target_message_age_steps=80,
        min_target_confidence=.20, failed_blue_agent=1, node_failure_start_step=25, node_failure_duration_steps=80,
        min_success_step=0, attack_hold_steps=4, stochastic=False, allow_random_policy=False, hidden_dim=64,
        role_dim=8, intent_dim=8, graph_encoder="multi_relation", graph_relation_ablation="none",
        graph_message_ablation="none", graph_input_ablation="none", role_gate_mode="relation_conditioned",
        multi_relation_global_residual_weight=1.0, device="cuda", timestep_trace_path=trace)


def main():
    checkpoint = ROOT / "results/development/role_gate_phase2ia2/runs/full_gate/seed101/actor_critic_latest.pt"
    with tempfile.TemporaryDirectory(prefix="phase2ia4_trace_") as temp:
        trace = Path(temp) / "trace.csv"
        off = evaluate(args(checkpoint))
        on = evaluate(args(checkpoint, trace))
        keys = [k for k in off[0] if k not in {"checkpoint"}]
        mismatches = [k for k in keys if str(off[0].get(k)) != str(on[0].get(k))]
        result = {"status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches,
                  "off_trace_rows": 0, "on_trace_rows": sum(1 for _ in trace.open(encoding="utf-8")) - 1}
        print(json.dumps(result, indent=2))
        if mismatches:
            raise SystemExit(1)


if __name__ == "__main__": main()
