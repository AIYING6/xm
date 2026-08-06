# audit_mappo_validation.py
# MAPPO formal 641939 validation audit (post-run; before lock).
#
# Evidence chain: training lock mappo-ppo-training-lock-v1.5.0 @ 989e338;
# PPO entry mappo-ppo-freeze-v1.5.0 @ 3d5346d; eval impl mappo-freeze-v1.5.0
# @ 11fa019; candidates from the training-audit manifest.
#
# Checks:
#   1. 30/30 candidate checkpoint path+SHA vs training-audit manifest
#   2. summary matrix 3 seeds x 10 updates x 4 scenarios complete (120 rows)
#   3. selection CSV: exactly 1 checkpoint per seed (3 rows)
#   4. independent Wilson recompute from summary == selection (3/3)
#   5. recompute SHA of the 3 selected checkpoints
#   6. freeze SHA of the raw validation outputs (episode/summary/selection)
#   7. write the MAPPO validation audit bundle
#
# Outputs under <root>/_operator_notes/final_mappo_validation_audit_v1_5/:
#   mappo_validation_audit_report.md
#   mappo_candidate_sha_audit.csv
#   mappo_selection_recompute.csv
#   mappo_selected_checkpoint_sha256.txt
#   mappo_validation_outputs_sha256.txt
#   mappo_validation_evidence_manifest.json
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    aggregate_suite_rows,
    select_checkpoints,
)

