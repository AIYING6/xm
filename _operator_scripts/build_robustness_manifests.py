# build_robustness_manifests.py
# FROZEN-PROTOCOL helper: builds the robustness checkpoint manifest (21 rows
# from the held-out split manifest) and the robustness split manifest (10
# conditions, deterministic base seed 946804) for FORMAL_ROBUSTNESS_PROTOCOL_V1_5.
#
# Inputs:
#   --held-out-manifest : held_out_split_manifest.csv (27 rows, authoritative)
# Outputs (--out-dir):
#   robustness_checkpoint_manifest.csv   (21 rows: method, seed, update, abs, sha)
#   robustness_checkpoint_manifest.json
#   robustness_split_manifest.json       (base seed + derivation + 10 conditions)
#   robustness_checkpoint_sha256.txt     (21 lines)
#   robustness_input_sha_audit.md        (21/21 file vs manifest sha)
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = "formal-robustness-v1.5"
RESERVED = {888000, 120000, 641939, 745669}
BASE_SEED = 946804  # frozen computed value (protocol section 5)
METHODS = [
    "full_ea_rg", "w_o_role_pair_gate", "w_o_gate_prior", "w_o_task_support",
    "mappo", "happo", "param_matched_single",
]
SEEDS = [0, 1, 2]
EPISODES_PER_CONDITION = 50

