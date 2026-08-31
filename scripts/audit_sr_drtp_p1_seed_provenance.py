"""Audit proposed SR-DRTP P1 seeds without launching an experiment."""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "configs" / "sr_drtp_p1_shadow_preparation_freeze.json"
TEXT_SUFFIXES = {".json", ".md", ".py", ".sh", ".toml", ".yaml", ".yml"}

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8")); seeds = freeze["cohorts"]["A"] + freeze["cohorts"]["B"]
    pattern = re.compile(r"(?:(?:\"seed\"\s*:\s*)|(?:--seed\s+)|(?:seed[_-]?))(" + "|".join(map(str, seeds)) + r")(?!\d)", re.I)
    hits: dict[int, list[str]] = {seed: [] for seed in seeds}
    # A generated provenance report necessarily contains the proposed seeds.
    # Exclude both outputs so a repeatable audit cannot contaminate itself.
    excluded = {args.output.resolve(), args.output.with_suffix(".json").resolve()}
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.lower() not in TEXT_SUFFIXES
            or path.resolve() in excluded
        ):
            continue
        try: text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError: continue
        for match in pattern.finditer(text): hits[int(match.group(1))].append(str(path.relative_to(ROOT)))
    rows = [{"seed": seed, "explicit_prior_use_hits": len(sorted(set(hits[seed]))), "clean": not hits[seed], "paths": ";".join(sorted(set(hits[seed])))} for seed in seeds]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    payload = {"protocol": freeze["protocol"], "status": "P1_SEEDS_CLEAN" if all(row["clean"] for row in rows) else "P1_SEED_CONTAMINATION_FOUND", "seeds": rows, "scan_limit": "explicit seed fields, CLI arguments, and seed-prefixed names in uncompressed source/document text", "execution_authorized": False}
    report = args.output.with_suffix(".json"); report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "report": str(report)}, indent=2))
if __name__ == "__main__": main()
