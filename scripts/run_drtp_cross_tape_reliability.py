"""Evaluate frozen formal and independent DRTP cohorts on both frozen tapes.

This is a zero-training, post hoc reliability diagnostic.  It intentionally
keeps the two training cohorts stratified, never promotes a checkpoint, and
refuses to overwrite an existing output directory.
"""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import aggregate_drtp_sg_development as aggregate  # noqa: E402
import run_drtp_sg_development_evaluation as base  # noqa: E402


PROTOCOL = "DRTP-CROSS-TAPE-RELIABILITY-DIAGNOSTIC-V1"
FINAL_LABEL = "10m"
ARMS = ("utr_sg", "drtp_sg")
COHORTS = {
    "formal_2301_2305": {
        "seeds": (2301, 2302, 2303, 2304, 2305),
        "training_protocol": "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-TRAINING-V1",
        "tape_file": "formal_tape_manifest.json",
        "expected_tape_hash": "84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2",
    },
    "independent_2401_2405": {
        "seeds": (2401, 2402, 2403, 2404, 2405),
        "training_protocol": "DRTP-SNR-Q2-MECHANISM-COMPARATOR-TRAINING-V1",
        "tape_file": "snr_comparator_tape_manifest.json",
        "expected_tape_hash": "c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2",
    },
}
ARCHIVE_SHA256 = {
    "formal_2301_2305": "cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd",
    "independent_2401_2405": "86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1",
}
TAPE_LABELS = {
    "formal_2301_2305": "tape_490",
    "independent_2401_2405": "tape_500",
}
PRIMARY_ENDPOINTS = ("J_F0", "J_pert_mean", "J_pert_worst")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write an empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite_mean(values: list[float]) -> float:
    values = [value for value in values if math.isfinite(value)]
    return sum(values) / len(values) if values else math.nan


def load_tape(root: Path, cohort: str) -> dict:
    config = COHORTS[cohort]
    tape = json.loads((root / config["tape_file"]).read_text(encoding="utf-8"))
    if tape.get("tape_hash") != config["expected_tape_hash"]:
        raise RuntimeError(f"unexpected frozen tape hash for {cohort}")
    episode_ids = tape.get("episode_ids")
    conditions = tape.get("conditions")
    if not isinstance(episode_ids, list) or len(episode_ids) != 100:
        raise RuntimeError(f"invalid episode count for {cohort}")
    if episode_ids != list(range(int(episode_ids[0]), int(episode_ids[0]) + 100)):
        raise RuntimeError(f"non-contiguous frozen tape namespace for {cohort}")
    if not isinstance(conditions, list) or len(conditions) != 12:
        raise RuntimeError(f"invalid condition count for {cohort}")
    names = [item.get("name") for item in conditions]
    if names[:2] != ["nominal", "f0_seen_44_80"]:
        raise RuntimeError(f"unexpected first conditions for {cohort}: {names[:2]}")
    return tape


def load_sources(root: Path, cohort: str) -> list[dict]:
    config = COHORTS[cohort]
    sources = []
    for arm in ARMS:
        for seed in config["seeds"]:
            run_dir = root / "runs" / arm / f"seed{seed}"
            manifest_path = run_dir / "run_manifest.json"
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not manifest_path.is_file() or not checkpoint.is_file():
                raise FileNotFoundError(f"missing final run asset: {run_dir}")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            checks = {
                "completed": manifest.get("status") == "completed",
                "protocol": manifest.get("protocol") == config["training_protocol"],
                "seed": int(manifest.get("seed")) == seed,
                "parameter_count": manifest.get("parameter_count") == 116728,
                "from_scratch": manifest.get("from_scratch") is True,
                "strict_continuous": manifest.get("strict_continuous_trajectory") is True,
                "runtime_persistence": manifest.get("runtime_state_checkpointing") is True,
                "no_canonical": manifest.get("canonical_seeds_used") is False,
                "checkpoint_hash": sha256(checkpoint) == manifest.get("final_checkpoint_sha256"),
            }
            if not all(checks.values()):
                raise RuntimeError(f"frozen source validation failed for {cohort}/{arm}/seed{seed}: {checks}")
            sources.append({
                "cohort": cohort,
                "arm": arm,
                "seed": seed,
                "checkpoint": checkpoint,
                "checkpoint_sha256": sha256(checkpoint),
                "manifest": manifest,
            })
    return sources


def evaluate_worker(task: tuple[tuple, int]) -> list[dict]:
    (cohort, tape_label, base_task), gpu_id = task
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.set_device(gpu_id)
    except ImportError:  # pragma: no cover
        pass
    rows = base.evaluate_cell(base_task)
    for row in rows:
        row.update({
            "protocol": PROTOCOL,
            "training_cohort": cohort,
            "evaluation_tape": tape_label,
            "inference_unit": "training_seed",
        })
    return rows


