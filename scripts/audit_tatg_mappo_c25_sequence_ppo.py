"""Zero-training audit of the TATG recurrent PPO interface requirement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "tatg_mappo_c25_sequence_ppo_freeze.json"
RUNNER_PATH = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"


def collect_checks(freeze: dict[str, Any], runner_text: str) -> dict[str, bool]:
    return {
        "existing_rollout_preserves_time_environment_layout": '"obs": np.asarray(obs_buf' in runner_text
        and '"dones": dones_np' in runner_text,
        "existing_actor_update_flattens_time_environment_rows": "batch[\"obs\"].reshape(num_graphs" in runner_text
        and "indices = np.arange(num_graphs)" in runner_text,
        "existing_flat_random_minibatch_is_not_valid_for_temporal_state_replay": "forbidden" in freeze
        and any("random flattened time-environment minibatches" in rule for rule in freeze["forbidden"]),
        "exact_rollout_start_state_is_required": "state_before_rollout" in freeze["collection"],
        "episode_reset_semantics_are_explicit": "episode_boundary" in freeze["collection"],
        "each_ppo_epoch_replays_ordered_sequences": "every PPO epoch replays" in freeze["actor_update"]["epoch_rule"],
        "critic_remains_snapshot_and_ordinary": "existing snapshot centralized critic" in freeze["actor_update"]["critic"],
        "candidate_and_generic_control_share_sequence_runner": "same sequence PPO runner" in freeze["controls"]["generic_gnn_gru"],
        "no_training_or_evaluation_authorized": "actor/critic parameter update during C2.5" in freeze["forbidden"],
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# TATG-MAPPO C2.5 recurrent PPO interface audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "The current PPO implementation correctly stores rollout arrays with time and vectorized-environment axes, but it then flattens and randomly permutes those rows for actor updates. That is valid for the snapshot actor and invalid for CETM: a later graph row would not have the legal preceding state needed to reconstruct its memory.",
        "",
        "The frozen resolution is a full-sequence actor replay: save the exact TATG state at rollout start; replay each environment sequence chronologically for each PPO epoch; apply stored actions only after calculating each log-probability; and reset only completed slots before the next graph. The critic remains the ordinary snapshot centralized critic. The candidate, generic GRU control and delta-zero ablation must use this identical sequence runner.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- `{name}`: `{passed}`" for name, passed in result["checks"].items())
    lines += [
        "",
        "This is a runner-design result, not an algorithm result. It authorizes a separately frozen sequence-runner implementation and same-rollout PPO correctness audit only. No PPO parameter update, environment rollout, evaluation or cloud training was run.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write C2.5 output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    checks = collect_checks(freeze, RUNNER_PATH.read_text(encoding="utf-8"))
    result = {
        "protocol": freeze["protocol"],
        "verdict": freeze["pass"] if all(checks.values()) else "TATG_C25_SEQUENCE_PPO_INTERFACE_NO_GO",
        "checks": checks,
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    output.mkdir(parents=True)
    (output / "TATG_C25_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_C25_REPORT.md").write_bytes(render_report(result).encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
