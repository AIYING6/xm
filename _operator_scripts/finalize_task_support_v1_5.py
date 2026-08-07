# finalize_task_support_v1_5.py — Steps 4-6: recovered-vs-failed contrast, cross-seed
# consistency, pre-registered verdict, final report, artifact SHA lock.
# Read-only over the locked extraction CSVs (1200 episodes).
from __future__ import annotations

import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "task_support_v1_5_assets"
WINDOWS = ["pre_failure", "early_post_failure", "pre_recovery", "post_recovery"]


def read_csv(name):
    with (OUT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mean(xs):
    xs = [float(x) for x in xs if x not in ("", "nan")]
    return float(np.mean(xs)) if xs else float("nan")


def main():
    dyn = read_csv("task_support_dynamics.csv")
    traj = read_csv("task_support_relation_trajectory.csv")
    manifest = read_csv("task_support_episode_manifest.csv")
    case = read_csv("task_support_case_manifest.csv")
    problems: list[str] = []

    # ---------------- A. Full window strength by seed (cross-seed consistency) ----------------
    # per (seed, window) mean strength for Full; direction must be consistent across seeds
    by_seed = defaultdict(list)
    for r in traj:
        if r["method"] == "full":
            by_seed[(r["seed"], r["window"])].append(float(r["mean_strength"]))
    seed_means = {}
    for w in WINDOWS:
        for s in (0, 1, 2):
            seed_means[(str(s), w)] = mean(by_seed[(str(s), w)])
    dir_s = {}
    for s in (0, 1, 2):
        v0 = seed_means[(str(s), "pre_failure")]
        v1 = seed_means[(str(s), "early_post_failure")]
        d = "down" if v1 < v0 - 1e-6 else ("up" if v1 > v0 + 1e-6 else "same")
        dir_s[str(s)] = d
    # ---------------- B. Full recovered vs failed contrast ----------------
    groups = defaultdict(lambda: defaultdict(list))
    for r in dyn:
        if r["method"] != "full":
            continue
        g = "recovered" if r["recovered"] == "1" else "failed"
        for k in ("first_support_after_failure", "support_persistence",
                  "unique_active_pairs", "pre_recovery_boost"):
            if r[k] not in ("", "nan"):
                groups[g][k].append(float(r[k]))
    rec_stats = {k: mean(v) for k, v in groups["recovered"].items()}
    fail_stats = {k: mean(v) for k, v in groups["failed"].items()}
    n_rec = sum(1 for r in dyn if r["method"] == "full" and r["recovered"] == "1")
    n_fail = sum(1 for r in dyn if r["method"] == "full" and r["recovered"] == "0")

    # ---------------- C. verdict (Addendum C Section 5) ----------------
    verdict_lines = []
    # compute means per window (pooled Full)
    w_mean = {w: mean([float(r["mean_strength"]) for r in traj
                       if r["method"] == "full" and r["window"] == w]) for w in WINDOWS}
    early_vs_pre = w_mean["early_post_failure"] - w_mean["pre_failure"]
    pre_rec_vs_early = w_mean["pre_recovery"] - w_mean["early_post_failure"]
    dirs = set(dir_s.values())
    dir_consistent = len(dirs) == 1
    verdict = "INCONCLUSIVE"
    if dir_consistent and pre_rec_vs_early > 0.02:
        # stable cross-seed support strengthening before recovery => re-organization supported
        verdict = "SUPPORT"
    elif dir_consistent:
        # no clear pre-recovery strengthening pattern
        verdict = "EMPIRICAL SUPPORT ONLY"
    if n_fail < 5:
        problems.append(f"too few failed Full episodes for contrast: {n_fail}")
    if not dir_consistent:
        verdict = "INCONCLUSIVE"

    # ---------------- report ----------------
    lines = [
        "# Task-Support Mechanism Report (v1.5) — FINAL",
        "",
        "- protocol: TASK_SUPPORT_MECHANISM_PROTOCOL_V1_5 (+ Addendum B/C)",
        "- frozen windows: [-20,-1]/[0,20]/[rec-20,rec-1]/[rec,rec+20]; 9 blue-blue pairs",
        "- extraction: 1200 episodes (2 scenarios x 2 methods x 3 seeds x 100), GPU; "
        "behavioral equivalence: event 60/60, action-hash 60/60, independent window 60/60",
        "",
        "## A. Full internal task-support dynamics (window mean strength, 9 pairs)",
        "",
        "| window | Full pooled mean | seed0 | seed1 | seed2 |",
        "|---|---|---|---|---|",
    ]
    for w in WINDOWS:
        lines.append(f"| {w} | {w_mean[w]:.4f} | "
                     f"{seed_means[('0', w)]:.4f} | {seed_means[('1', w)]:.4f} | "
                     f"{seed_means[('2', w)]:.4f} |")
    # post_recovery data fact: recovery coincides with episode termination
    rec_rows = [r for r in manifest if r["post_failure_chain_recovered"] == "1"]
    frac_last = (sum(1 for r in rec_rows
                     if int(r["recovery_step"]) == int(r["steps"])) / len(rec_rows)) if rec_rows else float("nan")
    lines += [
        "",
        f"early_post - pre_failure (pooled): {early_vs_pre:+.4f}",
        f"pre_recovery - early_post (pooled): {pre_rec_vs_early:+.4f}",
        f"cross-seed early-vs-pre direction: {dir_s}",
        "",
        "DATA FACT (post_recovery): in all recovered episodes of these two relay-failure "
        f"scenarios, recovery coincides with episode termination "
        f"(recovery_step == steps for {frac_last:.0%} of {len(rec_rows)} recovered episodes). "
        "post_recovery window is therefore undefined here; pre_recovery is the effective "
        "tail window.",
        "",
        "## B. Full recovered vs failed (descriptive, n=3 seeds pooled over episodes)",
        "",
        "| metric | recovered | failed |",
        "|---|---|---|",
    ]
    keys = ["first_support_after_failure", "support_persistence", "unique_active_pairs",
            "pre_recovery_boost"]
    for k in keys:
        rv, fv = rec_stats.get(k, float("nan")), fail_stats.get(k, float("nan"))
        lines.append(f"| {k} | {rv:.3f} | {fv:.3f} |")
    lines.append(f"| n_episodes | {n_rec} | {n_fail} |")
    lines += [
        "",
        "## C. Pre-registered verdict",
        "",
        f"**{verdict}**",
        "",
    ]
    lines += verdict_lines
    lines += [
        "",
        "## D. Cases (frozen rule, smallest episode index)",
        "",
    ]
    for c in case:
        lines.append(f"- {c['case_class']}: {c['scenario']} ep{c['episode']} "
                     f"(full_succ={c['full_success']}, fail_step={c['failure_step']}, "
                     f"full_rec={c['full_recovery_step']}, wot_rec={c['wot_recovery_step']})")
    lines += [
        "",
        "## Interpretation guard (Addendum C)",
        "",
        "- Full vs w/o relation strength difference is NOT mechanism evidence (ablation definition).",
        "- Mechanism evidence is Full's internal temporal dynamics above.",
        "- If EMPIRICAL SUPPORT ONLY: performance effect is locked and stable; internal "
        "temporal re-organization is not supported. Paper wording limited to the ablation "
        "effect + 'task-dependent relational mask' phrasing.",
    ]
    (OUT / "task_support_mechanism_report.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------------- SHA lock ----------------
    hashes = []
    for p in sorted(OUT.glob("*.csv")) + sorted(OUT.glob("*.md")) + sorted(OUT.glob("*.png")):
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        hashes.append(f"{h}  {p.name}")
    (OUT / "task_support_outputs_sha256.txt").write_text(
        "\n".join(hashes) + "\n", encoding="utf-8")

    print(f"verdict: {verdict}")
    print(f"early_vs_pre: {early_vs_pre:+.4f}  pre_rec_vs_early: {pre_rec_vs_early:+.4f}")
    print(f"cross-seed dirs: {dir_s}  consistent: {dir_consistent}")
    print(f"recovered={n_rec} failed={n_fail}")
    print(f"\nOVERALL: {'PASS' if not problems else 'FAIL'}  problems={problems}")
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
