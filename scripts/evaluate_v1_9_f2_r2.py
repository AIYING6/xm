"""Run the frozen v1.9 F2-R2 confirmatory episode matrix exactly once.

This script contains no optimization and never calls the training loop.  It
loads only the immutable F1-selected checkpoints after the zero-result launch
preflight has succeeded.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    checkpoint_model_state,
    eval_policy,
    make_env,
    summarize_validation_event_records,
)
from f2_r2_common import (  # noqa: E402
    F2_PROTOCOL,
    METHOD_SPECS,
    sha256_file,
    stable_json_sha256,
    write_new_json,
)


RECORD_FIELDS = [
    "episode_seed", "failure_onset_step", "event_observed",
    "first_stable_establishment_step", "event_time", "termination_reason",
    "terminal_failure_observed", "terminal_failure_time", "terminal_step",
    "physical_event_observed", "first_stable_physical_engagement_step", "physical_event_time",
]


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def f2_config(method: str, encoder: str, hidden_dim: int, training_seed: int, device: str) -> RIGMAPPOConfig:
    """Explicitly reproduce every F1 environment-side constant used by F2."""
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=training_seed,
        hidden_dim=hidden_dim,
        role_dim=8,
        intent_dim=8,
        graph_encoder=encoder,
        ppo_epochs=4,
        target_policy="mixed",
        target_speed=0.75,
        communication_radius=8.0,
        communication_range_scale=1.0,
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        radar_dropout_prob=0.10,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        max_target_message_age_steps=80,
        min_target_confidence=0.20,
        attack_hold_steps=4,
        min_success_step=80,
        failed_blue_agent=1,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        eval_episodes=300,
        eval_base_seed=510_000,
        device=device,
        method_label=method,
        protocol_version=F2_PROTOCOL,
        run_id=f"v1_9_f2_r2_{method}_seed{training_seed}",
    )


def build_agent(cfg: RIGMAPPOConfig) -> RIGMAPPOAgent:
    """Construct the exact policy shape without instantiating an F2 episode."""
    sample_env = make_env(cfg, seed=0, training=False)
    _, _, sample_graph = sample_env.reset()
    return RIGMAPPOAgent(
        obs_dim=sample_env.obs_dim,
        node_feat_dim=sample_graph["node_feat"].shape[-1],
        edge_feat_dim=sample_graph["edge_feat"].shape[-1],
        share_obs_dim=sample_env.share_obs_dim,
        action_dim=sample_env.action_dim,
        num_agents=sample_env.num_agents,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        use_intent_context=False,
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        num_roles=max(4, int(sample_graph["role"].max()) + 1),
    ).to(torch.device(cfg.device))


def load_exact_f1_checkpoint(
    agent: RIGMAPPOAgent,
    checkpoint_path: Path,
    plan: dict,
    f1_source_commit: str,
    device: torch.device,
) -> None:
    if sha256_file(checkpoint_path) != plan["checkpoint_sha256"]:
        raise RuntimeError(f"F2 checkpoint SHA256 changed: {checkpoint_path}")
    payload = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if not isinstance(payload, dict) or "metadata" not in payload:
        raise RuntimeError(f"F2 selected checkpoint lacks immutable metadata: {checkpoint_path}")
    metadata = payload["metadata"]
    if (
        metadata.get("method") != plan["method"]
        or int(metadata.get("training_seed", -1)) != int(plan["training_seed"])
        or int(metadata.get("update", -1)) != int(plan["selected_update"])
        or metadata.get("git_commit") != f1_source_commit
    ):
        raise RuntimeError(f"F2 selected checkpoint provenance mismatch: {checkpoint_path}")
    agent.load_state_dict(checkpoint_model_state(payload), strict=True)


def write_run_records(run_dir: Path, records: list[dict]) -> Path:
    records_path = run_dir / "episode_event_records.csv"
    if records_path.exists():
        raise FileExistsError(f"refusing to overwrite F2 run records: {run_dir}")
    with records_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS)
        writer.writeheader()
        writer.writerows([{field: row[field] for field in RECORD_FIELDS} for row in records])
    return records_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--f1-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--expected-f1-source-commit", required=True)
    parser.add_argument("--expected-evaluator-source-commit", required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if current_commit() != args.expected_evaluator_source_commit:
        raise SystemExit("F2 evaluator source commit mismatch")
    if not torch.cuda.is_available() and args.device.startswith("cuda"):
        raise SystemExit("F2 requires the frozen CUDA execution path")
    plan_path = args.out_root / "F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json"
    if not plan_path.exists():
        raise SystemExit("F2 zero-result launch preflight is missing")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (
        plan.get("status") != "F2_R2_LAUNCH_PREFLIGHT_PASS__CONFIRMATORY_NOT_YET_ACCESSED"
        or plan.get("f1_source_commit") != args.expected_f1_source_commit
        or plan.get("f2_evaluator_source_commit") != args.expected_evaluator_source_commit
        or plan.get("confirmatory_heldout_accessed") is not False
    ):
        raise SystemExit("F2 launch preflight provenance mismatch")
    specs = {method: (encoder, hidden_dim) for method, encoder, hidden_dim in METHOD_SPECS}
    execution_runs = []
    for index, checkpoint_plan in enumerate(plan["checkpoint_plans"], 1):
        method = str(checkpoint_plan["method"])
        encoder, hidden_dim = specs[method]
        if encoder != checkpoint_plan["encoder"] or int(hidden_dim) != int(checkpoint_plan["hidden_dim"]):
            raise RuntimeError(f"F2 method/encoder specification mismatch for {method}")
        cfg = f2_config(method, encoder, hidden_dim, int(checkpoint_plan["training_seed"]), args.device)
        if list(range(cfg.eval_base_seed, cfg.eval_base_seed + cfg.eval_episodes)) != checkpoint_plan["paired_episode_ids"]:
            raise RuntimeError(f"F2 episode pairing mismatch for {method}/seed{cfg.seed}")
        checkpoint_path = args.f1_root / checkpoint_plan["checkpoint_relative_path"]
        agent = build_agent(cfg)
        load_exact_f1_checkpoint(agent, checkpoint_path, checkpoint_plan, args.expected_f1_source_commit, torch.device(args.device))
        _, records = eval_policy(agent, cfg, base_seed=cfg.eval_base_seed, return_event_records=True)
        if [int(row["episode_seed"]) for row in records] != checkpoint_plan["paired_episode_ids"]:
            raise RuntimeError(f"F2 evaluator returned an incomplete or reordered episode bank for {method}/seed{cfg.seed}")
        metrics = summarize_validation_event_records(records)
        run_dir = args.out_root / f"{method}_seed{cfg.seed}"
        run_dir.mkdir(parents=True, exist_ok=False)
        records_path = write_run_records(run_dir, records)
        summary_path = run_dir / "summary.json"
        summary = {
            "protocol_version": F2_PROTOCOL,
            "f1_source_commit": args.expected_f1_source_commit,
            "f2_evaluator_source_commit": args.expected_evaluator_source_commit,
            "method": method,
            "training_seed": cfg.seed,
            "selected_update": int(checkpoint_plan["selected_update"]),
            "checkpoint_relative_path": checkpoint_plan["checkpoint_relative_path"],
            "checkpoint_sha256": checkpoint_plan["checkpoint_sha256"],
            "episodes": cfg.eval_episodes,
            "episode_seed_base": cfg.eval_base_seed,
            "episode_seed_list_sha256": stable_json_sha256(checkpoint_plan["paired_episode_ids"]),
            "episode_records_sha256": sha256_file(records_path),
            **{key[5:] if key.startswith("eval_") else key: float(value) for key, value in metrics.items()},
        }
        write_new_json(summary_path, summary)
        execution_runs.append({
            "method": method,
            "training_seed": cfg.seed,
            "selected_update": int(checkpoint_plan["selected_update"]),
            "checkpoint_sha256": checkpoint_plan["checkpoint_sha256"],
            "episode_records_path": str(records_path.relative_to(args.out_root)),
            "episode_records_sha256": sha256_file(records_path),
            "summary_path": str(summary_path.relative_to(args.out_root)),
            "summary_sha256": sha256_file(summary_path),
        })
        print(f"F2 progress: {index}/24 checkpoint evaluations complete", flush=True)

    execution = {
        "status": "F2_R2_CONFIRMATORY_EVALUATION_COMPLETE__ANALYSIS_PENDING",
        "protocol_version": F2_PROTOCOL,
        "f1_source_commit": args.expected_f1_source_commit,
        "f2_evaluator_source_commit": args.expected_evaluator_source_commit,
        "launch_preflight_sha256": sha256_file(plan_path),
        "confirmatory_heldout_accessed": True,
        "runs": execution_runs,
    }
    write_new_json(args.out_root / "F2_R2_EXECUTION_MANIFEST.json", execution)
    print("F2 confirmatory rollouts complete; no method metrics were printed", flush=True)


if __name__ == "__main__":
    main()
