# build_held_out_split_manifest.py
# FROZEN-PROTOCOL helper: builds the held-out split manifest and performs the
# 27/27 checkpoint input SHA audit for FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5.
#
# Inputs:
#   --manifest : joint_held_out_manifest_27.csv (frozen 27-checkpoint list)
# Outputs (same dir as --out-dir, git-tracked protocol assets):
#   held_out_split_manifest.json  (base seed + derivation + 27 inputs + volume)
#   held_out_split_manifest.csv   (27 rows + split columns)
#   held_out_input_sha_audit.csv  (27/27 file vs manifest sha)
#   held_out_input_sha_audit.md   (narrative)
#
# The base seed is derived deterministically from the manifest SHA and the
# fixed anchor string "formal-held-out-v1.5" (see protocol section 3.1).
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ABLATION_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
MAPPO_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5")
ANCHOR = "formal-held-out-v1.5"
RESERVED = {888000, 120000, 641939}
BASE_SEED = 745669  # frozen computed value (see protocol 3.1)
SCENARIOS = [
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
]
EPISODES_PER_SCENARIO = 100


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def derive_base_seed(manifest_sha: str) -> int:
    h = hashlib.sha256((manifest_sha + ANCHOR).encode()).hexdigest().upper()
    candidate = (int(h[0:8], 16) % 900000) + 100000
    while candidate in RESERVED:
        candidate = ((candidate + 1) % 900000) + 100000
    return candidate


def resolve_checkpoint(rel_or_abs: str) -> Path | None:
    p = Path(rel_or_abs)
    if p.is_absolute():
        return p if p.exists() else None
    for root in (ABLATION_ROOT, MAPPO_ROOT):
        cand = root / p
        if cand.exists():
            return cand
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_sha = sha256(args.manifest)
    recomputed_seed = derive_base_seed(manifest_sha)
    if recomputed_seed != BASE_SEED:
        raise SystemExit(f"base seed drift: recomputed {recomputed_seed} != frozen {BASE_SEED}")
    if recomputed_seed in RESERVED:
        raise SystemExit(f"base seed {recomputed_seed} hits a reserved value")

    with args.manifest.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 27:
        raise SystemExit(f"expected 27 manifest rows, got {len(rows)}")

    audit_rows: list[dict] = []
    problems: list[str] = []
    for r in rows:
        method = r["method"]
        seed = int(r["train_seed"])
        upd = r["selected_checkpoint_update"]
        ckpt = resolve_checkpoint(r["selected_checkpoint"])
        if ckpt is None:
            problems.append(f"{method} seed{seed}: checkpoint not resolvable: {r['selected_checkpoint']}")
            continue
        file_sha = sha256(ckpt)
        rec_sha = r["checkpoint_sha256"]
        ok = file_sha == rec_sha
        if not ok:
            problems.append(f"{method} seed{seed} upd{upd}: SHA mismatch file={file_sha} manifest={rec_sha}")
        audit_rows.append({
            "method": method, "train_seed": seed, "selected_checkpoint_update": upd,
            "checkpoint_abs": str(ckpt), "file_sha256": file_sha,
            "manifest_sha256": rec_sha, "match": "PASS" if ok else "FAIL",
        })

    n_pass = sum(1 for a in audit_rows if a["match"] == "PASS")
    all_ok = (len(audit_rows) == 27 and n_pass == 27 and not problems)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    split = {
        "generated": now,
        "protocol": "FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5",
        "status": "HELD-OUT TEST TARGET SET (one-shot)",
        "base_seed": BASE_SEED,
        "seed_derivation": {
            "manifest_csv_sha256": manifest_sha,
            "anchor": ANCHOR,
            "derivation_hash": hashlib.sha256((manifest_sha + ANCHOR).encode()).hexdigest().upper(),
            "formula": "candidate=(int(h[0:8],16)%900000)+100000; skip {888000,120000,641939}",
            "reserved_excluded": list(sorted(RESERVED)),
        },
        "episode_seed_rule": "episode_seed = base_seed + episode_index (matched across all 27 checkpoints)",
        "scenarios": SCENARIOS,
        "episodes_per_scenario": EPISODES_PER_SCENARIO,
        "total_episodes": 27 * len(SCENARIOS) * EPISODES_PER_SCENARIO,
        "checkpoints": len(rows),
        "input_sha_audit": {"27_of_27": all_ok, "pass": n_pass, "problems": problems},
        "no_selection": "True - held-out evaluates only locked checkpoints; no selector, no reselection",
    }
    (out_dir / "held_out_split_manifest.json").write_text(json.dumps(split, indent=2, ensure_ascii=False), encoding="utf-8")

    with (out_dir / "held_out_split_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()) + ["base_seed", "episodes_per_scenario", "scenarios"])
        w.writeheader()
        for a in audit_rows:
            a2 = dict(a)
            a2["base_seed"] = BASE_SEED
            a2["episodes_per_scenario"] = EPISODES_PER_SCENARIO
            a2["scenarios"] = ";".join(SCENARIOS)
            w.writerow(a2)
    with (out_dir / "held_out_input_sha_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audit_rows[0].keys()))
        w.writeheader()
        w.writerows(audit_rows)

    md = [
        "# Held-Out Input SHA Audit (27/27)",
        "",
        f"- generated: {now}",
        f"- protocol: FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5",
        f"- manifest csv sha256: {manifest_sha}",
        f"- held-out base seed: {BASE_SEED} (derivation frozen in protocol 3.1)",
        f"- input checkpoints: {len(audit_rows)}  pass: {n_pass}",
        f"- 27/27 input SHA match: {'PASS' if all_ok else 'FAIL'}",
        f"- total episodes: {split['total_episodes']} (27 x 4 x 100)",
        "",
        "## Per-checkpoint",
        "",
    ]
    for a in audit_rows:
        md.append(f"- [{'PASS' if a['match'] == 'PASS' else 'FAIL'}] {a['method']} seed{a['train_seed']} upd{a['selected_checkpoint_update']}: {a['file_sha256']}")
    md.append("")
    if problems:
        md.append("## PROBLEMS")
        for p in problems:
            md.append(f"- {p}")
        md.append("")
    md.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (out_dir / "held_out_input_sha_audit.md").write_text("\n".join(md), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"base seed: {BASE_SEED} (recomputed {recomputed_seed} match)")
    print(f"27/27 input sha: {n_pass}/{len(audit_rows)}")
    print(f"total episodes: {split['total_episodes']}")
    print(f"out: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
