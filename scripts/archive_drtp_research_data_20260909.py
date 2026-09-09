"""Build a non-destructive, evidence-tiered archive of the DRTP project data.

The archive is created on the same NTFS volume as the source data and uses
hard links whenever possible.  Original files are never moved, renamed, or
deleted.  Large repository result trees are preserved as a mixed-evidence
snapshot, but only explicitly registered datasets are placed in the formal
evidence tier.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
from typing import Iterable
import zipfile


ARCHIVE_ROOT = Path(r"D:\File\DRTP_RESEARCH_DATA_ARCHIVE_20260909_FINAL_V3")
DOWNLOADS = Path(r"D:\File\Downloads")
TEMP = Path(r"D:\File\MyFile\Temp")
REPO = Path(r"D:\Code\Codex\ri_gmappo_uav")

CURRENT_DATASETS = {
    "drtp_stabilization_A_complete_results.tar.gz": (
        "01_CURRENT_FORMAL_EVIDENCE/01_cohort_A",
        "formal_primary_confirmatory_cohort_A",
    ),
    "drtp_stabilization_B_complete_results.tar.gz": (
        "01_CURRENT_FORMAL_EVIDENCE/02_cohort_B",
        "formal_independent_confirmatory_cohort_B",
    ),
    "drtp_final_evidence_heldout_ood_results.tar.gz": (
        "01_CURRENT_FORMAL_EVIDENCE/03_structural_heldout",
        "formal_training_excluded_structural_evaluation",
    ),
    "drtp_plr_matched_ab_results.tar.gz": (
        "01_CURRENT_FORMAL_EVIDENCE/04_plr_external_positioning",
        "formal_external_positioning_not_primary_causal_control",
    ),
    "drtp_semantic_ablation_nonpaired_10m_results.tar.gz": (
        "02_SUPPORTING_MECHANISM_EVIDENCE/01_nonpaired_ablation",
        "supporting_exposure_manipulation_sensitivity",
    ),
    "drtp_semantic_ablation_factorial_completion_10m_results.tar.gz": (
        "02_SUPPORTING_MECHANISM_EVIDENCE/02_factorial_completion",
        "supporting_factorial_ablation_not_component_necessity_proof",
    ),
    "drtp_6uav_cross_scale_fresh_restart_v1_results.tar.gz": (
        "03_EXCLUDED_OR_NONINFORMATIVE/01_6uav_v1_fault_timing_invalid",
        "excluded_no_effective_non_nominal_fault_injection",
    ),
    "drtp_6uav_v2_faultstep3_results.tar.gz": (
        "03_EXCLUDED_OR_NONINFORMATIVE/02_6uav_v2_ceiling",
        "excluded_nondiscriminating_utr_ceiling",
    ),
    "drtp_6uav_v31_utr_pilot_1m_results.tar.gz": (
        "03_EXCLUDED_OR_NONINFORMATIVE/03_6uav_v31_learnability_fail",
        "development_pilot_failed_nominal_learnability",
    ),
    "active_diagnosis_p3b_staged_pilot_v3_results.tar.gz": (
        "04_DEVELOPMENT_DIAGNOSTICS/01_active_diagnosis_p3b_calibration_stop",
        "valid_negative_development_diagnostic_calibration_stop_no_performance_comparison",
    ),
}

REPORT_TOKENS = (
    "complete", "final_report", "cohort_summary", "paired", "endpoint",
    "verdict", "decision", "evaluation_manifest", "run_manifest",
    "sampler_manifest", "tape_manifest",
)
PROJECT_TOKENS = (
    "drtp", "egtr", "tatg", "uav", "phase_d", "phase_s", "mappo",
    "topology", "reliable", "redundant", "active_diagnosis", "p3b",
)


def progress(message: str) -> None:
    print(f"[archive] {message}", flush=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sidecar_for(path: Path) -> Path | None:
    direct = path.with_name(path.name + ".sha256")
    return direct if direct.is_file() else None


def expected_digest(sidecar: Path) -> str | None:
    text = sidecar.read_text(encoding="utf-8-sig", errors="replace").strip()
    if not text:
        return None
    token = text.split()[0].lower()
    return token if len(token) == 64 and all(c in "0123456789abcdef" for c in token) else None


def archive_readable(path: Path) -> tuple[bool, int, str]:
    try:
        lower = path.name.lower()
        if lower.endswith(".tar.gz") or lower.endswith(".tgz"):
            with tarfile.open(path, "r:gz") as archive:
                members = archive.getmembers()
            return True, sum(member.isfile() for member in members), "tar_gzip"
        if lower.endswith(".zip"):
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
            return True, sum(not member.is_dir() for member in members), "zip"
        return True, 1, "ordinary_file"
    except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError) as error:
        return False, 0, f"{type(error).__name__}: {error}"


def hardlink_or_copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        shutil.copy2(source, destination)
        return "copy"


def bounded_target(base: Path, relative: Path) -> Path:
    """Preserve ordinary paths and safely flatten only paths too long for Windows."""
    target = base / relative
    if len(str(target)) <= 235:
        return target
    token = hashlib.sha256(str(relative).encode("utf-8")).hexdigest()[:16]
    return base / "_LONG_PATHS" / f"{token}__{relative.name}"


def link_tree(source: Path, destination: Path, classification: str, manifest: list[dict]) -> int:
    count = 0
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        target = bounded_target(destination, path.relative_to(source))
        mode = hardlink_or_copy(path, target)
        manifest.append({
            "classification": classification,
            "source_path": str(path),
            "archive_path": str(target.relative_to(ARCHIVE_ROOT)),
            "bytes": path.stat().st_size,
            "sha256": "",
            "checksum_status": "snapshot_not_individually_hashed",
            "container_readable": "not_applicable",
            "container_members": "",
            "storage_mode": mode,
        })
        count += 1
    return count


def extract_reports(archive_path: Path, dataset_name: str) -> int:
    destination = ARCHIVE_ROOT / "00_INDEX" / "EXTRACTED_REPORTS" / dataset_name
    extracted = 0
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or member.size > 20 * 1024 * 1024:
                continue
            basename = Path(member.name).name.lower()
            suffix = Path(member.name).suffix.lower()
            if suffix not in {".json", ".csv", ".md", ".txt"}:
                continue
            if not any(token in basename for token in REPORT_TOKENS):
                continue
            # Keep the inspection copy shallow enough for legacy Windows path limits.
            # The digest suffix preserves uniqueness when archives contain repeated basenames.
            member_path_digest = hashlib.sha256(member.name.encode("utf-8")).hexdigest()[:12]
            member_basename = Path(member.name).name
            target = destination / f"{member_path_digest}__{member_basename}"
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as stream:
                shutil.copyfileobj(source, stream)
            extracted += 1
    return extracted


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def result_archives() -> list[Path]:
    paths: set[Path] = set()
    for root in (DOWNLOADS, TEMP, REPO):
        for path in root.rglob("*"):
            if not path.is_file() or path.stat().st_size == 0:
                continue
            lower = path.name.lower()
            if lower.endswith((".tar.gz", ".tgz")) and any(token in lower for token in PROJECT_TOKENS):
                paths.add(path)
    return sorted(paths, key=lambda path: str(path).lower())


def protocol_packages() -> list[Path]:
    paths: set[Path] = set()
    for root in (DOWNLOADS, TEMP, REPO):
        for path in root.rglob("*.zip"):
            if path.is_file() and path.stat().st_size > 0 and any(
                token in path.name.lower() for token in PROJECT_TOKENS
            ):
                paths.add(path)
    return sorted(paths, key=lambda path: str(path).lower())


def source_label(path: Path) -> tuple[str, Path]:
    for label, root in (("downloads", DOWNLOADS), ("temp", TEMP), ("repo", REPO)):
        try:
            return label, path.relative_to(root)
        except ValueError:
            continue
    raise ValueError(path)


def add_critical_archive(
    source: Path,
    relative_directory: str,
    classification: str,
    manifest: list[dict],
    current_register: list[dict],
) -> None:
    readable, member_count, container_type = archive_readable(source)
    digest = sha256(source)
    sidecar = sidecar_for(source)
    expected = expected_digest(sidecar) if sidecar else None
    checksum_status = (
        "verified_sidecar_match" if expected == digest
        else "sidecar_mismatch" if expected is not None
        else "generated_no_sidecar"
    )
    if not readable or checksum_status == "sidecar_mismatch":
        raise RuntimeError(f"critical dataset failed validation: {source}: {checksum_status}, {container_type}")
    destination = ARCHIVE_ROOT / relative_directory / source.name
    mode = hardlink_or_copy(source, destination)
    manifest.append({
        "classification": classification,
        "source_path": str(source),
        "archive_path": str(destination.relative_to(ARCHIVE_ROOT)),
        "bytes": source.stat().st_size,
        "sha256": digest,
        "checksum_status": checksum_status,
        "container_readable": readable,
        "container_members": member_count,
        "storage_mode": mode,
    })
    if sidecar:
        sidecar_target = destination.with_name(destination.name + ".sha256")
        sidecar_mode = hardlink_or_copy(sidecar, sidecar_target)
        manifest.append({
            "classification": classification + "_checksum",
            "source_path": str(sidecar),
            "archive_path": str(sidecar_target.relative_to(ARCHIVE_ROOT)),
            "bytes": sidecar.stat().st_size,
            "sha256": sha256(sidecar),
            "checksum_status": "sidecar_file",
            "container_readable": "not_applicable",
            "container_members": "",
            "storage_mode": sidecar_mode,
        })
    dataset_name = source.name[:-7] if source.name.lower().endswith(".tar.gz") else source.stem
    reports = extract_reports(source, dataset_name)
    current_register.append({
        "dataset": source.name,
        "classification": classification,
        "source": str(source),
        "archive_location": relative_directory,
        "bytes": source.stat().st_size,
        "sha256": digest,
        "checksum_status": checksum_status,
        "archive_members": member_count,
        "extracted_report_files": reports,
    })


def main() -> None:
    if ARCHIVE_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite existing archive: {ARCHIVE_ROOT}")
    for root in (DOWNLOADS, TEMP, REPO):
        if not root.is_dir():
            raise FileNotFoundError(root)
    (ARCHIVE_ROOT / "00_INDEX").mkdir(parents=True)
    progress(f"destination created: {ARCHIVE_ROOT}")

    manifest: list[dict] = []
    current_register: list[dict] = []
    current_sources: set[Path] = set()
    for filename, (relative_directory, classification) in CURRENT_DATASETS.items():
        source = DOWNLOADS / filename
        if not source.is_file() or source.stat().st_size == 0:
            raise FileNotFoundError(f"required registered dataset is absent or empty: {source}")
        add_critical_archive(source, relative_directory, classification, manifest, current_register)
        current_sources.add(source.resolve())
        progress(f"validated current dataset {len(current_register)}/{len(CURRENT_DATASETS)}: {filename}")

    historical_rows = []
    historical_candidates = result_archives()
    progress(f"discovered {len(historical_candidates)} non-empty result archives")
    for index, source in enumerate(historical_candidates, start=1):
        if source.resolve() in current_sources:
            continue
        readable, member_count, container_type = archive_readable(source)
        digest = sha256(source)
        sidecar = sidecar_for(source)
        expected = expected_digest(sidecar) if sidecar else None
        checksum_status = (
            "verified_sidecar_match" if expected == digest
            else "sidecar_mismatch" if expected is not None
            else "generated_no_sidecar"
        )
        label, relative = source_label(source)
        included = readable and checksum_status != "sidecar_mismatch"
        history_base = ARCHIVE_ROOT / "10_HISTORICAL_RESULT_ARCHIVES" / label
        destination = bounded_target(history_base, relative)
        storage_mode = "not_included"
        if included:
            storage_mode = hardlink_or_copy(source, destination)
            if sidecar:
                hardlink_or_copy(sidecar, destination.with_name(destination.name + ".sha256"))
            manifest.append({
                "classification": "historical_result_not_current_formal_evidence",
                "source_path": str(source),
                "archive_path": str(destination.relative_to(ARCHIVE_ROOT)),
                "bytes": source.stat().st_size,
                "sha256": digest,
                "checksum_status": checksum_status,
                "container_readable": readable,
                "container_members": member_count,
                "storage_mode": storage_mode,
            })
        historical_rows.append({
            "source_path": str(source),
            "bytes": source.stat().st_size,
            "sha256": digest,
            "readable": readable,
            "container_type_or_error": container_type,
            "members": member_count,
            "checksum_status": checksum_status,
            "included": included,
            "evidence_status": "historical_not_current_formal_evidence" if included else "quarantined_invalid_container_or_checksum",
        })
        if index % 25 == 0 or index == len(historical_candidates):
            progress(f"audited result archives {index}/{len(historical_candidates)}")

    package_rows = []
    seen_package_hashes: dict[str, str] = {}
    package_candidates = protocol_packages()
    progress(f"discovered {len(package_candidates)} non-empty protocol packages")
    for index, source in enumerate(package_candidates, start=1):
        readable, member_count, container_type = archive_readable(source)
        digest = sha256(source)
        duplicate_of = seen_package_hashes.get(digest, "")
        label, relative = source_label(source)
        package_base = ARCHIVE_ROOT / "20_REPRODUCIBILITY_PACKAGES" / label
        destination = bounded_target(package_base, relative)
        storage_mode = "manifest_only_duplicate" if duplicate_of else "not_included_invalid"
        if readable and not duplicate_of:
            storage_mode = hardlink_or_copy(source, destination)
            seen_package_hashes[digest] = str(destination.relative_to(ARCHIVE_ROOT))
            manifest.append({
                "classification": "reproducibility_or_execution_package_not_result_data",
                "source_path": str(source),
                "archive_path": str(destination.relative_to(ARCHIVE_ROOT)),
                "bytes": source.stat().st_size,
                "sha256": digest,
                "checksum_status": "archive_generated_sha256",
                "container_readable": readable,
                "container_members": member_count,
                "storage_mode": storage_mode,
            })
        package_rows.append({
            "source_path": str(source),
            "bytes": source.stat().st_size,
            "sha256": digest,
            "readable": readable,
            "container_type_or_error": container_type,
            "members": member_count,
            "duplicate_of": duplicate_of,
            "storage_mode": storage_mode,
        })
        if index % 50 == 0 or index == len(package_candidates):
            progress(f"audited protocol packages {index}/{len(package_candidates)}")

    zero_length_rows = []
    for root_name, root in (("downloads", DOWNLOADS), ("temp", TEMP), ("repo", REPO)):
        for source in root.rglob("*"):
            if not source.is_file() or source.stat().st_size != 0:
                continue
            lower = source.name.lower()
            if not any(token in lower for token in PROJECT_TOKENS):
                continue
            if not lower.endswith((".tar.gz", ".tgz", ".zip", ".csv", ".json", ".pt", ".pth")):
                continue
            zero_length_rows.append({
                "source_root": root_name,
                "source_path": str(source),
                "bytes": 0,
                "status": "excluded_zero_length_not_valid_data",
            })
    progress(f"recorded {len(zero_length_rows)} zero-length candidates")

    snapshot_counts = {}
    for source, relative, classification in (
        (REPO / "results", "30_MIXED_EVIDENCE_SNAPSHOTS/repository/results", "repository_results_mixed_evidence_snapshot"),
        (REPO / "artifacts", "30_MIXED_EVIDENCE_SNAPSHOTS/repository/artifacts", "repository_artifacts_mixed_evidence_snapshot"),
        (REPO / "diagnostics", "30_MIXED_EVIDENCE_SNAPSHOTS/repository/diagnostics", "repository_diagnostics_mixed_evidence_snapshot"),
    ):
        if source.is_dir():
            snapshot_counts[str(source)] = link_tree(source, ARCHIVE_ROOT / relative, classification, manifest)
            progress(f"snapshotted {source}: {snapshot_counts[str(source)]} files")

    temp_snapshot_names = (
        "drtp_mechanism_v1_1m_audit",
        "tcr_phase_d_forensic_20260819113654",
        "tcr_spc_phase_c_results_audit_20260818",
        "pp_drtp_p3_pilot_inspection_20260830",
        "phase_d_continuation_audit_20260818",
        "phase_d_continuation_audit_20260818_v2",
        "phase_d_continuation_audit_20260818_v3",
        "drtp_additional_unseen_evaluation_inspect_20260828",
    )
    for name in temp_snapshot_names:
        source = TEMP / name
        if source.is_dir():
            relative = f"30_MIXED_EVIDENCE_SNAPSHOTS/temp_extracted/{name}"
            snapshot_counts[str(source)] = link_tree(
                source, ARCHIVE_ROOT / relative, "historical_extracted_mixed_evidence_snapshot", manifest
            )
            progress(f"snapshotted {source}: {snapshot_counts[str(source)]} files")

    backup_result_roots = []
    for path in (TEMP / "backup").rglob("*"):
        if path.is_dir() and path.name.lower() in {"results", "artifacts", "diagnostics"}:
            if any(parent in backup_result_roots for parent in path.parents):
                continue
            backup_result_roots.append(path)
    for index, source in enumerate(sorted(backup_result_roots, key=str), start=1):
        relative = f"30_MIXED_EVIDENCE_SNAPSHOTS/temp_backup/{index:02d}_{source.parent.name}_{source.name}"
        snapshot_counts[str(source)] = link_tree(
            source, ARCHIVE_ROOT / relative, "historical_backup_mixed_evidence_snapshot", manifest
        )
        progress(f"snapshotted {source}: {snapshot_counts[str(source)]} files")

    governance_sources: list[Path] = []
    governance_sources.extend(path for path in (REPO / "configs").glob("*.json") if any(
        token in path.name.lower() for token in PROJECT_TOKENS + ("active_diagnosis",)
    ))
    for relative in (
        "docs/drtp_submission_ready",
        "docs/drtp_stabilization_final_freeze_20260905",
        "docs/drtp_final_evidence_preparation_20260906_complete",
        "docs/q1_zero_training_topic_audit_20260909",
    ):
        directory = REPO / relative
        if directory.is_dir():
            governance_sources.extend(path for path in directory.rglob("*") if path.is_file())
    for source in sorted(set(governance_sources), key=str):
        destination = bounded_target(
            ARCHIVE_ROOT / "40_EVIDENCE_GOVERNANCE", source.relative_to(REPO)
        )
        mode = hardlink_or_copy(source, destination)
        manifest.append({
            "classification": "evidence_governance_or_claim_boundary",
            "source_path": str(source),
            "archive_path": str(destination.relative_to(ARCHIVE_ROOT)),
            "bytes": source.stat().st_size,
            "sha256": "",
            "checksum_status": "governance_snapshot_not_individually_hashed",
            "container_readable": "not_applicable",
            "container_members": "",
            "storage_mode": mode,
        })

    write_csv(ARCHIVE_ROOT / "00_INDEX" / "CURRENT_EVIDENCE_REGISTER.csv", current_register)
    write_csv(ARCHIVE_ROOT / "00_INDEX" / "HISTORICAL_ARCHIVE_AUDIT.csv", historical_rows)
    write_csv(ARCHIVE_ROOT / "00_INDEX" / "REPRODUCIBILITY_PACKAGE_AUDIT.csv", package_rows)
    write_csv(ARCHIVE_ROOT / "00_INDEX" / "ZERO_LENGTH_CANDIDATES.csv", zero_length_rows)
    write_csv(ARCHIVE_ROOT / "00_INDEX" / "MASTER_FILE_MANIFEST.csv", manifest)

    critical_sums = "\n".join(
        f"{row['sha256']}  {row['archive_location']}/{row['dataset']}"
        for row in current_register
    ) + "\n"
    (ARCHIVE_ROOT / "00_INDEX" / "SHA256SUMS_CURRENT_EVIDENCE.txt").write_text(
        critical_sums, encoding="ascii"
    )
    report = {
        "protocol": "DRTP-RESEARCH-DATA-ARCHIVE-20260909-V1",
        "archive_root": str(ARCHIVE_ROOT),
        "source_roots": [str(DOWNLOADS), str(TEMP), str(REPO)],
        "original_files_modified_or_deleted": False,
        "current_registered_datasets": len(current_register),
        "historical_result_archives_scanned": len(historical_rows),
        "historical_result_archives_included": sum(bool(row["included"]) for row in historical_rows),
        "protocol_packages_scanned": len(package_rows),
        "unique_protocol_packages_included": sum(row["storage_mode"] in {"hardlink", "copy"} for row in package_rows),
        "zero_length_candidates_excluded": len(zero_length_rows),
        "manifested_files": len(manifest),
        "snapshot_counts": snapshot_counts,
        "storage_note": "Large files are NTFS hard links where possible; SHA256 protects current critical archives.",
    }
    (ARCHIVE_ROOT / "00_INDEX" / "ARCHIVE_BUILD_REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    readme = f"""# DRTP research data archive (2026-09-09)

