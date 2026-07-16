from __future__ import annotations

import csv
import hashlib
import importlib.util
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "reproducibility_checksum_manifest.csv"
OUT_MD = ROOT / "docs" / "reproducibility_checksum_manifest.md"


EXCLUDED_DYNAMIC = {
    "docs/paper_asset_build_report.md",
    "docs/supplemental_data_readme.md",
    "docs/supplemental_csv_schema_audit.md",
    "results/supplemental_csv_schema_audit.csv",
    "docs/result_provenance_audit.md",
    "results/result_provenance_audit.csv",
    "docs/reproducibility_checksum_manifest.md",
    "results/reproducibility_checksum_manifest.csv",
    "docs/reproducibility_checksum_verification.md",
    "results/reproducibility_checksum_verification.csv",
}


@dataclass(frozen=True)
class ChecksumRow:
    path: str
    artifact_group: str
    size_bytes: int
    sha256: str


def load_reproducibility_lists() -> tuple[list[str], list[str]]:
    script_path = ROOT / "scripts" / "check_reproducibility_artifacts.py"
    spec = importlib.util.spec_from_file_location("check_reproducibility_artifacts", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load check_reproducibility_artifacts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.REQUIRED_FILES), list(module.REQUIRED_SCRIPTS)


def group_for(rel: str) -> str:
    if rel.endswith(".pt"):
        return "checkpoint"
    if rel.startswith("paper_latex"):
        return "latex"
    if rel.startswith("docs/"):
        return "documentation"
    if rel.startswith("results/figures/"):
        return "figure"
    if rel.startswith("results/"):
        return "result"
    if rel.startswith("scripts/"):
        return "script"
    if rel.startswith("envs/"):
        return "environment_adapter"
    return "other"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_rows() -> list[ChecksumRow]:
    required_files, required_scripts = load_reproducibility_lists()
    rels = []
    for rel in [*required_files, *required_scripts]:
        if rel in EXCLUDED_DYNAMIC:
            continue
        if rel not in rels:
            rels.append(rel)

    rows = []
    missing = []
    for rel in rels:
        path = ROOT / rel
        if not path.exists() or path.stat().st_size <= 0:
            missing.append(rel)
            continue
        rows.append(
            ChecksumRow(
                path=rel,
                artifact_group=group_for(rel),
                size_bytes=path.stat().st_size,
                sha256=sha256_file(path),
            )
        )
    if missing:
        raise FileNotFoundError("missing files for checksum manifest: " + ", ".join(missing))
    return rows


def write_csv(rows: list[ChecksumRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ChecksumRow.__dataclass_fields__.keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_report(rows: list[ChecksumRow]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    bytes_by_group: dict[str, int] = {}
    for row in rows:
        counts[row.artifact_group] = counts.get(row.artifact_group, 0) + 1
        bytes_by_group[row.artifact_group] = bytes_by_group.get(row.artifact_group, 0) + row.size_bytes

    lines = [
        "# Reproducibility Checksum Manifest",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Record SHA256 hashes and file sizes for the stable reproducibility package artifacts.",
        "Dynamic build reports and self-referential audit outputs are excluded to avoid circular hashes.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"artifacts_hashed = {len(rows)}",
        *[f"{key} = {counts[key]}" for key in sorted(counts)],
        "```",
        "",
        "## Size by Group",
        "",
        "| Group | Files | Size MB |",
        "|---|---:|---:|",
    ]
    for group in sorted(counts):
        lines.append(f"| {group} | {counts[group]} | {bytes_by_group[group] / (1024 * 1024):.3f} |")

    lines.extend(
        [
            "",
            "## Excluded Dynamic Artifacts",
            "",
            "```text",
            *sorted(EXCLUDED_DYNAMIC),
            "```",
            "",
            "## Use Boundary",
            "",
            "```text",
            "Use this manifest after packaging or moving the project to verify that stable artifacts are unchanged.",
            "Regenerate it after rerunning experiments, changing manuscript text, or updating figures/tables.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_report(rows)
    print(OUT_CSV)
    print(OUT_MD)
    print(f"artifacts hashed: {len(rows)}")


if __name__ == "__main__":
    main()
