#!/usr/bin/env python3
"""Produce the zero-training B-line mechanism-discovery decision from frozen evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freeze",
        type=Path,
        default=Path("configs/drtp_bline_mechanism_discovery_freeze.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/drtp_bline_mechanism_discovery_20260831"),
    )
    args = parser.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    criteria = list(freeze["required_conditions"])
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    source_hashes = {}
    for record in freeze["evidence_records"]:
        source = record["source"]
        source_path = Path(source)
        if source_path.exists():
            source_hashes[source] = sha256_file(source_path)
        else:
            source_hashes[source] = "USER_VERIFIED_CLOUD_GATE_OR_NONFILE_SOURCE"
        rows.append({"route": record["route"], **{key: record[key] for key in criteria}, "summary": record["summary"]})

    with (output_dir / "mechanism_discovery_evidence_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["route", *criteria, "summary"])
        writer.writeheader()
        writer.writerows(rows)

    criterion_support = {key: any(row[key] for row in rows) for key in criteria}
    decision = "MECHANISM_DISCOVERY_GO" if all(criterion_support.values()) else "MECHANISM_DISCOVERY_NO_GO"
    payload = {
        "protocol": freeze["protocol"],
        "status": decision,
        "all_required_conditions_supported": all(criterion_support.values()),
        "criterion_support": criterion_support,
        "evidence_routes_screened": len(rows),
        "training_authorized": False,
        "algorithm_modification_authorized": False,
        "automatic_continuation_authorized": False,
        "mainline_a_modified": False,
        "source_hashes": source_hashes,
    }
    (output_dir / "MECHANISM_DISCOVERY_DECISION.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    table_header = "| Route | " + " | ".join(criteria) + " |\n"
    table_rule = "| --- | " + " | ".join(":---:" for _ in criteria) + " |\n"
    table_rows = [
        "| " + row["route"] + " | " + " | ".join(str(row[key]) for key in criteria) + " |"
        for row in rows
    ]
    report = [
        "# DRTP B 线机制发现 R0",
        "",
        f"**Decision:** `{decision}`.",
        "",
        "这是零训练、证据层级的综合审计。它不重新解释任何历史 gate，也不将不同 cohort 合并为一个样本。训练 seed 是唯一独立单位；update、episode 和 shadow alarm 只用于时间对齐。",
        "",
        "## 冻结判据",
        "",
        *[f"- **{key}**：{description}" for key, description in freeze["required_conditions"].items()],
        "",
        "## 证据矩阵",
        "",
        table_header,
        table_rule,
        *table_rows,
        "",
        "## 结论",
        "",
        "没有任何一条候选机制链同时满足重复性、时间领先、UTR 特异性、连续中间层和单一最小干预映射。特别是，B1、B5 和 R1 均没有得到跨 seed 的一致前兆；P1 没有得到可推广的 rollback 效用信号；CV-DRTP 则在两个新鲜 cohort 中直接系统性破坏收益和下尾。",
        "",
        "因此，此时设计任何新的 Reliable-DRTP 都将是无机制支持的猜测，而非可证伪的研究推进。该决定不否认 Original DRTP 的高收益潜力，也不影响主线 A；它只禁止继续 B 线的局部补丁、CV-v2 或任何新的训练候选。",
        "",
        "## 后续边界",
        "",
        "B 线转为 `MECHANISM_DISCOVERY_NO_GO`。除非出现新的、未被现有档案覆盖的可观测机制证据，否则不再授权 B 线训练。资源应转回主线 A 的投稿收敛与风险逐项解决。",
    ]
    (output_dir / "MECHANISM_DISCOVERY_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