def condition_summary(raw_rows: list[dict], tapes: dict[str, dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str, int, str], list[dict]] = {}
    for row in raw_rows:
        grouped.setdefault((
            row["training_cohort"], row["evaluation_tape"], row["method"],
            int(row["train_seed"]), row["topology_condition"],
        ), []).append(row)
    summaries: list[dict] = []
    for (cohort, tape_label, arm, seed, condition), rows in sorted(grouped.items()):
        if len(rows) != 100:
            raise RuntimeError(f"incomplete raw cell {cohort}/{tape_label}/{arm}/{seed}/{condition}: {len(rows)}")
        spec = next(item for item in tapes[tape_label]["conditions"] if item["name"] == condition)
        onset = int(spec["start_step"])
        risk_rows = [] if condition == "nominal" else [
            row for row in rows if int(float(row["terminal_step"])) >= onset
        ]
        pretrigger = [] if condition == "nominal" else [
            row for row in rows
            if float(row["collision"]) == 1.0 and int(float(row["terminal_step"])) < onset
        ]
        summaries.append({
            "training_cohort": cohort,
            "evaluation_tape": tape_label,
            "arm": arm,
            "seed": seed,
            "checkpoint_label": FINAL_LABEL,
            "condition": condition,
            "J": finite_mean([float(row["J"]) for row in rows]),
            "collision": finite_mean([float(row["collision"]) for row in rows]),
            "timeout": finite_mean([float(row["timeout"]) for row in rows]),
            "constraint_violation": finite_mean([float(row["constraint_violation"]) for row in rows]),
            "failure_exposure": math.nan if condition == "nominal" else finite_mean([float(row["failure_exposed"]) for row in rows]),
            "episode_length": finite_mean([float(row["terminal_step"]) for row in rows]),
            "risk_set_size": len(risk_rows),
            "survival_to_onset_fraction": math.nan if condition == "nominal" else len(risk_rows) / len(rows),
            "failure_trigger_success_rate_risk_set": math.nan if not risk_rows else finite_mean([float(row["failure_exposed"]) for row in risk_rows]),
            "pretrigger_collision_count": len(pretrigger),
            "pretrigger_collision_rate": math.nan if condition == "nominal" else len(pretrigger) / len(rows),
            "path_switch_count": finite_mean([float(row["path_switch_count"]) for row in rows]),
            "direct_path_fraction": finite_mean([float(row["direct_path_fraction_during_failure"]) for row in rows]),
            "relay_path_fraction": finite_mean([float(row["relay_path_fraction_during_failure"]) for row in rows]),
            "task_support_fraction": finite_mean([float(row["task_support_fraction_during_failure"]) for row in rows]),
            "legal_information_fraction": finite_mean([float(row["legal_information_fraction_during_failure"]) for row in rows]),
            "mean_cache_age": finite_mean([float(row["mean_cache_age_during_failure"]) for row in rows]),
        })
    return summaries


def endpoint_summary(summary_rows: list[dict], tape_names: tuple[str, ...]) -> list[dict]:
    grouped: dict[tuple[str, str, str, int], list[dict]] = {}
    for row in summary_rows:
        grouped.setdefault((row["training_cohort"], row["evaluation_tape"], row["arm"], int(row["seed"])), []).append(row)
    endpoints: list[dict] = []
    for (cohort, tape_label, arm, seed), rows in sorted(grouped.items()):
        by_condition = {row["condition"]: row for row in rows}
        if len(by_condition) != 12:
            raise RuntimeError(f"incomplete condition summary for {cohort}/{tape_label}/{arm}/{seed}")
        perturbation = [row for name, row in by_condition.items() if name not in {"nominal", "f0_seen_44_80"}]
        failures = [row for name, row in by_condition.items() if name != "nominal"]
        nominal, f0 = by_condition["nominal"], by_condition["f0_seen_44_80"]
        endpoints.append({
            "training_cohort": cohort,
            "evaluation_tape": tape_label,
            "arm": arm,
            "seed": seed,
            "J_nominal": nominal["J"],
            "J_F0": f0["J"],
            "J_pert_mean": finite_mean([float(row["J"]) for row in perturbation]),
            "J_pert_worst": min(float(row["J"]) for row in perturbation),
            "D_F0": float(nominal["J"]) - float(f0["J"]),
            "D_pert_worst": float(nominal["J"]) - min(float(row["J"]) for row in perturbation),
            "collision_failure_mean": finite_mean([float(row["collision"]) for row in failures]),
            "timeout_failure_mean": finite_mean([float(row["timeout"]) for row in failures]),
            "constraint_failure_mean": finite_mean([float(row["constraint_violation"]) for row in failures]),
            "risk_set_trigger_validity": min(
                float(row["failure_trigger_success_rate_risk_set"])
                for row in failures if int(row["risk_set_size"]) > 0
            ),
            "pretrigger_collision_count": sum(int(row["pretrigger_collision_count"]) for row in failures),
        })
    expected = len(COHORTS) * len(tape_names) * len(ARMS) * 5
    if len(endpoints) != expected:
        raise RuntimeError(f"endpoint cell count {len(endpoints)} != {expected}")
    return endpoints


