# audit_held_out_v1_5.py
# Post-run formal audit of the 27-checkpoint held-out test (attempt02,
# FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5, ops v1.5.1).
#
# Checks:
#   1. 27/27 method-seed groups exist with COMPLETE, no IN_PROGRESS
#   2. per-group episode rows == 400 (4 scenarios x 100), unique keys, no NaN/Inf
#   3. total episode rows == 10,800
#   4. per-group summary rows == 4; split=test; base_seed derived from
#      episode seed (seed = 745669 + episode); locked update
#   5. selection CSV empty (0 data rows) -- no reselection
#   6. checkpoint SHA/update == split manifest (27/27) via manifest abs path
#   7. seed-level stats (from frozen summary aggregation) + method-level stats
#      (3-seed mean +/- SD, worst seed)
#   8. Full minus rival per-seed deltas (MAPPO/HAPPO/param-matched/3 ablations)
#   9. freeze raw output SHA
#
# Outputs under <root>/_operator_notes/final_held_out_audit_v1_5/:
#   held_out_audit_report.md
#   held_out_group_audit.csv
#   held_out_seed_stats.csv
#   held_out_method_stats.csv
#   held_out_full_minus_rival.csv
#   held_out_outputs_sha256.txt
#   held_out_evidence_manifest.json
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(AB_ROOT))

from scripts.evaluate_3d_checkpoint_sweep import failure_exposure_stats  # noqa: E402

SCENARIOS = [
    "dropout030_delay2_relay_failure_early",
    "dropout030_delay2_relay_failure",
    "dropout030_delay2_relay_failure_delayed",
    "dropout030_delay2_relay_failure_late",
]
METHODS = [
    "full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
    "no_graph", "single_graph", "param_matched_single", "happo", "mappo",
]
SEEDS = [0, 1, 2]
BASE_SEED = 745669
EXPECTED_PER_GROUP = 400  # 4 scenarios x 100 episodes
TOTAL = 27 * 400


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_manifest(manifest_csv: Path) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    with manifest_csv.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out[(r["method"], int(r["train_seed"]))] = r
    return out


def mean_sd(xs: list[float]) -> tuple[float, float]:
    a = np.array([x for x in xs if not math.isnan(x)], dtype=float)
    if a.size == 0:
        return float("nan"), float("nan")
    return float(a.mean()), float(a.std(ddof=1))  # sample SD over 3 seeds


def mean_finite(xs: list[float]) -> float:
    vals = [x for x in xs if math.isfinite(x)]
    return float(np.mean(vals)) if vals else float("nan")


