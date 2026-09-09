"""Prune the DRTP archive to paper-closure evidence only.

This script is intentionally restricted to the archive generated on 2026-09-09.
It never touches Downloads, Temp, or the repository source/result trees.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil


ROOT = Path(r"D:\File\DRTP_RESEARCH_DATA_ARCHIVE_20260909_FINAL_V3")
EXPECTED_PROTOCOL = "DRTP-RESEARCH-DATA-ARCHIVE-20260909-V1"
FINAL_PROTOCOL = "DRTP-RESEARCH-DATA-ARCHIVE-20260909-PAPER-CLOSURE-V2"
ORIGINAL_PRUNE_FILES = 25681
ORIGINAL_PRUNE_LOGICAL_BYTES = 132650637669

REMOVE_TIERS = (
    "03_EXCLUDED_OR_NONINFORMATIVE",
    "04_DEVELOPMENT_DIAGNOSTICS",
    "10_HISTORICAL_RESULT_ARCHIVES",
    "30_MIXED_EVIDENCE_SNAPSHOTS",
)

INCOMPLETE_ARCHIVES = (
    Path(r"D:\File\ZZ_INCOMPLETE_DO_NOT_USE_DRTP_ARCHIVE_ATTEMPT1"),
    Path(r"D:\File\ZZ_INCOMPLETE_DO_NOT_USE_DRTP_ARCHIVE_ATTEMPT2"),
    Path(r"D:\File\ZZ_INCOMPLETE_DO_NOT_USE_DRTP_ARCHIVE_ATTEMPT3"),
)

KEEP_PACKAGES = {
    "DRTP_FINAL_EVIDENCE_HELDOUT_OOD_EVALUATION_V1.zip",
    "DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_PREFLIGHT.zip",
    "DRTP_SEMANTIC_ABLATION_FACTORIAL_COMPLETION_10M_V1.zip",
    "DRTP_STABILIZATION_FINAL_CONFIRMATION_10M_74036fb9.zip",
    "DRTP_STABILIZATION_FINAL_CONFIRMATION_AGGREGATE_REPAIR_V1_56bc5add.zip",
    "DRTP_STABILIZATION_INDEPENDENT_REPLICATION_10M_bcdcace3.zip",
    "DRTP_STABILIZATION_INDEPENDENT_REPLICATION_AGGREGATE_REPAIR_V1.zip",
}

KEEP_GOVERNANCE_FILES = {
    "configs/drtp_final_evidence_p0_heldout_ood_freeze_20260906.json",
    "configs/drtp_final_external_comparator_freeze_20260906.json",
    "configs/drtp_plr_external_formal_freeze_20260906.json",
    "configs/drtp_stabilization_evidence_governance_20260906.json",
    "configs/drtp_stabilization_final_development_evidence.json",
    "configs/drtp_stabilization_final_freeze.json",
    "configs/drtp_stabilization_final_method_selection_20260906.json",
    "configs/drtp_stabilization_independent_replication_freeze.json",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_FINAL_EXTERNAL_COMPARATOR_CONTRACT.json",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_FINAL_EXTERNAL_COMPARATOR_CONTRACT.md",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_FINAL_FROZEN_CLAIM_EVIDENCE_MATRIX.md",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_FINAL_PAPER_EVIDENCE_TABLES.md",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_FINAL_REPRODUCIBILITY_LEDGER.json",
    "docs/drtp_final_evidence_preparation_20260906_complete/DRTP_UTR_FINAL_FAIRNESS_AUDIT.md",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_FINAL_EVIDENCE_P0_HELDOUT_OOD_CONTRACT_20260906.md",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_STABILIZATION_A_COHORT_INTERPRETATION_20260906.md",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_STABILIZATION_DOUBLE_COHORT_METHOD_SELECTION_20260906.md",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_STABILIZATION_FINAL_FREEZE.md",
    "docs/drtp_stabilization_final_freeze_20260905/DRTP_STABILIZATION_INDEPENDENT_REPLICATION_FREEZE.md",
    "docs/drtp_submission_ready/DRTP_FINAL_EVIDENCE_REGISTER_20260908.md",
    "docs/drtp_submission_ready/DRTP_FINAL_FIGURE_CONTRACT_V1.md",
}

KEEP_DATASET_CLASSES = {
    "formal_primary_confirmatory_cohort_A",
    "formal_independent_confirmatory_cohort_B",
    "formal_training_excluded_structural_evaluation",
    "formal_external_positioning_not_primary_causal_control",
    "supporting_exposure_manipulation_sensitivity",
    "supporting_factorial_ablation_not_component_necessity_proof",
}


def ensure_within_root(path: Path, root: Path) -> None:
    resolved_path = str(path.resolve())
    resolved_root = str(root.resolve())
    if os.path.commonpath((resolved_path, resolved_root)) != resolved_root:
        raise RuntimeError(f"refusing target outside root: {path}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def files_under(path: Path) -> list[Path]:
    return [item for item in path.rglob("*") if item.is_file()] if path.is_dir() else []


def empty_directories(root: Path) -> None:
    directories = sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass


def remove_tree(path: Path) -> None:
    """Remove an exact Windows tree, including legacy paths longer than MAX_PATH."""
    resolved = path.resolve()
    extended = Path("\\\\?\\" + str(resolved)) if os.name == "nt" else resolved
    shutil.rmtree(extended)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    build_report_path = ROOT / "00_INDEX" / "ARCHIVE_BUILD_REPORT.json"
    if not ROOT.is_dir() or not build_report_path.is_file():
        raise FileNotFoundError("expected final archive is absent")
    build_report = json.loads(build_report_path.read_text(encoding="utf-8"))
    if build_report.get("protocol") not in {EXPECTED_PROTOCOL, FINAL_PROTOCOL}:
        raise RuntimeError("archive protocol mismatch")
    if str(ROOT.resolve()) != str(Path(r"D:\File\DRTP_RESEARCH_DATA_ARCHIVE_20260909_FINAL_V3").resolve()):
        raise RuntimeError("archive root mismatch")

    deletion_rows: list[dict[str, object]] = []
    for tier in REMOVE_TIERS:
        target = ROOT / tier
        ensure_within_root(target, ROOT)
        for path in files_under(target):
            deletion_rows.append({
                "target": str(path), "bytes": path.stat().st_size,
                "reason": f"remove_non_paper_tier:{tier}", "source_roots_untouched": True,
            })

    package_root = ROOT / "20_REPRODUCIBILITY_PACKAGES"
    retained_packages: list[Path] = []
    for path in files_under(package_root):
        ensure_within_root(path, ROOT)
        if path.name in KEEP_PACKAGES:
            retained_packages.append(path)
        else:
            deletion_rows.append({
                "target": str(path), "bytes": path.stat().st_size,
                "reason": "remove_unrelated_or_obsolete_execution_package", "source_roots_untouched": True,
            })

    governance_root = ROOT / "40_EVIDENCE_GOVERNANCE"
    retained_governance: list[Path] = []
    for path in files_under(governance_root):
        relative = path.relative_to(governance_root).as_posix()
        ensure_within_root(path, ROOT)
        if relative in KEEP_GOVERNANCE_FILES:
            retained_governance.append(path)
        else:
            deletion_rows.append({
                "target": str(path), "bytes": path.stat().st_size,
                "reason": "remove_historical_or_nonclosure_governance", "source_roots_untouched": True,
            })

    current_rows = read_csv(ROOT / "00_INDEX" / "CURRENT_EVIDENCE_REGISTER.csv")
    retained_current = [row for row in current_rows if row["classification"] in KEEP_DATASET_CLASSES]
    removed_dataset_names = {row["dataset"][:-7] for row in current_rows if row not in retained_current}
    extracted_root = ROOT / "00_INDEX" / "EXTRACTED_REPORTS"
    for name in removed_dataset_names:
        target = extracted_root / name
        ensure_within_root(target, ROOT)
        for path in files_under(target):
            deletion_rows.append({
                "target": str(path), "bytes": path.stat().st_size,
                "reason": "remove_extracted_report_for_excluded_dataset", "source_roots_untouched": True,
            })

    for path in INCOMPLETE_ARCHIVES:
        if path.exists():
            expected_parent = Path(r"D:\File").resolve()
            if path.parent.resolve() != expected_parent or not path.name.startswith("ZZ_INCOMPLETE_DO_NOT_USE_DRTP_ARCHIVE_ATTEMPT"):
                raise RuntimeError(f"unexpected incomplete archive target: {path}")
            for item in files_under(path):
                deletion_rows.append({
                    "target": str(item), "bytes": item.stat().st_size,
                    "reason": "remove_incomplete_archive_attempt", "source_roots_untouched": True,
                })

    summary = {
        "mode": "execute" if args.execute else "dry_run",
        "files_to_delete": len(deletion_rows),
        "logical_bytes_to_unlink": sum(int(row["bytes"]) for row in deletion_rows),
        "retained_current_datasets": len(retained_current),
        "retained_execution_packages": len(retained_packages),
        "retained_governance_files": len(retained_governance),
        "source_roots_untouched": False,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not args.execute:
        return

    pruning_audit_path = ROOT / "00_INDEX" / "PRUNING_AUDIT.csv"
    if deletion_rows:
        write_csv(pruning_audit_path, deletion_rows)

    for tier in REMOVE_TIERS:
        target = ROOT / tier
        if target.exists():
            ensure_within_root(target, ROOT)
            shutil.rmtree(target)

    for path in list(files_under(package_root)):
        if path.name not in KEEP_PACKAGES:
            path.unlink()
    empty_directories(package_root)

    for path in list(files_under(governance_root)):
        if path.relative_to(governance_root).as_posix() not in KEEP_GOVERNANCE_FILES:
            path.unlink()
    empty_directories(governance_root)

    for name in removed_dataset_names:
        target = extracted_root / name
        if target.exists():
            shutil.rmtree(target)

    for path in INCOMPLETE_ARCHIVES:
        if path.exists():
            remove_tree(path)

    for obsolete_index in ("HISTORICAL_ARCHIVE_AUDIT.csv", "ZERO_LENGTH_CANDIDATES.csv"):
        index_path = ROOT / "00_INDEX" / obsolete_index
        if index_path.exists():
            index_path.unlink()

    write_csv(ROOT / "00_INDEX" / "CURRENT_EVIDENCE_REGISTER.csv", retained_current)
    sums = "\n".join(
        f"{row['sha256']}  {row['archive_location']}/{row['dataset']}" for row in retained_current
    ) + "\n"
    (ROOT / "00_INDEX" / "SHA256SUMS_CURRENT_EVIDENCE.txt").write_text(sums, encoding="ascii")

    retained_package_rows = []
    for path in sorted(files_under(package_root), key=lambda p: str(p).lower()):
        retained_package_rows.append({
            "archive_path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "role": "paper_closure_reproducibility_package",
        })
    write_csv(ROOT / "00_INDEX" / "REPRODUCIBILITY_PACKAGE_AUDIT.csv", retained_package_rows)

    old_manifest = read_csv(ROOT / "00_INDEX" / "MASTER_FILE_MANIFEST.csv")
    retained_manifest = [row for row in old_manifest if (ROOT / row["archive_path"]).is_file()]
    write_csv(ROOT / "00_INDEX" / "MASTER_FILE_MANIFEST.csv", retained_manifest)

    retained_files = [path for path in ROOT.rglob("*") if path.is_file()]
    build_report.update({
        "protocol": FINAL_PROTOCOL,
        "pruned_to_paper_closure": True,
        "original_files_modified_or_deleted": True,
        "source_roots_untouched": False,
        "current_registered_datasets": len(retained_current),
        "historical_result_archives_scanned": 0,
        "historical_result_archives_included": 0,
        "protocol_packages_scanned": len(retained_package_rows),
        "unique_protocol_packages_included": len(retained_package_rows),
        "manifested_files": len(retained_manifest),
        "snapshot_counts": {},
        "retained_current_datasets": len(retained_current),
        "retained_execution_packages": len(retained_package_rows),
        "retained_governance_files": len(files_under(governance_root)),
        "retained_files_total": len(retained_files),
        "logical_bytes_after_prune": sum(path.stat().st_size for path in retained_files),
        "files_unlinked": ORIGINAL_PRUNE_FILES,
        "logical_bytes_unlinked": ORIGINAL_PRUNE_LOGICAL_BYTES,
        "original_source_roots_modified_or_deleted": True,
        "downloads_final_state": "six retained paper datasets plus checksum sidecars restored as NTFS hardlinks; excluded datasets not restored",
    })
    build_report_path.write_text(json.dumps(build_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readme = """# DRTP paper-closure data archive

This curated archive contains only evidence and reproducibility materials used
to close the current DRTP paper. Temp and repository source/result trees were
not modified. Downloads contains the same six retained datasets and checksum
sidecars as NTFS hard links; excluded datasets were not restored there.

- `01_CURRENT_FORMAL_EVIDENCE`: final A/B, structural held-out, and PLR positioning.
- `02_SUPPORTING_MECHANISM_EVIDENCE`: non-paired and factorial exposure sensitivity.
- `20_REPRODUCIBILITY_PACKAGES`: seven directly relevant execution/repair packages.
- `40_EVIDENCE_GOVERNANCE`: current freezes, contracts, fairness audit, and claim boundaries.
- `00_INDEX`: hashes, retained-data register, provenance manifest, and pruning audit.

Excluded 6-UAV runs, development diagnostics, historical archives, mixed snapshots,
obsolete execution packages, and incomplete archive attempts were removed from this
archive. `00_INDEX/PRUNING_AUDIT.csv` records the final long-path cleanup pass;
aggregate pre-prune and post-prune counts are stored in the build report.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(build_report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
