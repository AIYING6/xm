# build_mappo_joint_27_manifest.py
# Merge the frozen 24-checkpoint lock (original 8 methods, tag
# formal-ablation-validation-lock-v1.5.0 @ 65bd96c) with the MAPPO 3-checkpoint
# lock (mappo-validation-lock-v1.5.0 @ ec08b50) into a 27-checkpoint joint
# held-out manifest. Read-only w.r.t. the original lock assets.
#
# Output (in the MAPPO repo, under the validation audit bundle):
#   joint_held_out_manifest_27.csv
#   joint_held_out_manifest_27.json
#   joint_held_out_checkpoint_sha256.txt
#   joint_held_out_manifest_27.md
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ORIGINAL_24 = Path(
    r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5/results/paper_config_runs/"
    r"formal_ablation_v1.5_validation_selector_v1.5.1_20260805/_operator_notes/"
    r"final_validation_audit_v1_5/selected_checkpoints_24.csv"
)
MAPPO_3 = Path(
    r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/"
    r"formal_mappo_v1.5_validation_selector_v1.5.1_20260806/validation_selected_checkpoints.csv"
)
MAPPO_3_SHA = Path(
    r"D:/Code/Codex/ri_gmappo_uav_mappo_v1.5/results/paper_config_runs/"
    r"formal_mappo_v1.5_validation_selector_v1.5.1_20260806/_operator_notes/"
    r"final_mappo_validation_audit_v1_5/mappo_selected_checkpoint_sha256.txt"
)
MAPPO_SHA_COL = "checkpoint_sha256"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with ORIGINAL_24.open("r", encoding="utf-8", newline="") as f:
        original = list(csv.DictReader(f))
    if len(original) != 24:
        raise SystemExit(f"expected 24 original rows, got {len(original)}")

    with MAPPO_3.open("r", encoding="utf-8", newline="") as f:
        mappo = list(csv.DictReader(f))
    if len(mappo) != 3:
        raise SystemExit(f"expected 3 MAPPO rows, got {len(mappo)}")

    # MAPPO per-seed sha from the audit bundle (recomputed, authoritative).
    # Each line: "<SHA>  <rel-path>/ppo_seed{seed}/actor_critic_update_XXXX.pt"
    mappo_sha: dict[int, str] = {}
    for line in MAPPO_3_SHA.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ")
        if len(parts) == 2:
            rel = parts[1].strip()
            for seed in (0, 1, 2):
                if f"/ppo_seed{seed}/" in rel or rel.startswith(f"ppo_seed{seed}/"):
                    mappo_sha[seed] = parts[0]
    if set(mappo_sha) != {0, 1, 2}:
        raise SystemExit(f"MAPPO sha extraction failed: {mappo_sha}")

    # Unify: build 27 rows with the original 24 columns (method, train_seed,
    # selected_checkpoint_update, selected_checkpoint, checkpoint_sha256, ...).
    rows = list(original)
    for r in mappo:
        seed = int(r["train_seed"])
        rows.append({
            "method": "mappo",
            "train_seed": seed,
            "selected_checkpoint_update": r["selected_checkpoint_update"],
            "selected_checkpoint": r["selected_checkpoint"],
            "checkpoint_sha256": mappo_sha.get(seed, r["checkpoint_sha256"]),
            "failure_exposed_count": r["failure_exposed_count"],
            "recovered_given_exposure_count": r["recovered_given_exposure_count"],
            "recovery_given_exposure": r["recovery_given_exposure"],
            "wilson_lower_95": r["wilson_lower_95"],
            "estimate_unstable": r["estimate_unstable"],
            "collision_mean": r["collision_mean"],
            "success_mean": r["success_mean"],
            "time_to_recovery_given_exposure": r["time_to_recovery_given_exposure"],
            "time_to_success": r["time_to_success"],
            "selection_policy": r["selection_policy"],
            "audit_status": "PASS",
        })
    if len(rows) != 27:
        raise SystemExit(f"expected 27 rows, got {len(rows)}")

    # integrity: 27 unique checkpoint sha, one per (method, seed)
    seen: set[str] = set()
    for r in rows:
        s = r["checkpoint_sha256"]
        if s in seen:
            raise SystemExit(f"duplicate checkpoint sha {s}")
        seen.add(s)
    key_counts: dict[str, int] = {}
    for r in rows:
        key = (r["method"], r["train_seed"])
        key_counts[str(key)] = key_counts.get(str(key), 0) + 1
    dup = {k: v for k, v in key_counts.items() if v != 1}
    if dup:
        raise SystemExit(f"non-unique (method, seed) pairs: {dup}")

    fieldnames = list(original[0].keys())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with (out_dir / "joint_held_out_manifest_27.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    with (out_dir / "joint_held_out_checkpoint_sha256.txt").open("w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write(f"{r['checkpoint_sha256']}  {r['method']} seed{r['train_seed']} upd{r['selected_checkpoint_update']}\n")
    sha_csv = sha256_file(out_dir / "joint_held_out_manifest_27.csv")
    summary = {
        "generated": now,
        "total_checkpoints": len(rows),
        "methods": sorted({r["method"] for r in rows}),
        "method_counts": {m: sum(1 for r in rows if r["method"] == m) for m in sorted({r["method"] for r in rows})},
        "original_24_lock": "formal-ablation-validation-lock-v1.5.0 @ 65bd96c",
        "mappo_3_lock": "mappo-validation-lock-v1.5.0 @ ec08b50",
        "base_seed": 641939,
        "selection_policy": "v1_5_wilson",
        "status": "JOINT HELD-OUT MANIFEST (27 checkpoints) - TEST TARGET SET",
        "manifest_csv_sha256": sha_csv,
    }
    (out_dir / "joint_held_out_manifest_27.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    sha_json = sha256_file(out_dir / "joint_held_out_manifest_27.json")

    md = [
        "# 27-Checkpoint Joint Held-Out Manifest",
        "",
        "## STATUS NOTICE",
        "JOINT HELD-OUT TEST TARGET SET",
        "NOT VALIDATION-SELECTION RESULTS",
        "NOT TRAINING RESULTS",
        "",
        f"- generated: {now}",
        f"- total checkpoints: {len(rows)}",
        f"- original 24 lock: formal-ablation-validation-lock-v1.5.0 @ 65bd96c (8 methods)",
        f"- MAPPO 3 lock: mappo-validation-lock-v1.5.0 @ ec08b50",
        f"- validation base_seed: 641939 (all 27 from the SAME validation split)",
        f"- selection_policy: v1_5_wilson",
        "",
        "## Method breakdown",
        "",
    ]
    for m in sorted({r["method"] for r in rows}):
        cnt = sum(1 for r in rows if r["method"] == m)
        md.append(f"- {m}: {cnt} checkpoint(s)")
    md.append("")
    md.append("## Checkpoint list (method / seed / update / sha256)")
    md.append("")
    for r in rows:
        md.append(f"- {r['method']} seed{r['train_seed']} upd{r['selected_checkpoint_update']}  "
                  f"{r['checkpoint_sha256']}")
    md.append("")
    md.append("## Locking summary")
    md.append("")
    md.append("- 24 original (8 methods) frozen at `formal-ablation-validation-lock-v1.5.0 @ 65bd96c`")
    md.append("- 3 MAPPO frozen at `mappo-validation-lock-v1.5.0 @ ec08b50`")
    md.append("- 27-checkpoint joint manifest: TEST TARGET SET for held-out evaluation")
    (out_dir / "joint_held_out_manifest_27.md").write_text("\n".join(md), encoding="utf-8")

    # append the json sha into the summary and rewrite (self-referential, frozen)
    summary["manifest_json_sha256"] = sha_json
    (out_dir / "joint_held_out_manifest_27.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("methods:", summary["method_counts"])
    print(f"total: {len(rows)}")
    print(f"manifest csv sha: {sha_csv}")
    print(f"manifest json sha: {sha_json}")
    print(f"out: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
