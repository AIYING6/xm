"""Construct seed-level B1 update-sensitivity evidence without declaring a mechanism."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs  # noqa: E402
import run_phase_fl_single as fl  # noqa: E402
from run_drtp_b1_update_sensitivity_branch import ARMS, BRANCHES, COHORTS, FAMILIES  # noqa: E402


HORIZONS = ("u001", "u004", "u016", "u064")
PERTURBATIONS = ("F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FREEZE = ROOT / "configs" / "drtp_b1_update_sensitivity_freeze.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing empty B1 product: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def median_pairwise_cosine_distance(vectors: list[torch.Tensor]) -> float:
    values = []
    for left, right in itertools.combinations(vectors, 2):
        denom = float(torch.linalg.vector_norm(left) * torch.linalg.vector_norm(right))
        cosine = float(torch.dot(left, right) / denom) if denom > 0.0 else 1.0
        values.append(1.0 - max(-1.0, min(1.0, cosine)))
    return statistics.median(values)


def symmetric_js(left: torch.Tensor, right: torch.Tensor) -> float:
    eps = torch.finfo(left.dtype).eps
    left, right = left.clamp_min(eps), right.clamp_min(eps)
    middle = 0.5 * (left + right)
    value = 0.5 * ((left * (left.log() - middle.log())).sum(-1) + (right * (right.log() - middle.log())).sum(-1))
    return float(value.mean())


def actor_vector(state: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.cat([
        state[key].detach().cpu().float().reshape(-1)
        for key in sorted(state) if key.startswith("actor.") and state[key].is_floating_point()
    ])


def policy_probabilities(checkpoint: Path, seed: int, runtime: dict) -> torch.Tensor:
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    device = next(agent.parameters()).device
    graph = runtime["graph_obs"]
    with torch.no_grad():
        logits, *_ = agent.actor(
            torch.as_tensor(runtime["obs"], dtype=torch.float32, device=device),
            torch.as_tensor(graph["node_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(graph["edge_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(graph["role"], dtype=torch.long, device=device),
            torch.as_tensor(graph["adj"], dtype=torch.float32, device=device),
            agent.num_agents,
            relation_adj=torch.as_tensor(graph["relation_adj"], dtype=torch.float32, device=device),
            intent_label=torch.as_tensor(graph["intent_label"], dtype=torch.long, device=device),
        )
    return torch.softmax(logits, dim=-1).detach().cpu()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")
    report = args.output_root / "diagnostics" / "b1_update_sensitivity_gate"
    if report.exists():
        raise FileExistsError(f"refusing B1 aggregate rerun: {report}")
    report.mkdir(parents=True, exist_ok=False)
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    eval_rows = read_csv(args.output_root / "evaluations" / "branch_horizons" / "per_branch_condition_summary.csv")
    eval_index = defaultdict(list)
    for row in eval_rows:
        eval_index[(row["cohort"], row["arm"], int(row["seed"]), row["family"], int(row["branch"]), row["horizon"])].append(row)

    sensitivity, branch_dynamics = [], []
    for cohort, seeds in COHORTS.items():
        for arm in ARMS:
            for seed in seeds:
                source_path = args.assets_root / cohort / arm / f"seed{seed}" / "actor_critic_runtime_state_milestone_500k.pt"
                runtime = torch.load(source_path, map_location="cpu", weights_only=False)
                source_actor = actor_vector(runtime["model_state"])
                for family in FAMILIES:
                    for horizon in HORIZONS:
                        deltas, probabilities, endpoint_values = [], [], []
                        for branch in BRANCHES:
                            run = args.output_root / "branches" / cohort / arm / f"seed{seed}" / family / f"branch{branch}"
                            checkpoint = run / f"actor_critic_milestone_{horizon}.pt"
                            state = torch.load(checkpoint, map_location="cpu", weights_only=True)
                            deltas.append(actor_vector(state) - source_actor)
                            probabilities.append(policy_probabilities(checkpoint, seed, runtime))
                            log = read_csv(run / "train_log.csv")
                            end_update = {"u001": 1954, "u004": 1957, "u016": 1969, "u064": 2017}[horizon]
                            prefix = [row for row in log if int(row["update"]) <= end_update]
                            branch_dynamics.append({
                                "cohort": cohort, "arm": arm, "seed": seed, "family": family,
                                "branch": branch, "horizon": horizon,
                                "mean_approx_kl": float(np.mean([float(row["approx_kl"]) for row in prefix])),
                                "max_approx_kl": max(float(row["approx_kl"]) for row in prefix),
                                "mean_value_loss": float(np.mean([float(row["value_loss"]) for row in prefix])),
                                "mean_explained_variance": float(np.mean([float(row["explained_variance"]) for row in prefix])),
                                "mean_advantage_std": float(np.mean([float(row["advantage_std"]) for row in prefix])),
                                "mean_train_reward": float(np.mean([float(row["train_avg_reward"]) for row in prefix])),
                            })
                            if horizon in {"u016", "u064"}:
                                cell = eval_index[(cohort, arm, seed, family, branch, horizon)]
                                endpoint_values.append(float(np.mean([
                                    float(row["J"]) for row in cell if row["condition"] in PERTURBATIONS
                                ])))
                        js_values = [symmetric_js(left, right) for left, right in itertools.combinations(probabilities, 2)]
                        sensitivity.append({
                            "cohort": cohort, "arm": arm, "seed": seed, "family": family, "horizon": horizon,
                            "actor_delta_cosine_distance_median": median_pairwise_cosine_distance(deltas),
                            "policy_js_median": statistics.median(js_values),
                            "J_pert_mean_branch_sd": statistics.stdev(endpoint_values) if len(endpoint_values) > 1 else "",
                            "frozen_final_paired_gain": freeze["frozen_final_paired_J_robust_gain"][str(seed)],
                            "source_outcome_class": (
                                "catastrophic" if seed in freeze["frozen_catastrophic_drtp_seeds"]
                                else "adverse" if freeze["frozen_final_paired_J_robust_gain"][str(seed)] <= 0.0
                                else "positive"
                            ),
                            "independent_unit": "source_training_seed",
                        })
    write_csv(report / "source_seed_sensitivity_summary.csv", sensitivity)
    write_csv(report / "branch_training_dynamics.csv", branch_dynamics)
    inventory = {
        "status": "B1_UPDATE_RELIABILITY_GATE_READY_FOR_REVIEW",
        "source_checkpoints": 40,
        "branch_trajectories": 320,
        "branch_updates": 64,
        "training_environment_steps": 5_242_880,
        "mechanism_declared": False,
        "algorithm_modification_authorized": False,
        "independent_unit": "source_training_seed",
        "technical_repetitions_are_not_independent_n": True,
        "mainline_a_modified": False,
    }
    (report / "B1_GATE_DECISION.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (report / "B1_GATE_REPORT.md").write_text(
        "# DRTP B1 update-reliability mechanism gate\n\n"
        "**Status:** `B1_UPDATE_RELIABILITY_GATE_READY_FOR_REVIEW`.\n\n"
        "The automatic stage verifies all 320 frozen branches and constructs source-seed-level sensitivity products. "
        "It does not declare a mechanism and does not authorize Reliable-DRTP. Human review must apply every conjunctive "
        "discovery, matched-UTR, positive-control, held-out-cohort, temporal-precedence, and leave-one-branch-out requirement.\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