def paired_effects(endpoints: list[dict], tape_names: tuple[str, ...]) -> list[dict]:
    by_key = {(row["training_cohort"], row["evaluation_tape"], row["arm"], int(row["seed"])): row for row in endpoints}
    result: list[dict] = []
    metrics = ("J_nominal", *PRIMARY_ENDPOINTS, "D_F0", "D_pert_worst")
    for cohort, config in COHORTS.items():
        for tape_label in tape_names:
            for metric in metrics:
                values = []
                for seed in config["seeds"]:
                    utr = by_key[(cohort, tape_label, "utr_sg", seed)]
                    drtp = by_key[(cohort, tape_label, "drtp_sg", seed)]
                    values.append(float(drtp[metric]) - float(utr[metric]))
                result.append({
                    "training_cohort": cohort,
                    "evaluation_tape": tape_label,
                    "endpoint": metric,
                    "n_training_seeds": len(values),
                    "mean_drtp_minus_utr": statistics.mean(values),
                    "median_drtp_minus_utr": statistics.median(values),
                    "wins_over_zero": sum(value > 0 for value in values),
                    "worst_drtp_minus_utr": min(values),
                    "paired_values": json.dumps(values),
                    "direction": "positive" if statistics.mean(values) > 0 and statistics.median(values) > 0 else "nonpositive",
                })
    return result


def classify(effects: list[dict], tape_names: tuple[str, ...]) -> tuple[str, dict]:
    matrix: dict[str, dict[str, str]] = {}
    for cohort in COHORTS:
        matrix[cohort] = {}
        for endpoint in PRIMARY_ENDPOINTS:
            directions = [next(
                row["direction"] for row in effects
                if row["training_cohort"] == cohort and row["evaluation_tape"] == tape and row["endpoint"] == endpoint
            ) for tape in tape_names]
            matrix[cohort][endpoint] = "consistent" if len(set(directions)) == 1 else "changes_with_tape"
    if all(value == "consistent" for item in matrix.values() for value in item.values()):
        return "COHORT_DIRECTION_PERSISTS_ACROSS_TAPES", matrix
    if all(value == "changes_with_tape" for item in matrix.values() for value in item.values()):
        return "TAPE_SENSITIVITY_OR_INTERACTION_OBSERVED", matrix
    return "MIXED_ENDPOINT_PATTERN", matrix


