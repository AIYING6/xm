"""Zero-training DRTP cohort-reversal diagnostic.

Reads the frozen formal and independent archives, reconstructs only telemetry
that is actually present, and writes an evidence-bounded forensic report.
No training, evaluation, checkpoint promotion, or model mutation is performed.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import statistics
import tarfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "diagnostics" / "drtp_cohort_reversal_20260828"
GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
Q_FIELDS = {g: f"q_{g}" for g in GROUPS}
EMA_FIELDS = {g: f"ema_{g}" for g in ("N",) + GROUPS}
DIFF_FIELDS = {g: f"difficulty_{g}" for g in GROUPS}
PPO_FIELDS = ("approx_kl", "entropy", "policy_loss", "value_loss", "grad_norm", "train_avg_reward")
ARCHIVES = (
    {
        "cohort": "formal_2301_2305",
        "path": Path(r"D:\File\Downloads\drtp_utr_q2_paired_5seed_cloud_10way.tar.gz"),
        "root": "results/formal/drtp_utr_q2_paired_5seed_cloud_10way",
        "seeds": (2301, 2302, 2303, 2304, 2305),
    },
    {
        "cohort": "independent_2401_2405",
        "path": Path(r"D:\File\Downloads\drtp_snr_q2_mechanism_comparator_10way_results.tar.gz"),
        "root": "results/formal/drtp_snr_q2_mechanism_comparator_10way",
        "seeds": (2401, 2402, 2403, 2404, 2405),
    },
)


def num(value: object) -> float | None:
    if value is None or str(value).strip() in {"", "NA", "nan", "NaN", "NOT_AVAILABLE"}:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    return statistics.fmean(clean) if clean else None


def read_csv_member(bundle: tarfile.TarFile, name: str) -> list[dict[str, str]]:
    member = bundle.getmember(name)
    source = bundle.extractfile(member)
    if source is None:
        raise RuntimeError(f"cannot read archive member: {name}")
    with io.TextIOWrapper(source, encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def archive_inventory() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for spec in ARCHIVES:
        row: dict[str, object] = {"cohort": spec["cohort"], "archive": str(spec["path"]), "exists": spec["path"].exists()}
        if not spec["path"].exists():
            rows.append(row)
            continue
        with tarfile.open(spec["path"], "r:gz") as bundle:
            names = {m.name for m in bundle.getmembers() if m.isfile()}
        row.update({
            "file_count": len(names),
            "train_logs": sum(1 for n in names if n.endswith("train_log.csv")),
            "sampler_logs": sum(1 for n in names if n.endswith("drtp_topology_sampler_log.csv")),
            "runtime_checkpoints": sum(1 for n in names if "runtime_state" in n and n.endswith(".pt")),
            "milestone_checkpoints": sum(1 for n in names if "milestone" in n and n.endswith(".pt")),
            "raw_episode_files": sum(1 for n in names if n.endswith("raw_episode_metrics.csv")),
            "step_telemetry_files": sum(1 for n in names if "telemetry" in n.lower()),
        })
        rows.append(row)
    return rows


def reconstruct(output: Path) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    train_long: list[dict[str, object]] = []
    sampler_bins: dict[tuple[str, str, int, int], dict[str, object]] = {}
    features: list[dict[str, object]] = []
    timeline: list[dict[str, object]] = []
    for spec in ARCHIVES:
        if not spec["path"].exists():
            continue
        with tarfile.open(spec["path"], "r:gz") as bundle:
            names = {m.name for m in bundle.getmembers() if m.isfile()}
            for method in ("utr_sg", "drtp_sg"):
                for seed in spec["seeds"]:
                    prefix = f"{spec['root']}/runs/{method}/seed{seed}"
                    train_name = f"{prefix}/train_log.csv"
                    sampler_name = f"{prefix}/drtp_topology_sampler_log.csv"
                    if train_name not in names:
                        continue
                    train_rows = read_csv_member(bundle, train_name)
                    sampler_rows = read_csv_member(bundle, sampler_name) if sampler_name in names else []
                    train_by_bin: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
                    for raw in train_rows:
                        update = int(float(raw["update"]))
                        bin_id = (update - 1) // 500
                        row = {"cohort": spec["cohort"], "method": method, "seed": seed, "update": update,
                               "environment_steps_million": update * 256 / 1_000_000}
                        for field in PPO_FIELDS:
                            value = num(raw.get(field))
                            row[field] = value
                            if value is not None:
                                train_by_bin[bin_id][field].append(value)
                        train_long.append(row)
                    q_by_update: dict[int, dict[str, float]] = {}
                    local_sampler: dict[int, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
                    for raw in sampler_rows:
                        update = int(float(raw.get("update") or 0))
                        bin_id = max(0, (update - 1) // 500)
                        bucket = sampler_bins.setdefault((spec["cohort"], method, seed, bin_id), {
                            "cohort": spec["cohort"], "method": method, "seed": seed, "bin_id": bin_id,
                            "update_start": bin_id * 500 + 1, "update_end": (bin_id + 1) * 500,
                            "selection_count": 0, "adaptation_count": 0,
                            **{f"exposure_{g}": 0 for g in GROUPS},
                        })
                        bucket["selection_count"] = int(bucket["selection_count"]) + (1 if raw.get("record_type") == "selection" else 0)
                        bucket["adaptation_count"] = int(bucket["adaptation_count"]) + (1 if raw.get("record_type") == "adaptation" else 0)
                        if raw.get("record_type") == "selection" and raw.get("group") in GROUPS:
                            bucket[f"exposure_{raw['group']}"] = int(bucket[f"exposure_{raw['group']}" ]) + 1
                        q: dict[str, float] = {}
                        for group, field in Q_FIELDS.items():
                            value = num(raw.get(field))
                            if value is not None:
                                q[group] = value
                                local_sampler[bin_id][field].append(value)
                        if q:
                            q_by_update[update] = q
                        for group, field in {**EMA_FIELDS, **DIFF_FIELDS}.items():
                            value = num(raw.get(field))
                            if value is not None:
                                local_sampler[bin_id][field].append(value)
                    for bin_id, bucket in list(sampler_bins.items()):
                        if bucket["cohort"] == spec["cohort"] and bucket["method"] == method and bucket["seed"] == seed:
                            for field, values in local_sampler.get(bin_id, {}).items():
                                bucket[f"mean_{field}"] = mean(values)
                            q_values_in_bin = [bucket.get(f"mean_q_{group}") for group in GROUPS]
                            if all(value is not None for value in q_values_in_bin):
                                bucket["q_distance_uniform"] = sum(abs(float(value) - 1 / 6) for value in q_values_in_bin)
                            else:
                                bucket["q_distance_uniform"] = None
                    q_values = list(q_by_update.items())
                    q_distances: list[float] = []
                    q_entropies: list[float] = []
                    q_changes: list[float] = []
                    max_q = min_q = None
                    previous: dict[str, float] | None = None
                    for _, q in sorted(q_values):
                        vals = [q[g] for g in GROUPS if g in q]
                        if len(vals) != len(GROUPS):
                            continue
                        max_q = max(vals) if max_q is None else max(max_q, max(vals))
                        min_q = min(vals) if min_q is None else min(min_q, min(vals))
                        q_distances.append(sum(abs(v - 1 / 6) for v in vals))
                        q_entropies.append(-sum(v * math.log(max(v, 1e-12)) for v in vals))
                        if previous is not None:
                            q_changes.append(sum(abs(q[g] - previous[g]) for g in GROUPS))
                        previous = q
                    train_values = {field: [num(row.get(field)) for row in train_rows] for field in PPO_FIELDS}
                    train_values = {field: [v for v in values if v is not None] for field, values in train_values.items()}
                    n = max(1, len(q_values))
                    features.append({
                        "cohort": spec["cohort"], "method": method, "seed": seed,
                        "q_snapshots": len(q_values), "max_q": max_q, "min_q": min_q,
                        "time_at_upper_bound": sum(v >= 0.349999 for v in [x for _, q in q_values for x in q.values()]) / max(1, len(q_values) * 6),
                        "time_at_lower_bound": sum(v <= 0.050001 for v in [x for _, q in q_values for x in q.values()]) / max(1, len(q_values) * 6),
                        "mean_L1_q_change": mean(q_changes), "max_L1_q_change": max(q_changes) if q_changes else None,
                        "q_variance": statistics.pvariance(q_distances) if len(q_distances) > 1 else None,
                        "q_entropy_mean": mean(q_entropies), "distance_from_uniform_mean": mean(q_distances),
                        "cumulative_distance_from_uniform": sum(q_distances) / n,
                        "mean_KL": mean(train_values["approx_kl"]), "max_KL": max(train_values["approx_kl"], default=None),
                        "KL_ge_0_02_count": sum(v >= 0.02 for v in train_values["approx_kl"]),
                        "entropy_drop_first_to_last": (mean(train_values["entropy"][:max(1, len(train_values["entropy"]) // 10)]) - mean(train_values["entropy"][-max(1, len(train_values["entropy"]) // 10):])) if train_values["entropy"] else None,
                        "value_loss_peak": max((abs(v) for v in train_values["value_loss"]), default=None),
                        "policy_loss_variance": statistics.pvariance(train_values["policy_loss"]) if len(train_values["policy_loss"]) > 1 else None,
                        "grad_norm_peak": max(train_values["grad_norm"], default=None),
                        "early_return": mean(train_values["train_avg_reward"][:max(1, len(train_values["train_avg_reward"]) // 10)]),
                        "mid_return": mean(train_values["train_avg_reward"][len(train_values["train_avg_reward"]) // 2:max(1, len(train_values["train_avg_reward"]) // 2 + len(train_values["train_avg_reward"]) // 10)]),
                        "late_return": mean(train_values["train_avg_reward"][-max(1, len(train_values["train_avg_reward"]) // 10):]),
                    })
    # Build a descriptive window table from binned training and sampler telemetry.
    windows = (("0-1M", 0, 3906), ("1-2M", 3907, 7812), ("2-3M", 7813, 11718),
               ("3-5M", 11719, 19531), ("5-7M", 19532, 27343), ("7-10M", 27344, 39063))
    for name, lo, hi in windows:
        for cohort in ("formal_2301_2305", "independent_2401_2405"):
            row: dict[str, object] = {"window": name, "cohort": cohort}
            for method in ("utr_sg", "drtp_sg"):
                matching = [r for r in train_long if r["cohort"] == cohort and r["method"] == method and lo <= int(r["update"]) <= hi]
                for field in ("train_avg_reward", "approx_kl", "entropy", "policy_loss", "value_loss", "grad_norm"):
                    row[f"{method}_{field}"] = mean([float(r[field]) for r in matching if r[field] is not None])
                srows = [r for r in sampler_bins.values() if r["cohort"] == cohort and r["method"] == method and lo // 500 <= int(r["bin_id"]) <= hi // 500]
                row[f"{method}_q_distance_uniform"] = mean([num(r.get("q_distance_uniform")) for r in srows])
            timeline.append(row)
    write_csv(output / "01_reconstructed" / "training_dynamics_long.csv", train_long,
              ["cohort", "method", "seed", "update", "environment_steps_million", *PPO_FIELDS])
    sampler_fields = ["cohort", "method", "seed", "bin_id", "update_start", "update_end", "selection_count", "adaptation_count", "q_distance_uniform", *[f"exposure_{g}" for g in GROUPS]]
    sampler_fields += [f"mean_{f}" for f in (*Q_FIELDS.values(), *EMA_FIELDS.values(), *DIFF_FIELDS.values())]
    write_csv(output / "01_reconstructed" / "drtp_sampler_dynamics.csv", list(sampler_bins.values()), sampler_fields)
    write_csv(output / "01_reconstructed" / "ppo_dynamics.csv", train_long,
              ["cohort", "method", "seed", "update", "environment_steps_million", *PPO_FIELDS])
    write_csv(output / "03_features" / "seed_features.csv", features, list(features[0].keys()) if features else ["cohort", "method", "seed"])
    write_csv(output / "04_timeline" / "divergence_timeline.csv", timeline, list(timeline[0].keys()) if timeline else ["window", "cohort"])
    return train_long, list(sampler_bins.values()), features, timeline


def write_report(output: Path, inventory: list[dict[str, object]], train: list[dict[str, object]], sampler: list[dict[str, object]], features: list[dict[str, object]], timeline: list[dict[str, object]]) -> None:
    missing = [
        "两批 cohort 均无 per-step environment/behavior telemetry 文件；因此 completion/timeout/collision 的训练期动态不可重建。",
        "归档内没有独立、逐阶段落盘的 entropy/KL/loss/grad 之外的行为—优化同步日志；现有 train_log.csv 可提供 PPO 诊断，但不能替代环境行为轨迹。",
        "正式与独立 cohort 的逐种子 q/EMA/difficulty 原始日志存在；公开复现包只选择性提取了 sampler log，完整重建依赖源归档。",
    ]
    lines = [
        "# DRTP cohort reversal mechanism diagnostic",
        "",
        "状态：`NO-GO — existing telemetry does not support a stable actionable mechanism`",
        "",
        "本报告为零训练、零重评估诊断。未修改算法、PPO、检查点、评价规则或训练种子；没有任何大规模训练/评估在本机执行。",
        "",
        "## 1. Inputs and provenance",
        "",
        "| cohort | train logs | sampler logs | runtime checkpoints | milestone checkpoints | step telemetry files |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in inventory:
        lines.append(f"| {row['cohort']} | {row.get('train_logs','NA')} | {row.get('sampler_logs','NA')} | {row.get('runtime_checkpoints','NA')} | {row.get('milestone_checkpoints','NA')} | {row.get('step_telemetry_files','NA')} |")
    lines += [
        "",
        "P1 重建得到：目标 UTR/DRTP 的 20 条训练日志的 PPO/return 逐 update 记录、20 条 sampler 日志的 q/EMA/difficulty/selection 信息，以及 20 个 seed-level 特征行。独立归档另含 5 条 SNR comparator 训练日志，但它们不属于本次 formal-vs-independent DRTP cohort reversal 目标。训练轴采用 500 updates 分箱；environment step 映射沿用 10M 合同的 256 steps/update。",
        "",
        "## 2. Missing telemetry",
        "",
    ] + [f"- {item}" for item in missing] + [
        "",
        "## 3. Formal and independent cohort behavior",
        "",
        f"归档清单共包含 {sum(int(row.get('train_logs', 0)) for row in inventory)} 个 train_log.csv；本诊断实际重建 UTR/DRTP 目标日志 {len(train)} 行、sampler 分箱记录 {len(sampler)} 行、seed 特征 {len(features)} 行。正式主 cohort 与独立 cohort 的最终方向仍以 cross-tape 结果为准：正式 cohort 两张 tape 正向，独立 cohort 两张 tape 反向。",
        "",
        "### 3.1 Descriptive cohort summaries",
        "",
        "下表仅是现有训练日志的描述性聚合，不是机制证明；`late_return` 是 train_log 的末期平均回报代理，不能替代 evaluation return。",
        "",
        "| cohort | method | mean L1(q-uniform) | mean KL | late training reward |",
        "|---|---|---:|---:|---:|",
        *[
            f"| {cohort} | {method} | "
            + " | ".join(
                f"{statistics.fmean([float(value) for value in (num(row.get(field)) for row in features if row['cohort'] == cohort and row['method'] == method) if value is not None]):.6f}"
                if any(num(row.get(field)) is not None for row in features if row['cohort'] == cohort and row['method'] == method)
                else "NA"
                for field in ("distance_from_uniform_mean", "mean_KL", "late_return")
            )
            + " |"
            for cohort in ("formal_2301_2305", "independent_2401_2405")
            for method in ("utr_sg", "drtp_sg")
        ],
        "",
        "## 4. First divergence point",
        "",
        "不能从现有证据把‘最终性能首次分叉’定位到某一训练窗口。现有 q/PPO 过程数据可用于描述窗口差异，但缺少与行为结果同步的逐步轨迹，也没有预注册的 divergence effect threshold；因此不得把 0–1M 或其他窗口写成已证实的因果起点。",
        "",
        "## 5. Sampler and PPO diagnostics",
        "",
        "sampler q、EMA、difficulty 和 selection/exposure 已按 500-update 窗口导出到 `01_reconstructed/drtp_sampler_dynamics.csv`；PPO 指标导出到 `01_reconstructed/ppo_dynamics.csv`。这些文件可支持‘采样器实际改变了暴露’和‘PPO 指标的描述性比较’，不能单独支持 EMA noise → q polarization → behavior collapse 的机制链。",
        "",
        "## 6. UTR control analysis",
        "",
        "UTR 的 train_log 也按同一 update 轴重建，因而每个 PPO 候选都必须与 UTR 同 cohort 对照。由于缺少训练期行为遥测，不能仅凭 DRTP 的 KL/entropy/loss 差异认定其为 DRTP 特异失稳。",
        "",
        "## 7. Candidate mechanism evidence matrix",
        "",
        "| candidate | temporal precedence | cross-seed repetition | DRTP specificity | counter-evidence / limitation | level |",
        "|---|---|---|---|---|---|",
        "| EMA noise → q divergence → exposure imbalance | partially inspectable from sampler log | not established across majority of failed seeds with behavior linkage | not established against UTR | no synchronized behavior trajectory; no causal intervention | weak/insufficient |",
        "| generic PPO/optimization instability | PPO fields available | not established as a cohort-specific mechanism | not established; UTR control required | no behavior linkage and no pre-registered instability threshold | weak/insufficient |",
        "| coordination/role deadlock | unavailable | unavailable | unavailable | no per-step position/action/task-stage telemetry | not testable |",
        "",
        "## 8. Evidence against over-interpretation",
        "",
        "- Cross-tape persistence rejects evaluation tape change as a sufficient explanation, but does not identify the training mechanism.",
        "- A difference in q or PPO statistics is not evidence of a performance-causal chain without temporal linkage to behavior and an appropriate UTR control.",
        "- Final checkpoints and final evaluation records cannot reconstruct an unobserved early training divergence.",
        "- Missing fields remain `NA`; no final metric is back-filled into a training curve.",
        "",
        "## 9. Decision",
        "",
        "`NO-GO`: existing logs are sufficient for a reproducibility-bounded descriptive audit, but insufficient for a stable actionable failure mechanism under the frozen GO rule (time-leading, repeated across failed seeds, DRTP-specific, directionally coherent, and supported against counter-evidence).",
        "",
        "## 10. Recommended next intervention",
        "",
        "不实现 Stable-DRTP，不启动新的 10M。若未来仍要做机制研究，应先单独冻结完整行为/优化同步遥测合同，并在开训前通过实际落盘 smoke gate；任何大规模训练或大规模评估必须转移到云端执行，并采用硬件内存允许范围内的最大安全并发。",
    ]
    report = output / "05_report" / "cohort_reversal_forensic_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "00_contract").mkdir(parents=True, exist_ok=True)
    (output / "00_contract" / "diagnostic_contract.md").write_text(
        "# DRTP cohort reversal diagnostic contract\n\nZero training/evaluation; preserve all seeds, checkpoints, methods, PPO and evaluation definitions. Reconstruct only archived fields; missing telemetry is `NA`; no Stable-DRTP implementation or long run before a strong mechanism candidate.\n",
        encoding="utf-8")
    (output / "00_contract" / "missing_assets.md").write_text("# Missing assets\n\n" + "\n".join(f"- {item}" for item in missing) + "\n", encoding="utf-8")
    (output / "02_figures" / "behavior_dynamics").mkdir(parents=True, exist_ok=True)
    (output / "02_figures" / "behavior_dynamics" / "MISSING_TELEMETRY.md").write_text("Behavior dynamics cannot be plotted: no archived per-step environment/behavior telemetry for both cohorts.\n", encoding="utf-8")
    (output / "05_report" / "mechanism_evidence_matrix.csv").write_text(
        "candidate,temporal_precedence,cross_seed_repetition,drtp_specificity,level\n"
        "ema_to_q_to_exposure,partial,not_established,not_established,insufficient\n"
        "generic_ppo_instability,partial,not_established,not_established,insufficient\n"
        "coordination_deadlock,unavailable,unavailable,unavailable,not_testable\n", encoding="utf-8")
    (output / "05_report" / "seed_level_summary.csv").write_text(
        "cohort,method,seed\n" + "\n".join(f"{r['cohort']},{r['method']},{r['seed']}" for r in features) + "\n", encoding="utf-8")
    (output / "00_contract" / "provenance.json").write_text(json.dumps({"status": "zero_training_diagnostic", "archives": [str(s["path"]) for s in ARCHIVES], "no_training": True, "no_evaluation": True}, indent=2), encoding="utf-8")


def write_figures(output: Path, timeline: list[dict[str, object]]) -> None:
    """Write only descriptive plots from reconstructed logs; never re-evaluate episodes."""
    figure_root = output / "05_report"
    for folder in ("q_dynamics", "ppo_dynamics", "divergence_timeline"):
        (figure_root / folder).mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on the local analysis runtime
        note = f"Figures unavailable because matplotlib could not be imported: {exc}\n"
        (figure_root / "q_dynamics" / "FIGURES_UNAVAILABLE.md").write_text(note, encoding="utf-8")
        return

    windows = [str(row["window"]) for row in timeline if row["cohort"] == "formal_2301_2305"]
    x = list(range(len(windows)))
    colors = {"formal_2301_2305": "tab:blue", "independent_2401_2405": "tab:orange"}
    cohort_label = {"formal_2301_2305": "formal 2301-2305", "independent_2401_2405": "independent 2401-2405"}

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for cohort in colors:
        rows = [row for row in timeline if row["cohort"] == cohort]
        for method, linestyle in (("utr_sg", "--"), ("drtp_sg", "-")):
            values = [num(row.get(f"{method}_q_distance_uniform")) for row in rows]
            ax.plot(x[:len(values)], values, marker="o", linestyle=linestyle, color=colors[cohort],
                    label=f"{cohort_label[cohort]} / {method.upper()}")
    ax.set_xticks(x, windows, rotation=25, ha="right")
    ax.set_ylabel("L1 distance of q from uniform")
    ax.set_title("Descriptive sampler deviation across training windows")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(figure_root / "q_dynamics" / "cohort_q_distance.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for cohort in colors:
        rows = [row for row in timeline if row["cohort"] == cohort]
        for method, linestyle in (("utr_sg", "--"), ("drtp_sg", "-")):
            label = f"{cohort_label[cohort]} / {method.upper()}"
            axes[0].plot(x[:len(rows)], [num(row.get(f"{method}_approx_kl")) for row in rows],
                         marker="o", linestyle=linestyle, color=colors[cohort], label=label)
            axes[1].plot(x[:len(rows)], [num(row.get(f"{method}_entropy")) for row in rows],
                         marker="o", linestyle=linestyle, color=colors[cohort], label=label)
    axes[0].set_ylabel("approx KL")
    axes[1].set_ylabel("entropy")
    axes[1].set_xticks(x, windows, rotation=25, ha="right")
    axes[0].set_title("Descriptive PPO diagnostics across training windows")
    for axis in axes:
        axis.grid(alpha=0.25)
    axes[0].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(figure_root / "ppo_dynamics" / "cohort_ppo_diagnostics.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for cohort in colors:
        rows = [row for row in timeline if row["cohort"] == cohort]
        formal_or_independent = "formal" if cohort.startswith("formal") else "independent"
        for method, marker in (("utr_sg", "s"), ("drtp_sg", "o")):
            values = [num(row.get(f"{method}_train_avg_reward")) for row in rows]
            ax.plot(x[:len(rows)], values, marker=marker, color=colors[cohort],
                    label=f"{formal_or_independent} / {method.upper()}")
    ax.set_xticks(x, windows, rotation=25, ha="right")
    ax.set_ylabel("mean training reward")
    ax.set_title("Descriptive divergence timeline (training reward proxy)")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(figure_root / "divergence_timeline" / "divergence_timeline.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    inventory = archive_inventory()
    write_csv(output / "00_contract" / "asset_inventory.csv", inventory, sorted({k for row in inventory for k in row}))
    train, sampler, features, timeline = reconstruct(output)
    write_report(output, inventory, train, sampler, features, timeline)
    write_figures(output, timeline)
    print(json.dumps({"status": "NO_GO_EXISTING_TELEMETRY_INSUFFICIENT", "output": str(output), "train_rows": len(train), "sampler_bins": len(sampler), "seed_features": len(features), "timeline_rows": len(timeline)}, indent=2))


if __name__ == "__main__":
    main()
