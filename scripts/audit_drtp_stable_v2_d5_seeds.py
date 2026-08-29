"""Audit proposed D5 pilot seed identifiers without running an environment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (3201, 3202, 3203)
TEXT_SUFFIXES = {".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".py", ".sh", ".ps1"}
EXCLUDED_TOP_LEVEL = {".git", "tmp", "output"}


def patterns(seed: int) -> tuple[re.Pattern[str], ...]:
    return (
        re.compile(rf"(?i)seed[_ -]?{seed}(?!\d)"),
        re.compile(rf"(?i)[\"']?seed[\"']?\s*[:=]\s*{seed}(?!\d)"),
        re.compile(rf"(?i)training_seed[^\n]{{0,16}}{seed}(?!\d)"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    hits = {str(seed): [] for seed in SEEDS}
    scanned = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        normalized = str(relative).replace("\\", "/")
        if (
            normalized == "scripts/audit_drtp_stable_v2_d5_seeds.py"
            or normalized.startswith("docs/drtp_stable_v2_d5_20260829/")
            or normalized.startswith("configs/drtp_stable_v2_d5_")
            or "drtp_stable_v2_d5" in normalized
        ):
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        for seed in SEEDS:
            matched = sorted({match.group(0) for pattern in patterns(seed) if (match := pattern.search(normalized + "\n" + text))})
            if matched:
                hits[str(seed)].append({"path": normalized, "matches": matched})
    clean = all(not rows for rows in hits.values())
    payload = {
        "protocol": "DRTP-STABLE-V2-D5-SEED-PROVENANCE-V1",
        "candidate_seeds": list(SEEDS),
        "status": "CLEAN" if clean else "CONTAMINATED",
        "semantic_hits": hits,
        "scanned_text_files": scanned,
        "selection_rule": "next consecutive unused namespace after the completed 3101-3103 D2 pilot",
        "scientific_results_seen_before_freeze": False if clean else None,
        "training_started": False,
        "limitations": "Binary archives and text files over 5 MiB are not content-scanned; maintained paths, configs, manifests, scripts and docs are covered.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if clean else 1)


if __name__ == "__main__":
    main()
