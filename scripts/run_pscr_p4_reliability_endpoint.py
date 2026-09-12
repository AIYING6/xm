"""Read-only, reliability-stratified endpoint evaluation for PSCR P4 G0.

The P4 task exposes forecast reliability publicly.  Its endpoint therefore
reports the two frozen reliability bands separately rather than averaging them
through the mixed training distribution.  This runner never updates a policy.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_mappo import PSCRContingencyMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts.run_pscr_plain_baseline import deterministic_action
from scripts.run_pscr_p4_baseline import PROTOCOL


RELIABILITY_BANDS = (0.90, 0.25)
METRICS = (
    "return",
    "weighted_service_value",
    "primary_completed",
    "future_completed",
    "primary_expired",
    "future_expired",
    "energy_used",
    "reconfiguration_events",
)


def p4_config(seed: int, reliability: float) -> PSCRConfig:
    """Return the frozen P4 geometry with one fixed public reliability band."""
    return PSCRConfig(
        seed=seed,
        primary_forward_distance=4_500.0,
        future_forward_distance=12_000.0,
        future_lateral_distance=13_000.0,
        contingency_forward_distance=11_000.0,
        future_arrival_step=84,
        future_deadline_urgent_step=117,
        forecast_reliability_choices=(reliability,),
        adversary_profile="bounded_mixture",
    )


def evaluate(agent: PSCRContingencyMAPPO, seed: int, repeats: int = 48) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Evaluate one fixed checkpoint in both frozen public-reliability bands."""
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []
    for reliability in RELIABILITY_BANDS:
        for episode in range(repeats):
            env = PSCRContingencyServiceEnv(p4_config(int(rng.integers(0, 2**31 - 1)), reliability))
            env.reset()
            total = 0.0
            while not env.done:
                _, _, _, reward, _, _ = env.step(deterministic_action(agent, env))
                total += float(reward.mean())
            rows.append({
                "reliability_band": f"r{reliability:.2f}",
                "public_reliability": reliability,
                "episode": episode,
                "return": total,
                **env.terminal_summary(),
            })

    summary: dict[str, float] = {"episodes": float(len(rows))}
    for reliability in RELIABILITY_BANDS:
        prefix = f"r{reliability:.2f}"
        subset = [row for row in rows if row["reliability_band"] == prefix]
        for metric in METRICS:
            summary[f"{prefix}_{metric}"] = float(np.mean([float(row[metric]) for row in subset]))
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True, help="Training seed of the checkpoint.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=48)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError("unexpected checkpoint protocol")
    if payload.get("seed") != args.seed:
        raise ValueError("checkpoint training seed does not match --seed")
    agent = PSCRContingencyMAPPO()
    agent.load_state_dict(payload["state_dict"])
    rows, summary = evaluate(agent, args.seed + 70_000, repeats=args.repeats)

    args.output_root.mkdir(parents=True)
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "protocol": "PSCR-P4-RELIABILITY-ENDPOINT-V1",
        "checkpoint_protocol": PROTOCOL,
        "training_seed": args.seed,
        "reliability_bands": list(RELIABILITY_BANDS),
        "episodes_per_training_seed_band": args.repeats,
        "independent_unit": "training_seed",
        "interpretation_boundary": "Episode rows estimate each fixed policy. Only summaries across independently trained seeds are independent repetitions.",
    }
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "evaluation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
