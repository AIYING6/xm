"""Run exactly one frozen RSG-1 development training/evaluation cell."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_phase_rsg1_development_smoke import (
    METHODS, PROTOCOL, EPISODES, NUM_ENVS, ROLLOUT_STEPS, SEEDS,
    TAPE_START, UPDATES, build_agent, evaluate_episode, sha256,
    training_config, write_csv,
)
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo


def run_one(method_name: str, seed: int, output_root: Path) -> dict:
    method = METHODS[method_name]
    run_dir = output_root / "runs" / method_name / f"seed{seed}"
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite run output: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(method, seed, run_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "method": method_name,
        "seed": seed, "updates": UPDATES, "num_envs": NUM_ENVS,
        "rollout_steps": ROLLOUT_STEPS,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "resume": False,
        "early_stopping": False, "canonical_data_used": False,
        "graph_encoder": method["graph_encoder"], "config": cfg.__dict__,
    }
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    train_ri_gmappo(cfg)
    checkpoint = run_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)

    agent = build_agent(method, checkpoint, seed)
    raw, all_bias = [], []
    for episode in range(EPISODES):
        episode_id = TAPE_START + episode
        for condition in ("nominal", "relay_failure"):
            row, bias = evaluate_episode(agent, method_name, seed, episode_id, condition)
            raw.append(row)
            all_bias.extend(
                [{**item, "method": method_name, "train_seed": seed,
                  "development_episode_id": episode_id} for item in bias]
            )
    write_csv(run_dir / "raw_episode_metrics.csv", raw)
    nominal = {
        row["development_episode_id"]: row
        for row in raw if row["condition"] == "nominal"
    }
    paired = [
        {
            "protocol": PROTOCOL, "development_episode_id": row["development_episode_id"],
            "method": method_name, "train_seed": seed,
            "J_nominal": nominal[row["development_episode_id"]]["J"],
            "J_failure": row["J"],
            "delta_J": nominal[row["development_episode_id"]]["J"] - row["J"],
            "success_nominal": nominal[row["development_episode_id"]]["success_at_horizon"],
            "success_failure": row["success_at_horizon"],
            "failure_exposed": row["failure_exposed"],
        }
        for row in raw if row["condition"] == "relay_failure"
    ]
    write_csv(run_dir / "paired_metrics.csv", paired)
    manifest.update({
        "status": "completed", "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint), "evaluation_tape_start": TAPE_START,
        "evaluation_episodes_per_condition": EPISODES,
        "evaluation_success_metric": "success_at_horizon_min_success_step_260",
        "raw_episode_rows": len(raw), "bias_telemetry_rows": len(all_bias),
    })
    write_csv(run_dir / "bias_telemetry.csv", all_bias)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "completed", "method": method_name, "seed": seed,
                      "run_dir": str(run_dir), "checkpoint_sha256": manifest["checkpoint_sha256"]},
                     indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=tuple(METHODS), required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output-root", type=Path,
                        default=Path("results/development/phase_rsg1_development_smoke"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: single RSG-1 run requires explicit --execute")
    run_one(args.method, args.seed, args.output_root)


if __name__ == "__main__":
    main()
