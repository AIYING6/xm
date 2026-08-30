#!/usr/bin/env python3
"""Build the frozen DRTP B5 cross-cohort evidence atlas without training."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import tarfile
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "drtp_b5_cross_cohort_atlas_freeze.json"
DEFAULT_OUTPUT = ROOT / "docs" / "drtp_b5_20260830"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def fmt(values: list[float]) -> str:
    if not values:
        return "NA"
    return ";".join(f"{value:.6f}" for value in values)


def dispersion(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "minimum": None, "maximum": None, "range": None, "sample_sd": None}
    return {
        "mean": statistics.mean(values),
        "minimum": min(values),
        "maximum": max(values),
        "range": max(values) - min(values),
        "sample_sd": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def archive_audit(config: dict[str, Any], archive_root: Path) -> list[dict[str, Any]]:
    audits: list[dict[str, Any]] = []
    for experiment in config["experiments"]:
        archive = archive_root / experiment["archive"]
        if not archive.is_file():
            raise FileNotFoundError(f"missing evidence archive: {archive}")
        actual = sha256_file(archive)
        if actual != experiment["sha256"]:
            raise RuntimeError(f"SHA256 mismatch for {archive.name}: {actual}")
        required = experiment["required_member"]
        with tarfile.open(archive, "r:gz") as bundle:
            members = set(bundle.getnames())
            if required not in members:
                raise RuntimeError(f"required member missing from {archive.name}: {required}")
            extracted = bundle.extractfile(required)
            if extracted is None:
                raise RuntimeError(f"cannot read required member from {archive.name}: {required}")
            decision_text = extracted.read().decode("utf-8")
        expected_decision = experiment["decision"]
        if required.endswith(".json"):
            actual_decision = json.loads(decision_text).get("decision")
            if actual_decision != expected_decision:
                raise RuntimeError(
                    f"decision mismatch for {experiment['id']}: expected {expected_decision!r}, got {actual_decision!r}"
                )
        elif expected_decision not in decision_text:
            raise RuntimeError(f"decision text missing for {experiment['id']}: {expected_decision}")
        audits.append(
            {
                "experiment_id": experiment["id"],
                "archive": archive.name,
                "sha256": actual,
                "required_member": required,
                "decision": expected_decision,
                "integrity": "PASS",
            }
        )
    return audits


def source_audit(config: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for relative in config["source_documents"]:
        path = ROOT / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing source document: {relative}")
        rows.append({"path": relative, "sha256": sha256_file(path), "integrity": "PASS"})
    return rows


def telemetry_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    available = {
        "B3_TELEMETRY": {"sampler_q_and_exposure", "global_ppo_dynamics", "failure_relative_behavior"},
        "H2_CONFIRMATION": {"sampler_q_and_exposure", "global_ppo_dynamics", "failure_relative_behavior", "milestone_endpoints"},
        "S1_TR": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints"},
        "S2_ANCHOR": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints"},
        "R1_CONSERVATIVE": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints"},
        "D3_KLR": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints", "intervention_events"},
        "D5_KLB": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints", "intervention_events"},
        "P3_PP": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints", "intervention_events"},
        "P4_PP": {"sampler_q_and_exposure", "global_ppo_dynamics", "milestone_endpoints", "intervention_events"},
        "B4_SELECTOR": {"milestone_endpoints", "intervention_events"},
    }
    rows: list[dict[str, str]] = []
    for experiment in config["experiments"]:
        row = {"experiment_id": experiment["id"]}
        for dimension in config["telemetry_dimensions"]:
            row[dimension] = "YES" if dimension in available.get(experiment["id"], set()) else "NO"
        rows.append(row)
    return rows


def build(config: dict[str, Any], archive_root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    audits = archive_audit(config, archive_root)
    sources = source_audit(config)

    registry = []
    intervention_rows = []
    for experiment in config["experiments"]:
        original = experiment["paired_gains_original"]
        candidate = experiment["paired_gains_candidate"]
        original_stats = dispersion(original)
        candidate_stats = dispersion(candidate)
        registry.append(
            {
                "experiment_id": experiment["id"],
                "arms": experiment["arms"],
                "seeds": experiment["seeds"],
                "budget_m": experiment["budget_m"],
                "decision": experiment["decision"],
                "intervention": experiment["intervention"],
                "original_gains": fmt(original),
                "candidate_gains": fmt(candidate),
                "contribution": experiment["contribution"],
            }
        )
        intervention_rows.append(
            {
                "experiment_id": experiment["id"],
                "intervention": experiment["intervention"],
                "decision": experiment["decision"],
                "n_independent_seeds": max(len(original), len(candidate)),
                "original_mean_gain": original_stats["mean"],
                "candidate_mean_gain": candidate_stats["mean"],
                "original_worst_gain": original_stats["minimum"],
                "candidate_worst_gain": candidate_stats["minimum"],
                "original_range": original_stats["range"],
                "candidate_range": candidate_stats["range"],
                "interpretation": experiment["contribution"],
            }
        )

    write_csv(
        output / "run_registry.csv",
        ["experiment_id", "arms", "seeds", "budget_m", "decision", "intervention", "original_gains", "candidate_gains", "contribution"],
        registry,
    )
    write_csv(
        output / "intervention_evidence_matrix.csv",
        ["experiment_id", "intervention", "decision", "n_independent_seeds", "original_mean_gain", "candidate_mean_gain", "original_worst_gain", "candidate_worst_gain", "original_range", "candidate_range", "interpretation"],
        intervention_rows,
    )
    telemetry = telemetry_rows(config)
    write_csv(output / "telemetry_availability_matrix.csv", ["experiment_id", *config["telemetry_dimensions"]], telemetry)
    write_csv(
        output / "candidate_signal_ranking.csv",
        ["rank", "name", "status", "support", "missing"],
        config["candidate_hypotheses"],
    )

    chain = "# DRTP B5 cross-cohort mechanism evidence\n\n"
    chain += "## Frozen conclusion\n\n"
    chain += "The existing evidence does **not** authorize another sampler-only or global actor-update patch. "
    chain += "Across independent cohorts, locally promising interventions repeatedly failed to preserve both upper-tail gain and lower-tail reliability.\n\n"
    chain += "The only remaining actionable mechanism family is **failure-group-conditioned credit assignment / gradient interference**. "
    chain += "This is a hypothesis generated by intervention counterexamples, not a demonstrated mechanism. "
    chain += "Generic MAPPO optimization-basin sensitivity remains the null hypothesis.\n\n"
    chain += "## Evidence logic\n\n"
    chain += "1. B3 and H2 did not replicate a sampler→exposure→behavior→outcome chain.\n"
    chain += "2. TR and uniform anchoring constrained sampler feedback but did not generalize across seeds.\n"
    chain += "3. KLR could rescue the lower tail while damaging failure-condition performance on a previously strong seed; nominal performance need not collapse with it.\n"
    chain += "4. KLB did not rescue the next cohort, so global KL control is not a sufficient cause-level solution.\n"
    chain += "5. PP-DRTP strongly rescued one pilot and then reversed on an independent five-seed cohort.\n"
    chain += "6. Existing logs lack per-failure-group critic residual, advantage, and gradient-conflict telemetry, so the remaining hypothesis is presently untestable.\n\n"
    chain += "## Scientific boundary\n\n"
    chain += "No final-score correlation is treated as a mechanism. Training seed is the independent unit; PPO updates and evaluation episodes are technical repetitions.\n"
    write_text(output / "mechanism_chain_evidence.md", chain)

    missing = "# Missing evidence for B5\n\n"
    missing += "The current archive set is rich in global PPO, sampler, intervention, and endpoint evidence but has a systematic blind spot at the credit-assignment layer.\n\n"
    missing += "Required read-only telemetry:\n\n"
    missing += "- per update × failure group: sample count, return target, value prediction, TD/value residual, value loss and explained variance;\n"
    missing += "- raw and normalized advantage mean, SD and frozen quantiles by group;\n"
    missing += "- actor and critic gradient norm by group, plus pairwise cosine/conflict rate between groups;\n"
    missing += "- the existing sampler q/exposure and failure-relative behavior/task-support telemetry on the same update axis;\n"
    missing += "- matched UTR controls with the identical logger;\n"
    missing += "- deterministic save/resume and telemetry-on/off trajectory equivalence.\n\n"
    missing += "These fields are log-only. They must not enter actor/critic inputs, PPO buffers, rewards, or sampler decisions.\n"
    write_text(output / "missing_evidence.md", missing)

    decision = f"# B5 GO / NO-GO\n\n**Decision:** `{config['decision']}`.\n\n"
    decision += "- Another algorithm modification is **not authorized**.\n"
    decision += "- New training is **not authorized by this artifact**.\n"
    decision += "- A single observational telemetry cohort may be prepared for later human authorization.\n"
    decision += "- Mainline A remains frozen and is not modified by B5.\n\n"
    decision += "The closed single-cause routes are sampler-step magnitude, uniform anchoring, global KL rollback/backtracking, paired-probe sampler evidence, and checkpoint-population selection. "
    decision += "They remain useful negative evidence, but none justifies another parameter variation.\n"
    write_text(output / "B5_GO_NO_GO.md", decision)

    cohort = config["observational_cohort"]
    contract = "# B5 observational cohort contract (preparation only)\n\n"
    contract += f"**Status:** `{cohort['status']}`. This contract does not authorize training.\n\n"
    contract += "## Frozen design\n\n"
    contract += f"- Arms: `{', '.join(cohort['arms'])}`.\n"
    contract += f"- Provisional seeds: `{', '.join(map(str, cohort['provisional_seeds']))}`; {cohort['seed_status']}.\n"
    contract += f"- Ceiling: `{cohort['ceiling_env_steps']}` environment steps; milestones `{', '.join(map(str, cohort['milestones_env_steps']))}`.\n"
    contract += "- Same paired seeds, environment, reward, PPO, actor/critic, failure semantics, sampler parameters and frozen evaluation tape.\n"
    contract += "- No early stopping, best-checkpoint promotion, seed replacement, performance rerun or algorithm change.\n"
    contract += f"- The 0.5M milestone is descriptive only. {cohort['reason_for_1m_ceiling']}\n\n"
    contract += "## Mechanism GO\n\nAll conditions are required:\n\n"
    for condition in cohort["mechanism_go"]:
        contract += f"- {condition};\n"
    contract += f"\n**NO-GO:** {cohort['mechanism_no_go']}\n"
    write_text(output / "B5_OBSERVATIONAL_COHORT_CONTRACT.md", contract)

    executive = "# B 线后续执行方案（B5）\n\n"
    executive += "## 当前判断\n\n"
    executive += "原始 DRTP 的高收益能力是真实存在的，但截至目前没有一个稳定化版本同时跨独立 cohort 保住高收益和下尾可靠性。"
    executive += "TR、uniform anchor、KL rollback/backtracking、paired probe 与 population selector 均已提供有效反例，因此不再做参数微调或第三个局部补丁。\n\n"
    executive += "## 已完成\n\n"
    executive += "- 对 10 份关键结果包完成 SHA256、内部裁决文件和决策一致性审计；\n"
    executive += "- 建立跨 cohort 的干预—分叉—结果证据矩阵；\n"
    executive += "- 冻结唯一剩余可检验假设：故障组条件下的 credit assignment / gradient interference；\n"
    executive += "- 保留通用 MAPPO optimization-basin sensitivity 作为零假设；\n"
    executive += "- 明确本阶段未改算法、未训练、未触碰主线 A。\n\n"
    executive += "## 下一阶段门控\n\n"
    executive += "1. 先实现只读的 group-conditioned value/advantage/gradient telemetry，并完成 trajectory equivalence、RNG、save/resume 和开销验收。\n"
    executive += "2. 技术验收通过后，才允许另行人工授权云端 `UTR / Original DRTP × 5 clean paired seeds × 1M` 观测 cohort。\n"
    executive += "3. 只有完整机制链在至少 2/5 个不利 DRTP seed 中重复、且 paired UTR 不存在同等模式，才允许设计一个最小新算法。\n"
    executive += "4. 若 1M 仍无完整机制链，B 线算法开发永久停止；不再以新 gate、阈值或 seed 重跑延长项目。\n"
    executive += "5. 即使 B 线成功或失败，主线 A 的论文证据和投稿时间表均保持独立。\n"
    write_text(output / "B5_EXECUTIVE_PLAN_ZH.md", executive)

    artifact_paths = [
        output / "run_registry.csv",
        output / "intervention_evidence_matrix.csv",
        output / "telemetry_availability_matrix.csv",
        output / "candidate_signal_ranking.csv",
        output / "mechanism_chain_evidence.md",
        output / "missing_evidence.md",
        output / "B5_GO_NO_GO.md",
        output / "B5_OBSERVATIONAL_COHORT_CONTRACT.md",
        output / "B5_EXECUTIVE_PLAN_ZH.md",
    ]
    manifest = {
        "schema_version": config["schema_version"],
        "decision": config["decision"],
        "training_started": False,
        "algorithm_modification_authorized": False,
        "mainline_a_modified": False,
        "archive_audit": audits,
        "source_document_audit": sources,
        "artifacts": {path.name: sha256_file(path) for path in artifact_paths},
    }
    write_text(output / "B5_ATLAS_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    build(config, args.archive_root, args.output_dir)
    print(json.dumps({"decision": config["decision"], "output": str(args.output_dir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
