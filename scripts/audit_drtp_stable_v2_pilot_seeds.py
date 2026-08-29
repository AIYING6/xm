"""Audit candidate Stable-v2 pilot seed identifiers without running an environment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (3101, 3102, 3103)
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".py", ".sh", ".ps1"}
EXCLUDED_TOP_LEVEL = {".git", "tmp", "output"}
PLANNED_CONTRACT_FILES = {
    "scripts/audit_drtp_stable_v2_pilot_seeds.py",
    "scripts/freeze_drtp_stable_v2_pilot_tape.py",
    "configs/drtp_stable_v2_pilot_tape.json",
}


def semantic_patterns(seed: int) -> tuple[re.Pattern[str], ...]:
    return (
        re.compile(rf"(?i)seed[_ -]?{seed}(?!\d)"),
        re.compile(rf"(?i)[\"']?seed[\"']?\s*[:=]\s*{seed}(?!\d)"),
        re.compile(rf"(?i)training_seed[^\n]{{0,12}}{seed}(?!\d)"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hits: dict[str, list[dict[str, object]]] = {str(seed): [] for seed in SEEDS}
    scanned_files = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        normalized = str(relative).replace("\\", "/")
        if normalized in PLANNED_CONTRACT_FILES or normalized.startswith("docs/drtp_stable_v2_d2_20260829/"):
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            continue
        scanned_files += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for seed in SEEDS:
            matches = []
            for pattern in semantic_patterns(seed):
                match = pattern.search(normalized) or pattern.search(text)
                if match:
                    matches.append(match.group(0))
            if matches:
                hits[str(seed)].append({"path": normalized, "matches": sorted(set(matches))})
    clean = all(not values for values in hits.values())
    payload = {
        "protocol": "DRTP-STABLE-V2-PILOT-SEED-PROVENANCE-V1",
        "candidate_seeds": list(SEEDS),
        "status": "CLEAN" if clean else "CONTAMINATED",
        "semantic_hits": hits,
        "scanned_text_files": scanned_files,
        "selection_rule": "next consecutive unused namespace after frozen 3001-3005 R1 cohort",
        "scientific_results_seen_before_freeze": False if clean else None,
        "training_started": False,
        "limitations": "Files over 5 MiB and binary archive payloads are not text-scanned; maintained configs, scripts, docs, manifests and paths are covered.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if clean else 1)


if __name__ == "__main__":
    main()
