"""Create an anonymous-review staging package from the three frozen local archives.

No model is trained or evaluated. The package includes raw episode records,
manifests, selected source/configuration assets and checksums; authors still
must select a license and host the package anonymously before submission.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output" / "drtp_relay_failure_anonymous_reproducibility_v1"
ARCHIVES = {
    "formal_2301_2305": {
        "path": Path(r"D:\File\Downloads\drtp_utr_q2_paired_5seed_cloud_10way.tar.gz"),
        "sha": "cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd",
        "root": "results/formal/drtp_utr_q2_paired_5seed_cloud_10way",
        "arms": ("utr_sg", "drtp_sg"), "seeds": (2301, 2302, 2303, 2304, 2305),
        "report": "DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_REPORT.md", "tape": "formal_tape_manifest.json", "preflight": "formal_preflight.json",
    },
    "mappo_nograph_2301_2305": {
        "path": Path(r"D:\File\Downloads\drtp_mappo_nograph_external_5seed.tar.gz"),
        "sha": "2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5",
        "root": "results/formal/drtp_mappo_nograph_external_5seed",
        "arms": ("mappo_ng",), "seeds": (2301, 2302, 2303, 2304, 2305),
        "report": "DRTP_MAPPO_EXTERNAL_REFERENCE_REPORT.md", "tape": "formal_tape_manifest.json", "preflight": "external_preflight.json",
    },
    "independent_2401_2405": {
        "path": Path(r"D:\File\Downloads\drtp_snr_q2_mechanism_comparator_10way_results.tar.gz"),
        "sha": "86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1",
        "root": "results/formal/drtp_snr_q2_mechanism_comparator_10way",
        "arms": ("utr_sg", "snr_sg", "drtp_sg"), "seeds": (2401, 2402, 2403, 2404, 2405),
        "report": "DRTP_SNR_Q2_MECHANISM_COMPARATOR_REPORT.md", "tape": "snr_comparator_tape_manifest.json", "preflight": "snr_preflight.json",
    },
}
CONTRACTS = (
    "docs/DRTP_UTR_Q2_FORMAL_FIVE_SEED_CONFIRMATION_CONTRACT.md",
    "docs/DRTP_UTR_Q2_FORMAL_SEED_TAPE_PROVENANCE_AUDIT.md",
    "docs/DRTP_MAPPO_EXTERNAL_BASELINE_TRAINING_CONTRACT.md",
    "docs/DRTP_MAPPO_EXTERNAL_REFERENCE_AUDIT.md",
    "docs/DRTP_SNR_Q2_EXECUTION_CONTRACT.md",
    "docs/DRTP_SNR_Q2_IMPLEMENTATION_AUDIT.md",
)
PAPER_ASSETS = (
    "paper/q2_final_zh/main_zh.md", "paper/q2_final_zh/references_core.enw",
    "paper/q2_final_zh/22_submission_evidence_layer_freeze_audit.md",
    "paper/q2_final_zh/23_claim_evidence_audit.md", "paper/q2_final_zh/25_final_evidence_manifest.json",
    "paper/q2_final_zh/26_novelty_and_prior_art_positioning.md",
    "paper/q2_final_zh/supplementary/S1_full_formal_condition_and_safety.md",
    "paper/q2_final_zh/supplementary/S2_training_and_ppo_diagnostics.md",
    "paper/q2_final_zh/supplementary/S3_hyperparameters_projection_and_provenance.md",
    "paper/q2_final_zh/supplementary/S4_independent_three_arm_replication.md",
)
SCRIPTS = (
    "scripts/run_drtp_utr_q2_formal_single.py", "scripts/run_drtp_utr_q2_formal_evaluation.py",
    "scripts/aggregate_drtp_utr_q2_formal.py", "scripts/verify_drtp_utr_q2_formal_contract.py",
    "scripts/create_drtp_utr_q2_formal_tape.py", "scripts/run_drtp_mappo_external_single.py",
    "scripts/run_drtp_mappo_external_evaluation.py", "scripts/aggregate_drtp_mappo_external.py",
    "scripts/verify_drtp_mappo_external_contract.py", "scripts/run_drtp_snr_q2_formal_single.py",
    "scripts/run_drtp_snr_q2_evaluation.py", "scripts/aggregate_drtp_snr_q2.py",
    "scripts/verify_drtp_snr_q2_preflight.py", "scripts/create_drtp_snr_q2_tape.py",
    "scripts/build_paper_q2_evidence_chain.py", "scripts/check_q2_final_zh_manuscript.py",
    "scripts/build_drtp_anonymous_reproducibility_package.py",
    "scripts/check_drtp_anonymous_reproducibility_package.py",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def needed_members(spec: dict) -> set[str]:
    root = spec["root"]
    members = {
        f"{root}/evaluations/final_10m/raw_episode_metrics.csv",
        f"{root}/evaluations/final_10m/evaluation_manifest.json",
        f"{root}/{spec['report']}", f"{root}/{spec['tape']}", f"{root}/{spec['preflight']}",
    }
    for arm in spec["arms"]:
        for seed in spec["seeds"]:
            run = f"{root}/runs/{arm}/seed{seed}"
            members.add(f"{run}/run_manifest.json")
            sampler_prefix = "snr_static_nonuniform_topology_sampler" if arm == "snr_sg" else "drtp_topology_sampler"
            members.update({f"{run}/{sampler_prefix}_manifest.json", f"{run}/{sampler_prefix}_log.csv"})
    return members


def extract(archive: Path, output: Path, spec: dict) -> int:
    wanted = needed_members(spec)
    prefix = f"{spec['root']}/"
    with tarfile.open(archive, "r:gz") as bundle:
        available = {item.name for item in bundle.getmembers() if item.isfile()}
        missing = wanted - available
        if missing:
            raise RuntimeError(f"archive lacks required files: {sorted(missing)}")
        for member_name in sorted(wanted):
            item = bundle.getmember(member_name)
            relative_name = member_name[len(prefix):]
            target = output / Path(*PurePosixPath(relative_name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(item) as source, target.open("wb") as destination:
                if source is None:
                    raise RuntimeError(f"cannot extract {member_name}")
                shutil.copyfileobj(source, destination)
    return len(wanted)


def write(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def copy_sources(output: Path) -> None:
    for folder in ("envs", "algorithms"):
        for path in (ROOT / folder).rglob("*.py"):
            copy_file(path, output / "code" / folder / path.relative_to(ROOT / folder))
    for path in (ROOT / "configs").rglob("*"):
        if path.is_file() and path.suffix in {".json", ".yml", ".yaml"}:
            copy_file(path, output / "configs" / path.relative_to(ROOT / "configs"))
    for relative in ("requirements.txt", "environment.yml") + SCRIPTS + CONTRACTS + PAPER_ASSETS:
        copy_file(ROOT / relative, output / relative)
    for path in (ROOT / "paper" / "q2_final_zh" / "formal_results" / "figures").glob("*"):
        if path.suffix.lower() in {".png", ".svg", ".pdf"}:
            copy_file(path, output / "figures" / path.name)


def write_documents(output: Path, revision: str) -> None:
    write(output / "README.md", [
        "# DRTP relay-failure reproducibility package (anonymous-review staging)", "",
        "This package supports the DRTP relay-failure manuscript. It contains three non-pooled evidence strata:",
        "1. primary matched UTR--DRTP cohort (2301--2305; 12,000 raw records);",
        "2. Non-Graph MAPPO performance reference (2301--2305; 6,000 raw records);",
        "3. independent UTR/SNR/DRTP cohort (2401--2405; 18,000 raw records, with an adverse DRTP direction).", "",
        "The independent cohort must not be pooled with the primary cohort as n=10. The manuscript claims only a bounded empirical DRTP gain over uniform weighting in the frozen primary cohort. It does not claim strict OOD generalization, general DRO guarantees, information recovery, seed-stable superiority, or adaptive necessity against all static nonuniform distributions.", "",
        "## Verification", "Run `python scripts/check_drtp_anonymous_reproducibility_package.py --package-root .` after download. Raw records, manifests, run provenance and sampler logs are under `source_data/`. Checkpoint SHA256 values are in per-run manifests; binaries are not duplicated here.", "",
        f"Built from source revision `{revision}`. Before external hosting, complete every item in `RELEASE_BLOCKERS.md`.",
    ])
    write(output / "CITATION.cff", [
        "cff-version: 1.2.0", "message: \"Anonymous-review metadata only; authors and DOI will be completed upon publication.\"",
        "title: \"DRTP relay-failure reproducibility package\"", "type: software", "version: \"1.0-anonymous-review\"",
        "authors:", "  - family-names: \"ANONYMOUS\"", "    given-names: \"AUTHOR\"", "date-released: 2026-08-27",
    ])
    write(output / "LICENSE-REQUIRED-BEFORE-PUBLIC-RELEASE.md", [
        "# License decision required", "", "No license is selected automatically. The authors must choose the applicable code/data license before public release.",
    ])
    write(output / "RELEASE_BLOCKERS.md", [
        "# Author-owned publication blockers", "", "- [ ] Host an anonymous reviewer-access repository or data-record link.",
        "- [ ] Test download and checksum verification from an external session.", "- [ ] Choose and add a code/data license.",
        "- [ ] Decide whether checkpoint/runtime-state binaries are public; if restricted, give a real access route.",
        "- [ ] Replace anonymous metadata with authors, affiliations, funding, conflict statement, CRediT roles, DOI and release date.",
        "- [ ] Move the manuscript into the selected target-journal template.",
    ])
    write(output / "checkpoints" / "README.md", [
        "# Checkpoint and runtime-state policy", "", "Final checkpoint/runtime-state SHA256 values are retained in each extracted `run_manifest.json`. Large checkpoint binaries are intentionally not duplicated into this staging package. Before release, authors must either deposit them or state a concrete access route; the manuscript must not claim public checkpoint availability before that decision.",
    ])
    write(output / "source_data" / "DATA_DICTIONARY.md", [
        "# Source-data dictionary", "", "Each stratum includes final raw episode metrics, evaluation/tape manifests, a frozen report, preflight record, per-run manifests and sampler logs.",
        "Training seed is the independent statistical unit. No pre-trigger termination is removed from overall task or safety outcomes. Legacy archive fields named J_OOD_mean/J_OOD_worst map to manuscript J_pert,mean/J_pert,worst and are not strict unseen-condition OOD metrics.",
    ])


def manifest(output: Path, archives: list[dict], revision: str) -> None:
    rows = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "FILE_MANIFEST_SHA256.csv":
            rows.append((path.relative_to(output).as_posix(), path.stat().st_size, digest(path)))
    target = output / "manifests" / "FILE_MANIFEST_SHA256.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(("relative_path", "bytes", "sha256")); writer.writerows(rows)
    provenance = {"package_status": "PREPARED_FOR_AUTHOR_HOSTING", "built_utc": datetime.now(timezone.utc).isoformat(), "source_revision": revision, "archives": archives, "checkpoint_binaries_included": False, "manual_release_blockers": ["anonymous_repository_link", "license", "checkpoint_access_policy", "author_metadata", "target_journal_template"]}
    write(output / "manifests" / "PACKAGE_PROVENANCE.json", json.dumps(provenance, indent=2).splitlines())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(); output = args.output.resolve()
    if output.exists():
        if not args.overwrite: raise FileExistsError(f"refusing to overwrite: {output}")
        shutil.rmtree(output)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    records = []
    for name, spec in ARCHIVES.items():
        archive = spec["path"]
        if not archive.is_file(): raise FileNotFoundError(archive)
        observed = digest(archive)
        if observed != spec["sha"]: raise RuntimeError(f"SHA256 mismatch for {name}: {observed}")
        records.append({"stratum": name, "archive": archive.name, "sha256": observed, "selected_files": extract(archive, output / "source_data" / name, spec)})
    copy_sources(output); write_documents(output, revision); manifest(output, records, revision)
    print(json.dumps({"status": "PREPARED_FOR_AUTHOR_HOSTING", "output": str(output), "source_revision": revision, "archives": records}, indent=2))


if __name__ == "__main__": main()