def write_report(path: Path, effects: list[dict], classification: str, matrix: dict) -> None:
    lines = [
        "# DRTP 跨评价带可靠性诊断报告", "",
        f"**状态：** `{classification}`", "",
        "本报告为零训练、post hoc 的交叉评价诊断。训练 seed 仍是独立单位；两个训练 cohort 分层显示，绝不合并为 `n=10`。", "",
        "## UTR--DRTP 配对效应", "",
        "| 训练 cohort | 评价带 | 端点 | mean | median | wins/5 | worst | 方向 |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in effects:
        lines.append(
            f"| {row['training_cohort']} | {row['evaluation_tape']} | {row['endpoint']} | "
            f"{float(row['mean_drtp_minus_utr']):.2f} | {float(row['median_drtp_minus_utr']):.2f} | "
            f"{row['wins_over_zero']}/5 | {float(row['worst_drtp_minus_utr']):.2f} | {row['direction']} |"
        )
    lines += ["", "## 主要端点的 tape 内一致性", ""]
    for cohort, endpoints in matrix.items():
        lines.append(f"- `{cohort}`: " + "; ".join(f"{name}={value}" for name, value in endpoints.items()))
    lines += [
        "", "## 解释边界", "",
        "该结果只能说明 UTR--DRTP 的配对方向是否在同一训练 cohort 内跨两个冻结评价带保持。"
        "即使方向跨带保持，也不能单独识别具体训练随机源、证明在线自适应相对于任意静态非均匀分布必要，"
        "或将两个 cohort 视为同质样本。", "",
        "未启动训练、未修改 checkpoint、未重写原正式 cohort 或独立 cohort 的合同内结论。", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-root", type=Path, required=True)
    parser.add_argument("--independent-root", type=Path, required=True)
    parser.add_argument("--formal-archive", type=Path, required=True)
    parser.add_argument("--independent-archive", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--gpu-ids", default="0")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.workers < 1:
        raise ValueError("workers must be positive")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_root}")
    for cohort, archive in (
        ("formal_2301_2305", args.formal_archive),
        ("independent_2401_2405", args.independent_archive),
    ):
        if not archive.is_file():
            raise FileNotFoundError(archive)
        if sha256(archive) != ARCHIVE_SHA256[cohort]:
            raise RuntimeError(f"source archive SHA256 mismatch: {cohort}")
    tape_roots = {
        "formal_2301_2305": args.formal_root,
        "independent_2401_2405": args.independent_root,
    }
    tapes = {TAPE_LABELS[cohort]: load_tape(root, cohort) for cohort, root in tape_roots.items()}
    formal_names = [item["name"] for item in tapes["tape_490"]["conditions"]]
    independent_names = [item["name"] for item in tapes["tape_500"]["conditions"]]
    if formal_names != independent_names:
        raise RuntimeError("the two frozen tapes do not share the same condition table")
    sources = {
        cohort: load_sources(root, cohort)
        for cohort, root in tape_roots.items()
    }
    tape_names = tuple(tapes)
    tasks = []
    for cohort, source_rows in sources.items():
        for tape_label in tape_names:
            tape = tapes[tape_label]
            for source in source_rows:
                conditions = tape["conditions"][:1] if args.smoke else tape["conditions"]
                episode_ids = tape["episode_ids"][:1] if args.smoke else tape["episode_ids"]
                base_task = (
                    source["arm"], source["seed"], str(source["checkpoint"]), FINAL_LABEL,
                    episode_ids, conditions, tape["tape_hash"],
                )
                tasks.append((cohort, tape_label, base_task))
    gpu_ids = [int(item.strip()) for item in args.gpu_ids.split(",") if item.strip()]
    if not gpu_ids:
        raise ValueError("at least one GPU id is required")
    assigned = [(task, gpu_ids[index % len(gpu_ids)]) for index, task in enumerate(tasks)]
    args.output_root.mkdir(parents=True, exist_ok=False)
    expected = len(tasks) * (1 if args.smoke else 12) * (1 if args.smoke else 100)
    print(f"cross-tape evaluation: workers={min(args.workers, len(assigned))}, cells={len(tasks)}, episodes={expected}", flush=True)
    raw_rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=min(args.workers, len(assigned)), mp_context=mp.get_context("spawn")) as pool:
        futures = [pool.submit(evaluate_worker, task) for task in assigned]
        completed = 0
        for future in as_completed(futures):
            rows = future.result()
            raw_rows.extend(rows)
            completed += len(rows)
            print(f"cross-tape evaluation progress {completed}/{expected} ({100 * completed / expected:.2f}%)", flush=True)
    raw_rows.sort(key=lambda row: (
        row["training_cohort"], row["evaluation_tape"], row["method"], int(row["train_seed"]),
        formal_names.index(row["topology_condition"]), int(row["development_episode_id"]),
    ))
    if len(raw_rows) != expected:
        raise RuntimeError(f"expected {expected} raw rows, found {len(raw_rows)}")
    write_csv(args.output_root / "raw_episode_metrics.csv", raw_rows)
    manifest = {
        "protocol": PROTOCOL,
        "status": "smoke_completed" if args.smoke else "completed",
        "training_started": False,
        "archive_sha256": ARCHIVE_SHA256,
        "raw_rows": len(raw_rows),
        "expected_rows": expected,
        "workers": min(args.workers, len(assigned)),
        "gpu_ids": gpu_ids,
        "training_cohorts": {name: {"seeds": list(config["seeds"])} for name, config in COHORTS.items()},
        "evaluation_tapes": {name: {"tape_hash": tape["tape_hash"], "episode_ids": tape["episode_ids"]} for name, tape in tapes.items()},
        "all_scheduled_episodes_retained": True,
        "cross_cohort_pooling_prohibited": True,
    }
    (args.output_root / "evaluation_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.smoke:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    summaries = condition_summary(raw_rows, tapes)
    write_csv(args.output_root / "per_seed_condition_summary.csv", summaries)
    endpoints = endpoint_summary(summaries, tape_names)
    write_csv(args.output_root / "per_seed_endpoint_summary.csv", endpoints)
    effects = paired_effects(endpoints, tape_names)
    write_csv(args.output_root / "paired_effects_by_cohort_tape.csv", effects)
    classification, matrix = classify(effects, tape_names)
    decision = {
        "protocol": PROTOCOL,
        "status": classification,
        "training_started": False,
        "raw_rows": len(raw_rows),
        "technical_validity": "PASS",
        "tape_consistency_matrix": matrix,
        "cross_cohort_pooling_prohibited": True,
        "interpretation": "zero-training post hoc diagnostic only; it does not rewrite any cohort-specific verdict",
    }
    (args.output_root / "DRTP_CROSS_TAPE_RELIABILITY_DECISION.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(args.output_root / "DRTP_CROSS_TAPE_RELIABILITY_REPORT.md", effects, classification, matrix)
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
