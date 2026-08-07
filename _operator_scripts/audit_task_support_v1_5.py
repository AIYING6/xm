# audit_task_support_v1_5.py — Step 1: artifact integrity audit (read-only).
# Checks coverage, duplicates, NaN, missing action hash for the locked extraction.
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "task_support_v1_5_assets"
EXPECT_CELLS = 12       # 2 methods x 3 seeds x 2 scenarios
EXPECT_EPS = 100

problems: list[str] = []


def read_csv(name: str):
    p = OUT / name
    if not p.exists():
        problems.append(f"missing {name}")
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


manifest = read_csv("task_support_episode_manifest.csv")
traj = read_csv("task_support_relation_trajectory.csv")
dyn = read_csv("task_support_dynamics.csv")

# 1. coverage
cells = Counter((r["method"], r["seed"], r["scenario"]) for r in manifest)
if len(cells) != EXPECT_CELLS:
    problems.append(f"manifest cells={len(cells)} (expect {EXPECT_CELLS})")
for k, n in sorted(cells.items()):
    if n != EXPECT_EPS:
        problems.append(f"cell {k}: {n} episodes (expect {EXPECT_EPS})")

# 2. duplicates
keys = [(r["method"], r["seed"], r["scenario"], r["episode"]) for r in manifest]
dups = {k for k, c in Counter(keys).items() if c > 1}
if dups:
    problems.append(f"duplicate (method,seed,scenario,episode): {sorted(dups)[:5]}")

# 3. NaN / empty checks
for i, r in enumerate(manifest):
    for fld in ("success", "steps", "failure_step", "recovery_step", "action_hash"):
        v = r.get(fld, "")
        if fld == "action_hash":
            if len(v) != 16:
                problems.append(f"manifest[{i}] bad action_hash '{v}'")
        elif v in ("", "nan", "None"):
            problems.append(f"manifest[{i}] empty field {fld}")

# 4. hash consistency across trajectory/dynamics
hashes = {r["action_hash"] for r in manifest}
if len(hashes) < 10:
    problems.append(f"action hash entropy too low: {len(hashes)} unique")
if len(dyn) != len(manifest):
    problems.append(f"dynamics rows={len(dyn)} vs manifest={len(manifest)}")
else:
    mismatch = sum(1 for a, b in zip(dyn, manifest) if a["action_hash"] != b["action_hash"])
    if mismatch:
        problems.append(f"action_hash mismatch dyn vs manifest: {mismatch}")

# 5. window sanity: pre/post recovery windows present when recovery exists
rec_eps = [r for r in manifest if r["post_failure_chain_recovered"] == "1"]
if not rec_eps:
    problems.append("no recovered episodes at all")
else:
    sample = rec_eps[:3]
    for r in sample:
        ep_key = (r["method"], r["seed"], r["scenario"], r["episode"])
        has_pre_rec = any(t["window"] == "pre_recovery" and
                          (t["method"], t["seed"], t["scenario"], t["episode"]) == ep_key
                          for t in traj)
        if not has_pre_rec:
            problems.append(f"recovered episode missing pre_recovery window: {ep_key}")

# 6. totals
print(f"manifest rows: {len(manifest)}  trajectory rows: {len(traj)}  dynamics rows: {len(dyn)}")
print(f"cells: {len(cells)}  unique action hashes: {len(hashes)}")
print(f"recovered episodes: {len(rec_eps)}/{len(manifest)}")
print(f"\nOVERALL: {'PASS' if not problems else 'FAIL'}")
for p in problems[:20]:
    print("  -", p)
sys.exit(0 if not problems else 1)
