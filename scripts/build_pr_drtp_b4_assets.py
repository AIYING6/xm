"""Build a compact hash-verified checkpoint asset archive from existing results."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json"
ASSET_ROOT = "pr_drtp_b4_assets"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mtime = 0
    info.mode = 0o644
    archive.addfile(info, io.BytesIO(payload))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloads-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
        raise FileExistsError(f"refusing asset overwrite: {output}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    checkpoint_by_seed = {int(row["seed"]): row for row in freeze["checkpoints"]}
    records: list[dict] = []
    payloads: dict[str, bytes] = {}
    for source in freeze["source_archives"]:
        source_path = args.downloads_dir / source["name"]
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if sha256_file(source_path) != source["sha256"]:
            raise RuntimeError(f"source archive hash mismatch: {source_path}")
        with tarfile.open(source_path, "r:gz") as source_archive:
            for seed in source["seeds"]:
                expected = checkpoint_by_seed[int(seed)]
                for arm, hash_key in (("utr_sg", "utr_sha256"), ("drtp_sg", "drtp_sha256")):
                    prefix = f'{source["root"]}/runs/{arm}/seed{seed}'
                    manifest_member = source_archive.extractfile(f"{prefix}/run_manifest.json")
                    checkpoint_member = source_archive.extractfile(f"{prefix}/actor_critic_latest.pt")
                    if manifest_member is None or checkpoint_member is None:
                        raise RuntimeError(f"missing frozen source artifact: {prefix}")
                    manifest_bytes = manifest_member.read()
                    checkpoint_bytes = checkpoint_member.read()
                    manifest = json.loads(manifest_bytes)
                    if (
                        manifest.get("status") != "completed"
                        or manifest.get("arm") != arm
                        or int(manifest.get("seed")) != int(seed)
                        or int(manifest.get("updates")) != freeze["checkpoint_budget_updates"]
                        or int(manifest.get("environment_steps"))
                        != freeze["checkpoint_budget_environment_steps"]
                    ):
                        raise RuntimeError(f"invalid source manifest: {prefix}")
                    actual_hash = sha256_bytes(checkpoint_bytes)
                    if actual_hash != expected[hash_key] or manifest.get("final_checkpoint_sha256") != actual_hash:
                        raise RuntimeError(f"checkpoint hash mismatch: {prefix}")
                    destination = f'{ASSET_ROOT}/{source["cohort"]}/{arm}/seed{seed}'
                    payloads[f"{destination}/run_manifest.json"] = manifest_bytes
                    payloads[f"{destination}/actor_critic_latest.pt"] = checkpoint_bytes
                    records.append({
                        "cohort": source["cohort"], "seed": seed, "arm": arm,
                        "checkpoint_sha256": actual_hash,
                        "source_archive": source["name"], "source_archive_sha256": source["sha256"],
                        "asset_path": f"{destination}/actor_critic_latest.pt",
                    })
    asset_manifest = {
        "protocol": "PR-DRTP-B4-ASSET-MANIFEST-V1",
        "freeze_sha256": sha256_file(FREEZE),
        "records": sorted(records, key=lambda row: (row["seed"], row["arm"])),
        "training_performed": False,
        "checkpoint_count": len(records),
    }
    payloads[f"{ASSET_ROOT}/ASSET_MANIFEST.json"] = (
        json.dumps(asset_manifest, indent=2) + "\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz", compresslevel=9) as target:
        for name, payload in sorted(payloads.items()):
            add_bytes(target, name, payload)
    checksum = output.with_suffix(output.suffix + ".sha256")
    digest = sha256_file(output)
    with checksum.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {output.name}\n")
    print(json.dumps({
        "asset_archive": str(output), "sha256_file": str(checksum),
        "sha256": digest, "checkpoint_count": len(records), "bytes": output.stat().st_size,
    }, indent=2))


if __name__ == "__main__":
    main()