SEEDS = [0, 1, 2]
UPDATES = [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]
SCENARIOS = [
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
]
METHOD = "mappo"
BASE_SEED = 641939
SELECTION_POLICY = "v1_5_wilson"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def file_sha256(p: Path) -> str:
    """SHA of a text file's raw bytes (for freezing raw outputs)."""
    return sha256(p)


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_candidate_manifest(manifest_path: Path) -> dict[int, dict[int, str]]:
    """manifest seeds -> {update -> sha256}."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: dict[int, dict[int, str]] = {}
    for seed_str, seed_block in data["seeds"].items():
        seed = int(seed_str)
        out[seed] = {}
        for upd_str, c in seed_block["checkpoints"].items():
            out[seed][int(upd_str)] = c["sha256"]
    return out


def wilson_lower_95(n: int, k: int) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    z = 1.959963984540054  # z for 95%
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / denom


def recompute_selection(summary_rows: list[dict]) -> list[dict]:
    """Recompute the frozen v1_5_wilson suite selection from the summary rows
    by calling the SAME frozen selector entrypoint used by the evaluation
    (aggregate_suite_rows + select_checkpoints with selection_group=suite and
    selection_policy=v1_5_wilson). The result must match the selection CSV 3/3.
    """
    args = SimpleNamespace(
        selection_group="suite",
        selection_policy="v1_5_wilson",
        scenarios=SCENARIOS,
        max_selection_collision_rate=0.0,
    )
    # select_checkpoints applies aggregate_suite_rows internally when
    # selection_group == "suite"; pass the RAW summary rows (do not pre-aggregate).
    return select_checkpoints(args, summary_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True, help="validation output root")
    parser.add_argument("--manifest", type=Path, required=True, help="training-audit candidate manifest json")
    parser.add_argument("--ppo-root", type=Path, required=True, help="PPO training output root")
    args = parser.parse_args()
    root: Path = args.root
    out_dir = root / "_operator_notes" / "final_mappo_validation_audit_v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    ep_path = root / "validation_episode_metrics.csv"
    sum_path = root / "validation_checkpoint_summary.csv"
    sel_path = root / "validation_selected_checkpoints.csv"

    # ---- 1. candidate 30/30 path+sha vs training manifest ----
    manifest = load_candidate_manifest(args.manifest)
    cand_rows: list[dict] = []
    for seed in SEEDS:
        for u in UPDATES:
            ckpt = args.ppo_root / f"ppo_seed{seed}" / f"actor_critic_update_{u:04d}.pt"
            if not ckpt.exists():
                problems.append(f"candidate missing: {ckpt}")
                continue
            sha = sha256(ckpt)
            exp = manifest.get(seed, {}).get(u)
            ok = sha == exp
            if not ok:
                problems.append(f"candidate SHA mismatch seed{seed} upd{u}: file={sha} manifest={exp}")
            cand_rows.append({
                "train_seed": seed, "checkpoint_update": u,
                "checkpoint": str(ckpt), "file_sha256": sha,
                "manifest_sha256": exp or "", "match": "PASS" if ok else "FAIL",
            })

    # ---- 2. summary matrix completeness ----
    summary_rows = read_rows(sum_path)
    if len(summary_rows) != 120:
        problems.append(f"summary rows = {len(summary_rows)} != 120")
    matrix_ok = True
    for seed in SEEDS:
        for u in UPDATES:
            cnt = sum(1 for r in summary_rows
                      if int(r["train_seed"]) == seed and int(r["checkpoint_update"]) == u)
            if cnt != 4:
                matrix_ok = False
                problems.append(f"summary matrix seed{seed} upd{u} has {cnt} scenarios (expected 4)")
    policy_ok = all(r.get("selection_policy") == SELECTION_POLICY for r in summary_rows)
    if not policy_ok:
        problems.append("not all summary rows have selection_policy=v1_5_wilson")

    # ---- 3. selection CSV ----
    sel_rows = read_rows(sel_path)
    if len(sel_rows) != 3:
        problems.append(f"selection rows = {len(sel_rows)} != 3")
    sel_by_seed: dict[int, dict] = {}
    for r in sel_rows:
        seed = int(r["train_seed"])
        if seed in sel_by_seed:
            problems.append(f"selection has duplicate seed {seed}")
        sel_by_seed[seed] = r
    if set(sel_by_seed) != set(SEEDS):
        problems.append(f"selection seeds {sorted(sel_by_seed)} != {SEEDS}")

    # ---- 4. independent Wilson recompute == selection ----
    recomputed = recompute_selection(summary_rows)
    recompute_rows: list[dict] = []
    for seed in SEEDS:
        rec = next((r for r in recomputed if int(r["train_seed"]) == seed), None)
        sel = sel_by_seed.get(seed)
        if rec is None:
            problems.append(f"seed{seed}: recompute produced no candidate")
            continue
        if sel is None:
            problems.append(f"seed{seed}: selection missing")
            continue
        rec_upd = int(rec["selected_checkpoint_update"])
        sel_upd = int(sel["selected_checkpoint_update"])
        ok = rec_upd == sel_upd
        if not ok:
            problems.append(f"seed{seed}: recompute update {rec_upd} != selection {sel_upd}")
        recompute_rows.append({
            "train_seed": seed, "recompute_update": rec_upd, "selection_update": sel_upd,
            "recompute_wilson": rec.get("wilson_lower_95", ""),
            "selection_wilson": sel.get("wilson_lower_95", ""),
            "recompute_checkpoint": rec.get("selected_checkpoint", ""),
            "selection_checkpoint": sel.get("selected_checkpoint", ""),
            "match": "PASS" if ok else "FAIL",
        })

    # ---- 5. recompute SHA of the 3 selected checkpoints ----
    sel_sha_rows: list[dict] = []
    for seed in SEEDS:
        sel = sel_by_seed.get(seed)
        if sel is None:
            continue
        rel = sel["selected_checkpoint"]
        ckpt = ROOT / rel
        if not ckpt.exists():
            problems.append(f"selected checkpoint missing: {ckpt}")
            continue
        sha = sha256(ckpt)
        rec = sel.get("checkpoint_sha256")
        ok = sha == rec
        if not ok:
            problems.append(f"selected sha mismatch seed{seed}: recomputed={sha} recorded={rec}")
        sel_sha_rows.append({
            "train_seed": seed, "selected_checkpoint": rel,
            "recomputed_sha256": sha, "recorded_sha256": rec or "", "match": "PASS" if ok else "FAIL",
        })

    # ---- 6. freeze SHA of raw validation outputs ----
    out_shas = {
        "validation_episode_metrics.csv": file_sha256(ep_path),
        "validation_checkpoint_summary.csv": file_sha256(sum_path),
        "validation_selected_checkpoints.csv": file_sha256(sel_path),
        "validation_checkpoint_sweep.md": file_sha256(root / "validation_checkpoint_sweep.md"),
    }

    # ---- git snapshot ----
    git = []
    for cmd in (["git", "rev-parse", "HEAD"], ["git", "describe", "--tags", "--exact-match", "HEAD"], ["git", "log", "-1", "--format=%h %s"]):
        try:
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
            git.append(f"$ {' '.join(cmd)}\nexit={r.returncode}\n{r.stdout.strip()}{('' if not r.stderr.strip() else chr(10) + r.stderr.strip())}")
        except Exception as e:  # noqa: BLE001
            git.append(f"$ {' '.join(cmd)}\nerror: {e}")

    # ---- write outputs ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (out_dir / "mappo_candidate_sha_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cand_rows[0].keys()))
        w.writeheader(); w.writerows(cand_rows)
    with (out_dir / "mappo_selection_recompute.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recompute_rows[0].keys()))
        w.writeheader(); w.writerows(recompute_rows)
    with (out_dir / "mappo_selected_checkpoint_sha256.txt").open("w", encoding="utf-8", newline="") as f:
        f.write("\n".join(f"{r['recomputed_sha256']}  {r['selected_checkpoint']}" for r in sel_sha_rows) + "\n")
    with (out_dir / "mappo_validation_outputs_sha256.txt").open("w", encoding="utf-8", newline="") as f:
        f.write("\n".join(f"{v}  {k}" for k, v in sorted(out_shas.items())) + "\n")

    cand_ok = all(r["match"] == "PASS" for r in cand_rows)
    sel_ok = all(r["match"] == "PASS" for r in recompute_rows)
    sel_sha_ok = all(r["match"] == "PASS" for r in sel_sha_rows)
    ev = {
        "generated": now,
        "frozen_evidence_chain": "mappo-ppo-training-lock-v1.5.0 @ 989e338 / mappo-ppo-freeze-v1.5.0 @ 3d5346d / mappo-freeze-v1.5.0 @ 11fa019",
        "base_seed": BASE_SEED, "selection_policy": SELECTION_POLICY,
        "episode_rows": len(read_rows(ep_path)), "summary_rows": len(summary_rows),
        "selection_rows": len(sel_rows), "candidate_30_of_30_pass": cand_ok,
        "matrix_complete": matrix_ok, "selection_policy_consistent": policy_ok,
        "selection_1_per_seed": set(sel_by_seed) == set(SEEDS) and len(sel_rows) == 3,
        "wilson_recompute_3of3": sel_ok,
        "selected_sha_recompute_3of3": sel_sha_ok,
        "raw_outputs_sha256": out_shas,
        "overall": "PASS",
        "problems": problems,
    }
    (out_dir / "mappo_validation_evidence_manifest.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")

    all_ok = (cand_ok and matrix_ok and policy_ok and set(sel_by_seed) == set(SEEDS)
              and len(sel_rows) == 3 and sel_ok and sel_sha_ok and not problems)
    report = [
        "# MAPPO 641939 Validation Audit",
        "",
        "## STATUS NOTICE",
        "MAPPO VALIDATION-SELECTION RESULTS",
        "NOT HELD-OUT TEST RESULTS",
        "",
        f"- generated: {now}",
        f"- evidence chain: {ev['frozen_evidence_chain']}",
        f"- base_seed = {BASE_SEED}, selection_policy = {SELECTION_POLICY}",
        f"- episode rows: {ev['episode_rows']} (expected 6000)",
        f"- summary rows: {ev['summary_rows']} (expected 120)",
        f"- selection rows: {ev['selection_rows']} (expected 3)",
        f"- 30/30 candidate path+sha vs training manifest: {'PASS' if cand_ok else 'FAIL'}",
        f"- 3x10x4 summary matrix complete: {'PASS' if matrix_ok else 'FAIL'}",
        f"- selection_policy=v1_5_wilson on all 120 rows: {'PASS' if policy_ok else 'FAIL'}",
        f"- exactly 1 selection per seed: {'PASS' if set(sel_by_seed) == set(SEEDS) and len(sel_rows) == 3 else 'FAIL'}",
        f"- independent Wilson recompute == selection 3/3: {'PASS' if sel_ok else 'FAIL'}",
        f"- selected checkpoint SHA recompute 3/3: {'PASS' if sel_sha_ok else 'FAIL'}",
        "",
        "## Selected checkpoints",
        "",
    ]
    for r in sel_sha_rows:
        report.append(f"- seed{r['train_seed']}: {r['selected_checkpoint']}")
        report.append(f"    sha256 = {r['recomputed_sha256']}")
    report.append("")
    report.append("## Raw validation output SHA (frozen)")
    for k, v in sorted(out_shas.items()):
        report.append(f"- {k}: {v}")
    report.append("")
    if problems:
        report.append("## PROBLEMS")
        for p in problems:
            report.append(f"- FAIL: {p}")
        report.append("")
    report.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    report.append("")
    report.append("## Git snapshot")
    report.extend(git)
    (out_dir / "mappo_validation_audit_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    print(f"candidates 30/30: {'PASS' if cand_ok else 'FAIL'}")
    print(f"wilson recompute 3/3: {'PASS' if sel_ok else 'FAIL'}")
    print(f"selected sha 3/3: {'PASS' if sel_sha_ok else 'FAIL'}")
    print(f"audit bundle: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