# Unique frozen 10-condition table (protocol section 4, R00-R09)
CONDITIONS = [
    ("R00", "dropout030_delay2_relay_failure"),
    ("R01", "dropout050_delay2_relay_failure"),
    ("R02", "dropout070_delay2_relay_failure"),
    ("R03", "dropout030_delay4_relay_failure"),
    ("R04", "dropout030_delay8_relay_failure"),
    ("R05", "dropout030_delay2_relay_failure_early"),
    ("R06", "dropout030_delay2_relay_failure_delayed"),
    ("R07", "dropout030_delay2_scout_failure"),
    ("R08", "dropout030_delay2_relay_failure_late"),
    ("R09", "dropout070_delay8_relay_failure_early"),
]
CONDITION_PARAMS = {
    "dropout030_delay2_relay_failure": dict(dropout=0.30, delay=2, agent=1, start=40, duration=80),
    "dropout050_delay2_relay_failure": dict(dropout=0.50, delay=2, agent=1, start=40, duration=80),
    "dropout070_delay2_relay_failure": dict(dropout=0.70, delay=2, agent=1, start=40, duration=80),
    "dropout030_delay4_relay_failure": dict(dropout=0.30, delay=4, agent=1, start=40, duration=80),
    "dropout030_delay8_relay_failure": dict(dropout=0.30, delay=8, agent=1, start=40, duration=80),
    "dropout030_delay2_relay_failure_early": dict(dropout=0.30, delay=2, agent=1, start=25, duration=80),
    "dropout030_delay2_relay_failure_delayed": dict(dropout=0.30, delay=2, agent=1, start=55, duration=80),
    "dropout030_delay2_scout_failure": dict(dropout=0.30, delay=2, agent=0, start=40, duration=80),
    "dropout030_delay2_relay_failure_late": dict(dropout=0.30, delay=2, agent=1, start=70, duration=80),
    "dropout070_delay8_relay_failure_early": dict(dropout=0.70, delay=8, agent=1, start=25, duration=80),
}


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--held-out-manifest", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_sha = sha256(args.held_out_manifest)
    recomputed = derive_base_seed(manifest_sha)
    if recomputed != BASE_SEED:
        raise SystemExit(f"base seed drift: recomputed {recomputed} != frozen {BASE_SEED}")
    if recomputed in RESERVED:
        raise SystemExit(f"base seed {recomputed} hits reserved value")

    # ---- 21-row checkpoint manifest from held-out split manifest ----
    rows21: list[dict] = []
    with args.held_out_manifest.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["method"] in METHODS:
                rows21.append(r)
    if len(rows21) != 21:
        raise SystemExit(f"expected 21 robustness checkpoints, got {len(rows21)}")

    # 21/21 input SHA audit (file vs manifest sha)
    problems: list[str] = []
    audited: list[dict] = []
    for r in rows21:
        ckpt = Path(r["checkpoint_abs"])
        if not ckpt.exists():
            problems.append(f"{r['method']} seed{r['train_seed']}: missing {ckpt}")
            continue
        file_sha = sha256(ckpt)
        ok = file_sha == r["manifest_sha256"]
        if not ok:
            problems.append(f"{r['method']} seed{r['train_seed']}: SHA mismatch {file_sha} vs {r['manifest_sha256']}")
        audited.append({
            "method": r["method"], "train_seed": int(r["train_seed"]),
            "selected_checkpoint_update": r["selected_checkpoint_update"],
            "checkpoint_abs": str(ckpt), "file_sha256": file_sha,
            "manifest_sha256": r["manifest_sha256"], "match": "PASS" if ok else "FAIL",
        })

    n_pass = sum(1 for a in audited if a["match"] == "PASS")
    all_ok = (len(audited) == 21 and n_pass == 21 and not problems)
    if not all_ok:
        for p in problems:
            print("PROBLEM:", p)
        raise SystemExit("robustness input SHA audit FAILED")

    with (out_dir / "robustness_checkpoint_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audited[0].keys()))
        w.writeheader(); w.writerows(audited)
    (out_dir / "robustness_checkpoint_sha256.txt").write_text(
        "\n".join(f"{a['file_sha256']}  {a['method']} seed{a['train_seed']} upd{a['selected_checkpoint_update']}" for a in audited) + "\n",
        encoding="utf-8")
    ckpt_json = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "protocol": "FORMAL_ROBUSTNESS_PROTOCOL_V1_5",
        "total_checkpoints": len(audited),
        "methods": METHODS,
        "input_sha_audit": {"21_of_21": all_ok, "pass": n_pass},
        "checkpoints": audited,
    }
    (out_dir / "robustness_checkpoint_manifest.json").write_text(json.dumps(ckpt_json, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- split manifest ----
    split = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "protocol": "FORMAL_ROBUSTNESS_PROTOCOL_V1_5",
        "base_seed": BASE_SEED,
        "seed_derivation": {
            "held_out_split_manifest_sha256": manifest_sha,
            "anchor": ANCHOR,
            "derivation_hash": hashlib.sha256((manifest_sha + ANCHOR).encode()).hexdigest().upper(),
            "formula": "candidate=(int(h[0:8],16)%900000)+100000; skip {888000,120000,641939,745669}",
        },
        "episode_seed_rule": "episode_seed = base_seed + episode_index (matched across 21 checkpoints x 10 conditions)",
        "episodes_per_condition": EPISODES_PER_CONDITION,
        "total_episodes": 21 * len(CONDITIONS) * EPISODES_PER_CONDITION,
        "conditions": [{"id": cid, "key": k, **CONDITION_PARAMS[k]} for cid, k in CONDITIONS],
        "no_selection": "True - robustness evaluates locked checkpoints only; no selector",
    }
    (out_dir / "robustness_split_manifest.json").write_text(json.dumps(split, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Robustness Input SHA Audit (21/21)",
        "",
        f"- protocol: FORMAL_ROBUSTNESS_PROTOCOL_V1_5",
        f"- robustness base seed: {BASE_SEED} (derivation frozen in protocol section 5)",
        f"- input checkpoints: {len(audited)}  pass: {n_pass}",
        f"- 21/21 input SHA match: {'PASS' if all_ok else 'FAIL'}",
        f"- total episodes: {split['total_episodes']} (21 x 10 x 50)",
        "",
        "## Per-checkpoint",
        "",
    ]
    for a in audited:
        md.append(f"- [{'PASS' if a['match'] == 'PASS' else 'FAIL'}] {a['method']} seed{a['train_seed']} upd{a['selected_checkpoint_update']}: {a['file_sha256']}")
    md.append("")
    md.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (out_dir / "robustness_input_sha_audit.md").write_text("\n".join(md), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"base seed: {BASE_SEED} (recomputed {recomputed} match)")
    print(f"21/21 input sha: {n_pass}/{len(audited)}")
    print(f"total episodes: {split['total_episodes']}")
    print(f"out: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