def wilson_lower_95(n: int, k: float) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    z = 1.959963984540054
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / denom


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True, help="held_out_split_manifest.csv")
    args = parser.parse_args()
    root: Path = args.root
    manifest = load_manifest(args.manifest)
    out_dir = root / "_operator_notes" / "final_held_out_audit_v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    group_rows: list[dict] = []
    seed_rows: list[dict] = []
    output_shas: dict[str, str] = {}
    total_ep = 0

    for method in METHODS:
        for seed in SEEDS:
            gdir = root / "held_out_v1.5" / method / f"seed{seed}"
            complete = (gdir / "COMPLETE").exists()
            in_progress = (gdir / "IN_PROGRESS").exists()
            if not complete:
                problems.append(f"{method}/seed{seed}: COMPLETE missing")
            if in_progress:
                problems.append(f"{method}/seed{seed}: IN_PROGRESS present")
            ep_csv = gdir / "test_episode_metrics.csv"
            su_csv = gdir / "test_checkpoint_summary.csv"
            sel_csv = gdir / "test_selected_checkpoints.csv"
            # ---- episode ----
            rows = list(csv.DictReader(ep_csv.open(encoding="utf-8")))
            total_ep += len(rows)
            scen = Counter(r.get("scenario", "") for r in rows)
            ok_scen = all(scen.get(s, 0) == 100 for s in SCENARIOS) and len(scen) == 4
            keys = [(r.get("graph_encoder"), r.get("train_seed"), r.get("scenario"), r.get("episode")) for r in rows]
            uniq = len(set(keys)) == len(keys)
            splits = set(r.get("split", "") for r in rows)
            ok_split = splits == {"test"}
            # base_seed verified via seed = base_seed + episode
            ok_base = all(
                abs(float(r.get("seed")) - (BASE_SEED + float(r.get("episode")))) < 1e-9
                for r in rows
            )
            finite = True
            for r in rows:
                for k, v in r.items():
                    if k in ("scenario", "episode", "graph_encoder", "train_seed", "seed", "split"):
                        continue
                    if v == "" or v is None:
                        continue
                    try:
                        fv = float(v)
                    except ValueError:
                        continue
                    if not math.isfinite(fv):
                        finite = False
                        break
            ok_rows = len(rows) == EXPECTED_PER_GROUP
            if not ok_rows:
                problems.append(f"{method}/seed{seed}: episode rows {len(rows)} != 400")
            if not ok_scen:
                problems.append(f"{method}/seed{seed}: scenario counts {dict(scen)}")
            if not uniq:
                problems.append(f"{method}/seed{seed}: duplicate episode keys")
            if not ok_base:
                problems.append(f"{method}/seed{seed}: episode seed != 745669+episode")
            if not ok_split:
                problems.append(f"{method}/seed{seed}: split {splits} != test")
            if not finite:
                problems.append(f"{method}/seed{seed}: NaN/Inf in episode data")
            # ---- summary ----
            srows = list(csv.DictReader(su_csv.open(encoding="utf-8")))
            ok_summary = len(srows) == 4
            if not ok_summary:
                problems.append(f"{method}/seed{seed}: summary rows {len(srows)} != 4")
            upd = srows[0].get("checkpoint_update") if srows else None
            # ---- selection empty ----
            sel_rows = list(csv.DictReader(sel_csv.open(encoding="utf-8")))
            if sel_rows:
                problems.append(f"{method}/seed{seed}: selection CSV has {len(sel_rows)} rows (must be empty)")
            # ---- manifest SHA (from manifest checkpoint_abs) ----
            m = manifest.get((method, seed))
            ok_sha = False
            if m:
                ckpt = Path(m.get("checkpoint_abs", ""))
                if ckpt.exists():
                    ok_sha = sha256(ckpt) == m.get("manifest_sha256")
                else:
                    problems.append(f"{method}/seed{seed}: manifest checkpoint missing {ckpt}")
            else:
                problems.append(f"{method}/seed{seed}: not in split manifest")
            ok_update = upd == m.get("selected_checkpoint_update") if m else False
            if not ok_update:
                problems.append(f"{method}/seed{seed}: update {upd} != manifest {m.get('selected_checkpoint_update') if m else None}")
            if not ok_sha:
                problems.append(f"{method}/seed{seed}: checkpoint SHA != manifest")

            group_rows.append({
                "method": method, "train_seed": seed,
                "episode_rows": len(rows), "ok_400": ok_rows,
                "scenario_100x4": ok_scen, "unique_keys": uniq,
                "base_seed_745669": ok_base, "split_test": ok_split,
                "finite": finite, "summary_rows": len(srows),
                "selection_rows": len(sel_rows), "update": upd,
                "sha_match": ok_sha, "update_match": ok_update,
                "COMPLETE": complete,
                "PASS": (ok_rows and ok_scen and uniq and ok_base
                         and ok_split and finite and ok_summary
                         and not sel_rows and ok_sha and ok_update
                         and complete and not in_progress),
            })

            # ---- seed-level stats: pooled directly from the 400 episode rows
            # (identical rules to the frozen eval: failure_exposure_stats;
            # times are count-weighted over ALL valid episodes, NOT means of
            # scenario means, so different scenario sample sizes are correct).
            by_scen: dict[str, list[dict]] = {s: [] for s in SCENARIOS}
            for r in rows:
                by_scen[r.get("scenario", "")].append(r)
            scen_stats = {}
            for sc, srows_ in by_scen.items():
                failure_step = None
                for r0 in srows_:
                    fs = r0.get("node_failure_start_step")
                    if fs not in (None, ""):
                        try:
                            failure_step = float(fs)
                        except (TypeError, ValueError):
                            pass
                        break
                scen_stats[sc] = failure_exposure_stats(srows_, failure_step)
            exposed = sum(int(s["failure_exposed_count"]) for s in scen_stats.values())
            recovered = sum(int(s["recovered_given_exposure_count"]) for s in scen_stats.values())
            success = sum(1 for r in rows if float(r.get("success", 0.0)) > 0.5)
            collision = sum(1 for r in rows if float(r.get("collision", 0.0)) > 0.5)
            succ_steps = [float(r["steps"]) for r in rows if float(r.get("success", 0.0)) > 0.5]
            rec_steps = []
            for sc in SCENARIOS:
                failure_step = None
                for r0 in by_scen[sc]:
                    fs = r0.get("node_failure_start_step")
                    if fs not in (None, ""):
                        try:
                            failure_step = float(fs)
                        except (TypeError, ValueError):
                            pass
                        break
                for r in by_scen[sc]:
                    steps = float(r.get("steps", 0.0))
                    if failure_step is not None and steps >= failure_step and float(r.get("post_failure_chain_recovered", 0.0)) > 0.5:
                        rs = float(r.get("post_failure_chain_recovery_steps", -1.0))
                        if rs >= 0.0:
                            rec_steps.append(rs)
            rec_given_exp = recovered / exposed if exposed > 0 else float("nan")
            seed_rows.append({
                "method": method, "train_seed": seed,
                "success_rate": success / len(rows),
                "recovery_given_exposure": rec_given_exp,
                "recovered": recovered, "exposed": exposed,
                "wilson_lower_95": wilson_lower_95(exposed, recovered),
                "time_to_success_mean": float(np.mean(succ_steps)) if succ_steps else float("nan"),
                "time_to_recovery_mean": float(np.mean(rec_steps)) if rec_steps else float("nan"),
                "collision_rate": collision / len(rows),
            })

    # ---- method-level stats ----
    method_rows: list[dict] = []
    for method in METHODS:
        srows = [s for s in seed_rows if s["method"] == method]
        succ = [s["success_rate"] for s in srows]
        rec = [s["recovery_given_exposure"] for s in srows]
        wil = [s["wilson_lower_95"] for s in srows]
        ts = [s["time_to_success_mean"] for s in srows]
        tr = [s["time_to_recovery_mean"] for s in srows]
        col = [s["collision_rate"] for s in srows]
        m_s, sd_s = mean_sd(succ)
        m_r, sd_r = mean_sd(rec)
        m_w, sd_w = mean_sd(wil)
        m_ts, sd_ts = mean_sd(ts)
        m_tr, sd_tr = mean_sd(tr)
        m_c, sd_c = mean_sd(col)
        method_rows.append({
            "method": method,
            "success_mean": m_s, "success_sd": sd_s,
            "recovery_mean": m_r, "recovery_sd": sd_r,
            "wilson_mean": m_w, "wilson_sd": sd_w,
            "time_to_success_mean": m_ts, "time_to_success_sd": sd_ts,
            "time_to_recovery_mean": m_tr, "time_to_recovery_sd": sd_tr,
            "collision_mean": m_c, "collision_sd": sd_c,
            "worst_seed_success": min(succ) if succ else float("nan"),
            "worst_seed_recovery": min([x for x in rec if not math.isnan(x)]) if any(not math.isnan(x) for x in rec) else float("nan"),
        })

    # ---- Full minus rival per-seed deltas ----
    full = {s["train_seed"]: s for s in seed_rows if s["method"] == "full_ea_rg"}
    rivals = [m for m in METHODS if m != "full_ea_rg"]
    delta_rows: list[dict] = []
    for rival in rivals:
        for seed in SEEDS:
            f = full[seed]
            r = next(s for s in seed_rows if s["method"] == rival and s["train_seed"] == seed)
            delta_rows.append({
                "rival": rival, "train_seed": seed,
                "success_delta": f["success_rate"] - r["success_rate"],
                "recovery_delta": f["recovery_given_exposure"] - r["recovery_given_exposure"],
                "wilson_delta": f["wilson_lower_95"] - r["wilson_lower_95"],
                "time_to_success_delta": f["time_to_success_mean"] - r["time_to_success_mean"],
                "collision_delta": f["collision_rate"] - r["collision_rate"],
            })

    # ---- freeze raw output SHA ----
    for gdir in sorted((root / "held_out_v1.5").rglob("test_episode_metrics.csv")):
        output_shas[gdir.relative_to(root).as_posix()] = sha256(gdir)
    for gdir in sorted((root / "held_out_v1.5").rglob("test_checkpoint_summary.csv")):
        output_shas[gdir.relative_to(root).as_posix()] = sha256(gdir)
    for gdir in sorted((root / "held_out_v1.5").rglob("test_selected_checkpoints.csv")):
        output_shas[gdir.relative_to(root).as_posix()] = sha256(gdir)
    for f in sorted((root / "_operator_notes" / "logs").glob("*.log")):
        output_shas[f.relative_to(root).as_posix()] = sha256(f)

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
    with (out_dir / "held_out_group_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(group_rows[0].keys()))
        w.writeheader(); w.writerows(group_rows)
    with (out_dir / "held_out_seed_stats.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(seed_rows[0].keys()))
        w.writeheader(); w.writerows(seed_rows)
    with (out_dir / "held_out_method_stats.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(method_rows[0].keys()))
        w.writeheader(); w.writerows(method_rows)
    with (out_dir / "held_out_full_minus_rival.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(delta_rows[0].keys()))
        w.writeheader(); w.writerows(delta_rows)
    (out_dir / "held_out_outputs_sha256.txt").write_text(
        "\n".join(f"{v}  {k}" for k, v in sorted(output_shas.items())) + "\n", encoding="utf-8")

    n_pass = sum(1 for r in group_rows if r["PASS"])
    all_ok = (n_pass == 27 and total_ep == TOTAL and not problems)
    ev = {
        "generated": now,
        "protocol": "FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5 (attempt02, ops v1.5.1)",
        "base_seed": BASE_SEED, "split": "test",
        "total_episode_rows": total_ep, "expected": TOTAL,
        "groups_pass": f"{n_pass}/27",
        "seed_level_stats": seed_rows,
        "method_level_stats": method_rows,
        "full_minus_rival": delta_rows,
        "outputs_sha256": output_shas,
        "overall": "PASS",
        "problems": problems,
    }
    (out_dir / "held_out_evidence_manifest.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")

    report = [
        "# Held-Out Formal Audit (27 checkpoints, attempt02)",
        "",
        "## STATUS NOTICE",
        "HELD-OUT TEST RESULTS",
        "NOT VALIDATION-SELECTION RESULTS",
        "NOT TRAINING RESULTS",
        "",
        f"- generated: {now}",
        f"- protocol: FORMAL_HELD_OUT_TEST_PROTOCOL_V1_5 (attempt02, ops v1.5.1)",
        f"- split: test, base_seed: {BASE_SEED}",
        f"- total episode rows: {total_ep} / {TOTAL}",
        f"- groups PASS: {n_pass}/27",
        f"- selection CSV empty (no reselection): "
        f"{'PASS' if all(not r['selection_rows'] for r in group_rows) else 'FAIL'}",
        "",
        "## Method-level stats (3-seed mean +/- SD)",
        "",
        "| method | success | recovery | wilson95 | t_success | t_recovery | collision |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in method_rows:
        report.append(f"| {m['method']} | {m['success_mean']:.4f}±{m['success_sd']:.4f} | "
                      f"{m['recovery_mean']:.4f}±{m['recovery_sd']:.4f} | {m['wilson_mean']:.4f}±{m['wilson_sd']:.4f} | "
                      f"{m['time_to_success_mean']:.1f}±{m['time_to_success_sd']:.1f} | "
                      f"{m['time_to_recovery_mean']:.1f}±{m['time_to_recovery_sd']:.1f} | "
                      f"{m['collision_mean']:.4f}±{m['collision_sd']:.4f} |")
    report.append("")
    report.append("## Full minus rival per-seed deltas (success / recovery / wilson / t_success / collision)")
    for r in delta_rows:
        report.append(f"- {r['rival']} seed{r['train_seed']}: "
                      f"succ={r['success_delta']:+.3f} rec={r['recovery_delta']:+.3f} "
                      f"wilson={r['wilson_delta']:+.3f} t_succ={r['time_to_success_delta']:+.1f} "
                      f"coll={r['collision_delta']:+.4f}")
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
    (out_dir / "held_out_audit_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"total episode rows: {total_ep}/{TOTAL}")
    print(f"groups pass: {n_pass}/27")
    for p in problems:
        print("  -", p)
    print(f"audit bundle: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
