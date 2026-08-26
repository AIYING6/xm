"""Build the frozen PAPER-Q2 evidence lineage without running experiments."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "paper_q2_closeout"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def heldout_rows() -> list[dict[str, object]]:
    text = (ROOT / "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md").read_text(encoding="utf-8")
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        if not line.startswith("| UTR-SG |") and not line.startswith("| DRTP-SG |"):
            continue
        parts = [item.strip() for item in line.strip().strip("|").split("|")]
        rows.append({
            "contract": "heldout_10M",
            "budget_env_steps": 10000128,
            "tape": "430000-430099",
            "method": parts[0],
            "seed": int(parts[1]),
            "J_nominal": float(parts[2]),
            "J_F0": float(parts[3]),
            "J_OOD_mean": float(parts[4]),
            "J_OOD_worst": float(parts[5]),
            "failure_exposure": float(parts[6]),
            "collision": float(parts[7]),
            "timeout": float(parts[8]),
            "constraint": 0.0,
            "source": "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md",
        })
    if len(rows) != 6:
        raise RuntimeError(f"expected 6 held-out rows, found {len(rows)}")
    return rows


def development_rows() -> list[dict[str, object]]:
    text = (ROOT / "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md").read_text(encoding="utf-8")
    pattern = re.compile(r"^\| `(?P<metric>J_(?:nominal|F0|OOD_mean|OOD_worst))` \| (?P<u1>[\d.]+) -> (?P<d1>[\d.]+) \| (?P<u2>[\d.]+) -> (?P<d2>[\d.]+) \|", re.MULTILINE)
    values: dict[str, tuple[float, float, float, float]] = {}
    for match in pattern.finditer(text):
        values[match.group("metric")] = tuple(float(match.group(name)) for name in ("u1", "d1", "u2", "d2"))
    expected = {"J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst"}
    if set(values) != expected:
        raise RuntimeError(f"development metric parse failed: {sorted(values)}")
    rows: list[dict[str, object]] = []
    for seed, idx in ((1901, 0), (1902, 2)):
        for method, offset in (("UTR-SG", 0), ("DRTP-SG", 1)):
            rows.append({
                "contract": "development_3M",
                "budget_env_steps": 3000064,
                "tape": "420000-420099",
                "method": method,
                "seed": seed,
                **{metric: values[metric][idx + offset] for metric in sorted(expected)},
                "failure_exposure": "NA",
                "collision": "NA",
                "timeout": "NA",
                "constraint": "NA",
                "source": "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md",
            })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paired_rows = development_rows() + heldout_rows()
    paired_fields = [
        "contract", "budget_env_steps", "tape", "method", "seed",
        "J_nominal", "J_F0", "J_OOD_mean", "J_OOD_worst",
        "failure_exposure", "collision", "timeout", "constraint", "source",
    ]
    write_csv(OUT / "final_paired_absolute_results.csv", paired_fields, paired_rows)

    edges = [
        {"edge_id": "E01", "from_path": "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md", "from_anchor": "Final 3M performance + seed consistency", "transformation": "parse absolute UTR/DRTP values", "to_path": "artifacts/paper_q2_closeout/final_paired_absolute_results.csv", "to_anchor": "development_3M rows", "contract": "development_3M", "independent_unit": "training_seed", "audit_rule": "seeds 1901/1902 retained"},
        {"edge_id": "E02", "from_path": "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md", "from_anchor": "Final-10M results", "transformation": "parse all six final-checkpoint rows", "to_path": "artifacts/paper_q2_closeout/final_paired_absolute_results.csv", "to_anchor": "heldout_10M rows", "contract": "heldout_10M", "independent_unit": "training_seed", "audit_rule": "seed2002 retained"},
        {"edge_id": "E03", "from_path": "artifacts/paper_q2_closeout/final_paired_absolute_results.csv", "from_anchor": "method-paired rows", "transformation": "DRTP minus UTR within seed and contract", "to_path": "artifacts/paper_q2_closeout/final_seed_level_results.csv", "to_anchor": "five paired deltas", "contract": "stratified", "independent_unit": "training_seed", "audit_rule": "no cross-seed pairing"},
        {"edge_id": "E04", "from_path": "artifacts/paper_q2_closeout/final_seed_level_results.csv", "from_anchor": "five paired deltas", "transformation": "mean/median/SD/IQR/MAD/win/worst", "to_path": "artifacts/paper_q2_closeout/final_reliability_results.csv", "to_anchor": "four primary metrics", "contract": "cross-stratum descriptive", "independent_unit": "training_seed", "audit_rule": "not confirmatory inference"},
        {"edge_id": "E05", "from_path": "artifacts/paper_q2_p1/main_table.csv", "from_anchor": "five absolute pooled rows", "transformation": "identity copy", "to_path": "artifacts/paper_q2_closeout/final_main_results.csv", "to_anchor": "five absolute pooled rows", "contract": "stratified", "independent_unit": "training_seed", "audit_rule": "3M/10M labels preserved"},
        {"edge_id": "E06", "from_path": "artifacts/paper_q2_p1/statistical_summary.json", "from_anchor": "primary_metrics + contract_stratified", "transformation": "field-preserving export", "to_path": "artifacts/paper_q2_closeout/final_stratified_statistics.csv", "to_anchor": "eight contract-metric rows", "contract": "stratified", "independent_unit": "training_seed", "audit_rule": "n=2 and n=3 explicit"},
        {"edge_id": "E07", "from_path": "docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "from_anchor": "topology/path telemetry", "transformation": "claim-bounded mechanism synthesis", "to_path": "artifacts/paper_q2_closeout/claim_evidence_matrix.csv", "to_anchor": "C1", "contract": "S2 frozen", "independent_unit": "episode telemetry", "audit_rule": "no blackout/recovery claim"},
        {"edge_id": "E08", "from_path": "docs/DRTP_REL_A0_FINAL_REPORT.md", "from_anchor": "multi-tape reliability decision", "transformation": "reliability boundary", "to_path": "artifacts/paper_q2_closeout/claim_evidence_matrix.csv", "to_anchor": "C4", "contract": "zero-training reliability audit", "independent_unit": "training_seed", "audit_rule": "policy-basin cause remains unproven"},
        {"edge_id": "E09", "from_path": "artifacts/paper_q2_closeout/claim_evidence_matrix.csv", "from_anchor": "C1-C9", "transformation": "section routing", "to_path": "paper/q2_final_zh/02_evidence_table.md", "to_anchor": "C1-C9", "contract": "manuscript", "independent_unit": "claim", "audit_rule": "unsupported C9 prohibited"},
    ]
    write_csv(OUT / "evidence_chain_edges.csv", list(edges[0]), edges)

    sources = [
        ("development_report", "docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md", "upstream result report"),
        ("heldout_report", "docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md", "upstream result report"),
        ("publication_viability", "docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md", "historical paired audit"),
        ("topology_mechanism", "docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md", "mechanism report"),
        ("reliability_a0", "docs/DRTP_REL_A0_FINAL_REPORT.md", "multi-tape reliability audit"),
        ("p1_main", "artifacts/paper_q2_p1/main_table.csv", "intermediate machine table"),
        ("p1_seed", "artifacts/paper_q2_p1/seed_level_results.csv", "intermediate seed table"),
        ("p1_stats", "artifacts/paper_q2_p1/statistical_summary.json", "canonical statistical calculation"),
        ("p1_provenance", "artifacts/paper_q2_p1/result_provenance.json", "intermediate provenance"),
        ("p1_statistics_report", "docs/PAPER_Q2_P1_STATISTICAL_RESULTS.md", "corrected prose statistics table"),
        ("final_main", "artifacts/paper_q2_closeout/final_main_results.csv", "closeout table"),
        ("final_seed", "artifacts/paper_q2_closeout/final_seed_level_results.csv", "closeout seed table"),
        ("final_reliability", "artifacts/paper_q2_closeout/final_reliability_results.csv", "closeout reliability table"),
        ("final_stratified", "artifacts/paper_q2_closeout/final_stratified_statistics.csv", "contract-stratified statistics"),
        ("final_absolute", "artifacts/paper_q2_closeout/final_paired_absolute_results.csv", "all paired absolute rows"),
        ("final_decision", "artifacts/paper_q2_closeout/final_submission_decision.json", "immutable closeout decision"),
        ("claim_matrix", "artifacts/paper_q2_closeout/claim_evidence_matrix.csv", "claim routing"),
        ("figure_manifest", "artifacts/paper_q2_closeout/figure_source_manifest.csv", "figure routing"),
        ("manuscript_manifest", "artifacts/paper_q2_closeout/manuscript_source_manifest.csv", "manuscript source policy"),
        ("edge_manifest", "artifacts/paper_q2_closeout/evidence_chain_edges.csv", "lineage edges"),
        ("transform_p1", "scripts/build_paper_q2_p1.py", "upstream transformation code"),
        ("transform_closeout", "scripts/build_paper_q2_closeout.py", "closeout transformation code"),
        ("transform_lineage", "scripts/build_paper_q2_evidence_chain.py", "lineage builder code"),
        ("verify_lineage", "scripts/verify_paper_q2_evidence_chain.py", "lineage verification code"),
    ]
    records = []
    for source_id, rel, role in sources:
        path = ROOT / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        records.append({
            "source_id": source_id,
            "path": rel,
            "role": role,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        })
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    manifest = {
        "schema": "paper-q2-evidence-chain-manifest-v1",
        "evidence_freeze_commit": "1680b21",
        "manifest_built_from_commit": commit,
        "training_started": False,
        "independent_unit": "training_seed",
        "contract_rule": "development_3M and heldout_10M remain separate; cross-stratum summaries are descriptive only",
        "historical_decisions_required": ["DRTP_Q2_LIMITATION_ONLY", "held-out FAIL", "development NO-GO"],
        "required_seeds": [1901, 1902, 2001, 2002, 2003],
        "sources": records,
    }
    with (OUT / "evidence_chain_manifest.json").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        handle.write(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"built evidence chain with {len(records)} hashed sources and {len(edges)} edges")


if __name__ == "__main__":
    main()
