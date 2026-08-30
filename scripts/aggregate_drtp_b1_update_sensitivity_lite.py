"""Zero-environment analysis of completed B1 stochastic continuation branches.

This intentionally does not read, resume, or interpret the aborted full-tape
evaluation.  It characterizes only update-level sensitivity already generated
by the frozen 64-update B1 branches.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
import statistics
import sys

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_phase_fl_single as fl  # noqa: E402
from run_drtp_b1_update_sensitivity_branch import ARMS, BRANCHES, COHORTS, FAMILIES  # noqa: E402


PROTOCOL = "DRTP-B1-UPDATE-SENSITIVITY-LITE-V1"
HORIZONS = (("u001", 1954), ("u004", 1957), ("u016", 1969), ("u064", 2017))
POLICY_HORIZONS = {"u016", "u064"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"refusing an empty B1-Lite product: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def actor_vector(state: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.cat([
        state[key].detach().cpu().float().reshape(-1)
        for key in sorted(state)
        if key.startswith("actor.") and state[key].is_floating_point()
    ])


def median_pairwise_cosine_distance(vectors: list[torch.Tensor]) -> float:
    values = []
    for left, right in itertools.combinations(vectors, 2):
        denominator = float(torch.linalg.vector_norm(left) * torch.linalg.vector_norm(right))
        cosine = float(torch.dot(left, right) / denominator) if denominator > 0.0 else 1.0
        values.append(1.0 - max(-1.0, min(1.0, cosine)))
    return statistics.median(values)


def symmetric_js(left: torch.Tensor, right: torch.Tensor) -> float:
    eps = torch.finfo(left.dtype).eps
    left, right = left.clamp_min(eps), right.clamp_min(eps)
    middle = 0.5 * (left + right)
    value = 0.5 * (
        (left * (left.log() - middle.log())).sum(-1)
        + (right * (right.log() - middle.log())).sum(-1)
    )
    return float(value.mean())


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
    probabilities = torch.softmax(logits, dim=-1).detach().cpu()
    del agent
    return probabilities


def branch_prefix(log: list[dict[str, str]], end_update: int) -> list[dict[str, str]]:
    prefix = [row for row in log if int(row["update"]) <= end_update]
    if not prefix:
        raise RuntimeError(f"missing B1 branch updates through {end_update}")
    return prefix


def metric_mean(rows: list[dict[str, str]], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows]))


def metric_max(rows: list[dict[str, str]], key: str) -> float:
    return max(float(row[key]) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")

    report = args.output_root / "diagnostics" / "b1_lite_update_sensitivity"
    if report.exists():
        raise FileExistsError(f"refusing B1-Lite rerun: {report}")
    report.mkdir(parents=True, exist_ok=False)

    sensitivity_rows: list[dict] = []
    dynamic_rows: list[dict] = []
    for cohort, seeds in COHORTS.items():
        for arm in ARMS:
            for seed in seeds:
                runtime_path = args.assets_root / cohort / arm / f"seed{seed}" / "actor_critic_runtime_state_milestone_500k.pt"
                runtime = torch.load(runtime_path, map_location="cpu", weights_only=False)
                source_actor = actor_vector(runtime["model_state"])
                for family in FAMILIES:
                    branch_logs = {}
                    for branch in BRANCHES:
                        run = args.output_root / "branches" / cohort / arm / f"seed{seed}" / family / f"branch{branch}"
                        manifest = json.loads((run / "branch_manifest.json").read_text(encoding="utf-8"))
                        if manifest.get("status") != "completed" or manifest.get("branch_updates") != 64:
                            raise RuntimeError(f"invalid completed B1 branch: {run}")
                        branch_logs[branch] = read_csv(run / "train_log.csv")
                    for horizon, end_update in HORIZONS:
                        vectors, probabilities = [], []
                        for branch in BRANCHES:
                            run = args.output_root / "branches" / cohort / arm / f"seed{seed}" / family / f"branch{branch}"
                            checkpoint = run / f"actor_critic_milestone_{horizon}.pt"
                            state = torch.load(checkpoint, map_location="cpu", weights_only=True)
                            vectors.append(actor_vector(state) - source_actor)
                            prefix = branch_prefix(branch_logs[branch], end_update)
                            dynamic_rows.append({
                                "cohort": cohort, "arm": arm, "seed": seed, "family": family,
                                "branch": branch, "horizon": horizon, "end_update": end_update,
                                "mean_approx_kl": metric_mean(prefix, "approx_kl"),
                                "max_approx_kl": metric_max(prefix, "approx_kl"),
                                "mean_value_loss": metric_mean(prefix, "value_loss"),
                                "mean_explained_variance": metric_mean(prefix, "explained_variance"),
                                "mean_advantage_std": metric_mean(prefix, "advantage_std"),
                                "mean_train_reward": metric_mean(prefix, "train_avg_reward"),
                            })
                            if horizon in POLICY_HORIZONS:
                                probabilities.append(policy_probabilities(checkpoint, seed, runtime))
                        row = {
                            "cohort": cohort, "arm": arm, "seed": seed, "family": family,
                            "horizon": horizon, "end_update": end_update,
                            "actor_delta_cosine_distance_median": median_pairwise_cosine_distance(vectors),
                            "policy_js_median": "",
                            "environment_episodes_run": 0,
                            "independent_unit": "source_training_seed",
                            "technical_repetitions_are_not_independent_n": True,
                        }
                        if probabilities:
                            row["policy_js_median"] = statistics.median(
                                symmetric_js(left, right) for left, right in itertools.combinations(probabilities, 2)
                            )
                        sensitivity_rows.append(row)

    write_csv(report / "source_seed_update_sensitivity.csv", sensitivity_rows)
    write_csv(report / "branch_training_dynamics.csv", dynamic_rows)
    inventory = {
        "status": "B1_LITE_UPDATE_SENSITIVITY_READY_FOR_REVIEW",
        "protocol": PROTOCOL,
        "full_tape_evaluation_status": "ABORTED_FOR_COMPUTE; partial rows are not used",
        "source_checkpoints": 40,
        "completed_branch_trajectories": 320,
        "branch_updates": 64,
        "environment_episodes_run_by_this_analysis": 0,
        "mechanism_declared": False,
        "algorithm_modification_authorized": False,
        "mainline_a_modified": False,
    }
    (report / "B1_LITE_DECISION.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    (report / "B1_LITE_REPORT.md").write_text(
        "# B1-Lite update-sensitivity analysis\n\n"
        "**Status:** `B1_LITE_UPDATE_SENSITIVITY_READY_FOR_REVIEW`.\n\n"
        "This is a zero-environment analysis of the completed frozen B1 branches. "
        "The aborted 64,000-episode full-tape evaluation is excluded. Results are descriptive "
        "and cannot declare an update-reliability mechanism or authorize a new algorithm.\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
