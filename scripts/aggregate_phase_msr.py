"""Aggregate Stage-MSR mixed-policy training and six-checkpoint evaluation."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


GROUPS = ("fl_nominal_expert", "fl_f0_expert", "mixed50_sg")
SEEDS = (1801, 1802)
MILESTONES = {1172: "300k", 1953: "500k", 2930: "750k", 3907: "1m"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def summary(group: str, seed: int, paired: list[dict[str, str]]) -> dict:
    return {
        "group": group, "seed": seed,
        "J_nominal": mean(paired, "J_nominal"), "J_failure": mean(paired, "J_failure"),
        "Delta_J": mean(paired, "delta_J"),
        "collision_failure": mean(paired, "collision_failure"),
        "timeout_failure": mean(paired, "timeout_failure"),
        "constraint_failure": mean(paired, "constraint_failure"),
        "failure_exposure": mean(paired, "failure_exposed"),
        "episode_length_nominal": mean(paired, "episode_length_nominal"),
        "episode_length_failure": mean(paired, "episode_length_failure"),
        "path_switch_count_failure": mean(paired, "path_switch_count_failure"),
        "direct_path_fraction_failure": mean(paired, "direct_path_fraction_failure"),
        "relay_path_fraction_failure": mean(paired, "relay_path_fraction_failure"),
        "task_support_fraction_failure": mean(paired, "task_support_fraction_failure"),
        "legal_information_fraction_failure": mean(paired, "legal_information_fraction_failure"),
        "mean_cache_age_failure": mean(paired, "mean_cache_age_failure"),
        "traveled_distance_failure": mean(paired, "traveled_distance_failure"),
        "control_effort_failure": mean(paired, "control_effort_failure"),
    }


def verify_evaluation(root: Path, group: str, seed: int, tape_hash: str) -> tuple[dict, list[dict[str, str]]]:
    path = root / "evaluations" / group / f"seed{seed}"
    manifest = json.loads((path / "evaluation_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed", manifest
    assert manifest["group"] == group and manifest["seed"] == seed, manifest
    assert manifest["tape_start"] == 380000 and manifest["episodes_per_condition"] == 100, manifest
    assert manifest["tape_hash"] == tape_hash, manifest
    paired = read_csv(path / "paired_metrics.csv")
    raw = read_csv(path / "raw_episode_metrics.csv")
    assert len(paired) == 100 and len(raw) == 200, (len(paired), len(raw))
    assert all(float(row["failure_exposed"]) == 1.0 for row in paired), path
    return manifest, paired


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    args = parser.parse_args()
    tape = json.loads((args.results_root / "tape_manifest.json").read_text(encoding="utf-8"))
    assert tape["episode_ids"] == list(range(380000, 380100)), tape
    rows, eval_manifests = [], []
    for group in GROUPS:
        for seed in SEEDS:
            manifest, paired = verify_evaluation(args.results_root, group, seed, tape["tape_hash"])
            eval_manifests.append(manifest)
            rows.append(summary(group, seed, paired))
    fields = list(rows[0])
    with (args.results_root / "six_checkpoint_per_seed_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    pooled = {}
    for group in GROUPS:
        cells = [row for row in rows if row["group"] == group]
        pooled[group] = {key: sum(row[key] for row in cells) / len(cells) for key in fields if key not in {"group", "seed"}}
    j_n_star = pooled["fl_nominal_expert"]["J_nominal"]
    j_f_star = pooled["fl_f0_expert"]["J_failure"]
    mixed = pooled["mixed50_sg"]
    c_n = mixed["J_nominal"] / j_n_star
    c_f = mixed["J_failure"] / j_f_star
    c_min = min(c_n, c_f)
    if c_n >= 0.95 and c_f >= 0.90:
        classification = "M1"
        label = "already_balanced"
    elif c_n >= 0.95:
        classification = "M2"
        label = "failure_limited"
    elif c_f >= 0.90:
        classification = "M3"
        label = "nominal_limited"
    else:
        classification = "M4"
        label = "both_limited"

    mixed_manifests = []
    curve_rows = []
    for seed in SEEDS:
        run = args.results_root / "runs" / "mixed50_sg" / f"seed{seed}"
        manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "completed", manifest
        assert manifest["environment_steps"] == 1000192 and manifest["updates"] == 3907, manifest
        assert manifest["graph_encoder"] == "single" and manifest["parameter_count"] == 116728, manifest
        assert manifest["resume"] is False and manifest["early_stopping"] is False and manifest["checkpoint_promotion"] is False, manifest
        assert manifest["f0_probability"] == 0.5 and manifest["canonical_seeds_used"] is False, manifest
        assert (run / "fixed_condition_mixture_manifest.json").exists(), run
        mix_log = read_csv(run / "fixed_condition_mixture_log.csv")
        realized = {"nominal": sum(row["condition"] == "nominal" for row in mix_log),
                    "f0": sum(row["condition"] == "f0" for row in mix_log)}
        assert realized == manifest["realized_condition_counts"], (realized, manifest)
        train = read_csv(run / "train_log.csv")
        assert len(train) == 3907, len(train)
        for update, label_name in MILESTONES.items():
            checkpoint = run / f"actor_critic_milestone_{label_name}.pt"
            assert checkpoint.exists(), checkpoint
            row = next(row for row in train if int(row["update"]) == update)
            curve_rows.append({
                "seed": seed, "milestone": label_name, "update": update,
                "environment_steps": update * 4 * 64, "train_avg_reward": row["train_avg_reward"],
                "loss": row["loss"], "policy_loss": row["policy_loss"], "value_loss": row["value_loss"],
                "entropy": row["entropy"], "approx_kl": row["approx_kl"],
                "clip_fraction": row["clip_fraction"], "grad_norm": row["grad_norm"],
                "explained_variance": row["explained_variance"],
                "checkpoint_sha256": manifest["milestone_checkpoint_sha256"][label_name],
            })
        mixed_manifests.append({
            "seed": seed, "checkpoint_sha256": manifest["checkpoint_sha256"],
            "mixed50_config_hash": manifest["mixed50_config_hash"],
            "realized_condition_counts": realized, "milestone_checkpoint_sha256": manifest["milestone_checkpoint_sha256"],
        })
    with (args.results_root / "mixed50_milestone_learning_curves.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(curve_rows[0]))
        writer.writeheader(); writer.writerows(curve_rows)
    config_hashes = {item["mixed50_config_hash"] for item in mixed_manifests}
    assert len(config_hashes) == 1, config_hashes
    result = {
        "protocol": "PHASE-MSR-V1", "complete": True, "tape": tape,
        "six_checkpoint_evaluations": eval_manifests, "per_seed": rows, "pooled": pooled,
        "J_N_star": j_n_star, "J_F_star": j_f_star,
        "mixed50": {"C_N": c_n, "C_F": c_f, "C_min": c_min},
        "classification": classification, "classification_label": label,
        "mixed50_runs": mixed_manifests, "milestones_for_curve_only": True,
        "canonical_seeds_used": False, "enmm_started": False,
        "ood_started": False, "ablation_started": False, "formal_five_seed_started": False,
    }
    (args.results_root / "MSR_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
