"""Build a slim B1 checkpoint asset bundle from four immutable archives."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import csv


SOURCES = {
    "formal_positive_2300": {
        "archive": "drtp_utr_q2_paired_5seed_cloud_10way.tar.gz",
        "sha256": "cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd",
        "root": "results/formal/drtp_utr_q2_paired_5seed_cloud_10way",
        "seeds": range(2301, 2306),
    },
    "independent_reversal_2400": {
        "archive": "drtp_snr_q2_mechanism_comparator_10way_results.tar.gz",
        "sha256": "86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1",
        "root": "results/formal/drtp_snr_q2_mechanism_comparator_10way",
        "seeds": range(2401, 2406),
    },
    "r1_mixed_3000": {
        "archive": "drtp_stable_r1_1m_results.tar.gz",
        "sha256": "a54406e8d2d14c4bc9fa25ea43388595c19f41d476631e1c743512c6c30c0b10",
        "root": "drtp_stable_r1",
        "seeds": range(3001, 3006),
    },
    "b5_mixed_3600": {
        "archive": "drtp_b5_observational.tar.gz",
        "sha256": "d8e580142dfb4042b24e85861e7c3d023d35cb3e446b2cd11cd3ed2fd9df2a36",
        "root": "drtp_b5_observational",
        "seeds": range(3601, 3606),
    },
}
ARMS = ("utr_sg", "drtp_sg")
FILES = (
    "run_manifest.json",
    "actor_critic_runtime_state_milestone_500k.pt",
    "train_log.csv",
    "drtp_topology_sampler_log.csv",
)
SOURCE_SEGMENT_MIN_UPDATE = 1954
SOURCE_SEGMENT_MAX_UPDATE = 2017


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract_member(archive: tarfile.TarFile, member: tarfile.TarInfo, destination: Path) -> None:
    relative = PurePosixPath(member.name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe archive member: {member.name}")
    source = archive.extractfile(member)
    if source is None:
        raise ValueError(f"member is not a regular file: {member.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source, destination.open("wb") as handle:
        shutil.copyfileobj(source, handle)


def retain_source_segment(path: Path) -> None:
    """Retain only the exact-replay comparison window from a large source log."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row for row in reader
            if row.get("update") and SOURCE_SEGMENT_MIN_UPDATE <= int(row["update"]) <= SOURCE_SEGMENT_MAX_UPDATE
        ]
        fieldnames = reader.fieldnames
    if fieldnames is None:
        raise ValueError(f"source log has no header: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archives-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing B1 asset directory: {output}")
    output.mkdir(parents=True, exist_ok=False)
    inventory = []
    for cohort, spec in SOURCES.items():
        archive_path = (args.archives_dir / spec["archive"]).resolve()
        actual = sha256(archive_path)
        if actual != spec["sha256"]:
            raise RuntimeError(f"archive hash mismatch: {archive_path}")
        wanted = {}
        for arm in ARMS:
            for seed in spec["seeds"]:
                run_prefix = f"{spec['root']}/runs/{arm}/seed{seed}"
                for filename in FILES:
                    wanted[f"{run_prefix}/{filename}"] = (arm, seed, filename)
        found = set()
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive:
                binding = wanted.get(member.name)
                if binding is None:
                    continue
                arm, seed, filename = binding
                destination = output / cohort / arm / f"seed{seed}" / filename
                safe_extract_member(archive, member, destination)
                if filename in {"train_log.csv", "drtp_topology_sampler_log.csv"}:
                    retain_source_segment(destination)
                inventory.append({
                    "cohort": cohort,
                    "arm": arm,
                    "seed": seed,
                    "filename": filename,
                    "bytes": destination.stat().st_size,
                    "sha256": sha256(destination),
                    "source_archive_sha256": actual,
                    "source_segment_updates": (
                        [SOURCE_SEGMENT_MIN_UPDATE, SOURCE_SEGMENT_MAX_UPDATE]
                        if filename in {"train_log.csv", "drtp_topology_sampler_log.csv"}
                        else None
                    ),
                })
                found.add(member.name)
        missing = sorted(set(wanted) - found)
        if missing:
            raise FileNotFoundError(f"missing B1 assets in {archive_path}: {missing}")
    manifest = {
        "schema": "drtp-b1-slim-assets-v1",
        "status": "complete",
        "source_checkpoint": "500k",
        "cohorts": list(SOURCES),
        "arms": list(ARMS),
        "source_training_seeds": 20,
        "runtime_checkpoints": 40,
        "files": inventory,
    }
    (output / "B1_ASSET_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "complete", "files": len(inventory), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
