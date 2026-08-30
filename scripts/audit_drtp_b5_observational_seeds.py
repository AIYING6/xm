"""Audit candidate B5 training seeds against tracked sources and prior archives."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (3601, 3602, 3603, 3604, 3605)
CONFIG = ROOT / "configs" / "drtp_b5_cross_cohort_atlas_freeze.json"
OUTPUT = ROOT / "docs" / "drtp_b5_p1_20260830" / "B5_SEED_PROVENANCE_AUDIT.json"
ALLOWED_PREFIXES = (
    "configs/drtp_b5_", "docs/drtp_b5_", "scripts/audit_drtp_b5_",
    "scripts/freeze_drtp_b5_", "scripts/run_drtp_b5_", "scripts/aggregate_drtp_b5_",
    "scripts/launch_drtp_b5_", "scripts/build_drtp_b5_", "scripts/verify_drtp_b5_",
    "tests/test_drtp_b5_",
)
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".toml"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_seed(text: str) -> list[int]:
    return [seed for seed in SEEDS if re.search(rf"(?<!\d){seed}(?!\d)", text)]


def has_seed_context(text: str) -> list[int]:
    """Match provenance declarations, not coincidental metric values or hashes."""
    return [
        seed for seed in SEEDS
        if re.search(rf"(?i)seed(?:s|_namespace)?[^0-9]{{0,24}}{seed}(?!\d)", text)
    ]


def tracked_source_hits() -> list[dict]:
    paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    hits = []
    for relative in paths:
        normalized = relative.replace("\\", "/")
        if normalized.startswith(("results/", "artifacts/", "output/", *ALLOWED_PREFIXES)):
            continue
        path = ROOT / relative
        if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES | {".py", ".sh"}:
            continue
        seeds = has_seed(normalized)
        if not seeds:
            seeds = has_seed_context(path.read_text(encoding="utf-8", errors="ignore"))
        if seeds:
            hits.append({"path": normalized, "seeds": seeds})
    return hits


def archive_hits(archive: Path) -> list[dict]:
    hits = []
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle:
            seeds = has_seed(member.name)
            if seeds:
                hits.append({"member": member.name, "seeds": seeds, "source": "member_name"})
                continue
            suffix = Path(member.name).suffix.lower()
            provenance_name = any(
                token in member.name.lower()
                for token in ("manifest", "decision", "report", "freeze", "audit", "contract", "config")
            )
            if (not member.isfile() or suffix not in TEXT_SUFFIXES or
                    not provenance_name or member.size > 4 * 1024 * 1024):
                continue
            extracted = bundle.extractfile(member)
            if extracted is None:
                continue
            seeds = has_seed_context(extracted.read().decode("utf-8", errors="ignore"))
            if seeds:
                hits.append({"member": member.name, "seeds": seeds, "source": "text_content"})
    return hits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source_hits = tracked_source_hits()
    archives = []
    all_hits = list(source_hits)
    for experiment in config["experiments"]:
        path = args.archive_root / experiment["archive"]
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256(path)
        if actual != experiment["sha256"]:
            raise RuntimeError(f"SHA256 mismatch: {path.name}")
        hits = archive_hits(path)
        archives.append({"archive": path.name, "sha256": actual, "hits": hits})
        all_hits.extend(hits)
    clean = not all_hits
    payload = {
        "protocol": "DRTP-B5-SEED-PROVENANCE-AUDIT-V1",
        "candidate_seeds": list(SEEDS),
        "status": "CLEAN" if clean else "CONTAMINATED",
        "tracked_source_hits_excluding_b5_preparation": source_hits,
        "archives": archives,
        "archive_count": len(archives),
        "scientific_results_seen_for_candidates": not clean,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output": str(OUTPUT), "archives": len(archives)}, indent=2))
    if not clean:
        raise SystemExit("candidate seed provenance is contaminated")


if __name__ == "__main__":
    main()