This archive was built non-destructively from three source roots. No source file
was moved, renamed, overwritten, or deleted. Large files use NTFS hard links
when possible; therefore the archive consumes little additional disk space.

## Evidence tiers

- `01_CURRENT_FORMAL_EVIDENCE`: the only datasets currently registered for the
  principal DRTP paper evidence chain (A, B, structural held-out, PLR positioning).
- `02_SUPPORTING_MECHANISM_EVIDENCE`: completed ablation runs retained as
  sensitivity/mechanism evidence; they do not independently prove component necessity.
- `03_EXCLUDED_OR_NONINFORMATIVE`: technically preserved runs that cannot support
  the paper claim because of fault timing, ceiling, or learnability failures.
- `04_DEVELOPMENT_DIAGNOSTICS`: valid development diagnostics and stop decisions;
  these are not performance evidence and are never pooled with formal cohorts.
- `10_HISTORICAL_RESULT_ARCHIVES`: readable historical result packages. They are
  preserved but must not be mixed with the current formal cohorts.
- `20_REPRODUCIBILITY_PACKAGES`: deduplicated execution packages, not result data.
- `30_MIXED_EVIDENCE_SNAPSHOTS`: safety-net snapshots of scattered repository and
  extracted results. Presence here is not evidence qualification.
- `40_EVIDENCE_GOVERNANCE`: contracts, freezes, audits, and claim-boundary documents.

Use `00_INDEX/CURRENT_EVIDENCE_REGISTER.csv` for paper-facing datasets and
`00_INDEX/MASTER_FILE_MANIFEST.csv` for provenance. Any future promotion from a
historical or mixed tier requires a separate protocol/seed/checkpoint audit.

Manifested files: {len(manifest)}
Current registered datasets: {len(current_register)}
Historical result archives scanned: {len(historical_rows)}
"""
    (ARCHIVE_ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
