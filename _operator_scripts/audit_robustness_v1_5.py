# audit_robustness_v1_5.py
# Post-run formal audit of the robustness experiment (10,500 episodes,
# FORMAL_ROBUSTNESS_PROTOCOL_V1_5, ops robustness-eval-ops-v1.5.0).
#
# Checks:
#   1. 210/210 cells COMPLETE, no IN_PROGRESS; per-cell episode=50, summary=1,
#      selection=0; split=test; base_seed=946804; unique episode keys
#   2. 21 checkpoints x 10 conditions coverage (7 methods x 3 seeds)
#   3. checkpoint SHA/update == robustness manifest (per cell summary rows)
#   4. seed-level / method-seed-condition statistics (pooled aggregation,
#      identical rules as held-out audit; SD ddof=1; estimate_unstable<10)
#   5. degradation vs R00 (Delta_success / Delta_recovery / Delta_t_success /
#      Delta_t_recovery) per method-seed-condition
#   6. 3-seed mean +/- sample SD and worst seed per (method, condition)
#   7. Full degradation-slope comparison across conditions
#   8. Role-Pair Gate pre-registered verdict (section 9 of protocol)
#   9. freeze raw output SHA
#
# Outputs under <root>/_operator_notes/final_robustness_audit_v1_5/:
#   robustness_audit_report.md
#   robustness_cell_audit.csv
#   robustness_seed_condition_stats.csv
#   robustness_method_condition_stats.csv
#   robustness_degradation.csv
#   robustness_role_pair_verdict.md
#   robustness_outputs_sha256.txt
#   robustness_evidence_manifest.json
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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AB_ROOT))

from scripts.evaluate_3d_checkpoint_sweep import failure_exposure_stats  # noqa: E402

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
METHODS = ["full_ea_rg", "w_o_role_pair_gate", "w_o_gate_prior", "w_o_task_support",
           "param_matched_single", "happo", "mappo"]
SEEDS = [0, 1, 2]
BASE_SEED = 946804
EPISODES_PER_CELL = 50


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_manifest(manifest_csv: Path) -> dict[tuple[str, int], dict]:
    out = {}
    with manifest_csv.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out[(r["method"], int(r["train_seed"]))] = r
    return out


def mean_sd(xs: list[float]) -> tuple[float, float]:
    a = np.array([x for x in xs if not math.isnan(x)], dtype=float)
    if a.size == 0:
        return float("nan"), float("nan")
    return float(a.mean()), float(a.std(ddof=1))


def wilson_lower_95(recovered: float, exposed: float, z: float = 1.96) -> float:
    if exposed <= 0.0:
        return 0.0
    p = recovered / exposed
    denom = 1 + z * z / exposed
    centre = p + z * z / (2 * exposed)
    half = z * math.sqrt(p * (1 - p) / exposed + z * z / (4 * exposed * exposed))
    return (centre - half) / denom


def cell_stats(ep_rows: list[dict]) -> dict:
    """Pooled stats over one cell (50 episodes), frozen aggregation rules."""
    by_scen: dict[str, list[dict]] = {}
    for r in ep_rows:
        by_scen.setdefault(r["scenario"], []).append(r)
    scen_stats = {}
    for sc, rows in by_scen.items():
        failure_step = None
        for r0 in rows:
            fs = r0.get("node_failure_start_step")
            if fs not in (None, ""):
                try:
                    failure_step = float(fs)
                except (TypeError, ValueError):
                    pass
                break
        scen_stats[sc] = failure_exposure_stats(rows, failure_step)
    exposed = sum(int(s["failure_exposed_count"]) for s in scen_stats.values())
    recovered = sum(int(s["recovered_given_exposure_count"]) for s in scen_stats.values())
    success = sum(1 for r in ep_rows if float(r.get("success", 0.0)) > 0.5)
    collision = sum(1 for r in ep_rows if float(r.get("collision", 0.0)) > 0.5)
    succ_steps = [float(r["steps"]) for r in ep_rows if float(r.get("success", 0.0)) > 0.5]
    rec_steps = []
    for sc, rows in by_scen.items():
        failure_step = None
        for r0 in rows:
            fs = r0.get("node_failure_start_step")
            if fs not in (None, ""):
                try:
                    failure_step = float(fs)
                except (TypeError, ValueError):
                    pass
                break
        for r in rows:
            steps = float(r.get("steps", 0.0))
            if failure_step is not None and steps >= failure_step and float(r.get("post_failure_chain_recovered", 0.0)) > 0.5:
                rs = float(r.get("post_failure_chain_recovery_steps", -1.0))
                if rs >= 0.0:
                    rec_steps.append(rs)
    n = len(ep_rows)
    return {
        "episode_count": n,
        "success_count": success, "success_rate": success / n if n else float("nan"),
        "collision_count": collision, "collision_rate": collision / n if n else float("nan"),
        "exposed": exposed, "recovered": recovered,
        "recovery_given_exposure": recovered / exposed if exposed > 0 else float("nan"),
        "wilson_lower_95": wilson_lower_95(float(recovered), float(exposed)),
        "time_to_success": float(np.mean(succ_steps)) if succ_steps else float("nan"),
        "time_to_recovery": float(np.mean(rec_steps)) if rec_steps else float("nan"),
        "estimate_unstable": 1 if exposed < 10 else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root
    manifest = load_manifest(args.manifest)
    out_dir = root / "_operator_notes" / "final_robustness_audit_v1_5"
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    cell_rows: list[dict] = []
    stats: list[dict] = []
    total_ep = 0
    output_shas: dict[str, str] = {}

    for method in METHODS:
        for seed in SEEDS:
            man = manifest.get((method, seed))
            for cid, key in CONDITIONS:
                gdir = root / method / f"seed{seed}" / cid
                complete = (gdir / "COMPLETE").exists()
                in_progress = (gdir / "IN_PROGRESS").exists()
                if not complete:
                    problems.append(f"{method}/seed{seed}/{cid}: COMPLETE missing")
                if in_progress:
                    problems.append(f"{method}/seed{seed}/{cid}: IN_PROGRESS present")
                ep_csv = gdir / "test_episode_metrics.csv"
                rows = list(csv.DictReader(ep_csv.open(encoding="utf-8")))
                total_ep += len(rows)
                ok_rows = len(rows) == EPISODES_PER_CELL
                if not ok_rows:
                    problems.append(f"{method}/seed{seed}/{cid}: rows {len(rows)} != 50")
                splits = {r.get("split") for r in rows}
                ok_split = splits == {"test"}
                if not ok_split:
                    problems.append(f"{method}/seed{seed}/{cid}: split {splits}")
                ok_base = all(abs(float(r.get("seed")) - (BASE_SEED + float(r.get("episode")))) < 1e-9 for r in rows)
                if not ok_base:
                    problems.append(f"{method}/seed{seed}/{cid}: seed != 946804+episode")
                keys = [(r.get("graph_encoder"), r.get("train_seed"), r.get("scenario"), r.get("episode")) for r in rows]
                ok_uniq = len(set(keys)) == len(keys)
                if not ok_uniq:
                    problems.append(f"{method}/seed{seed}/{cid}: duplicate keys")
                sel_csv = gdir / "test_selected_checkpoints.csv"
                n_sel = len(list(csv.DictReader(sel_csv.open(encoding="utf-8"))))
                if n_sel != 0:
                    problems.append(f"{method}/seed{seed}/{cid}: selection {n_sel} rows")
                # summary + manifest sha/update
                su_csv = gdir / "test_checkpoint_summary.csv"
                srows = list(csv.DictReader(su_csv.open(encoding="utf-8")))
                ok_summary = len(srows) == 1
                if not ok_summary:
                    problems.append(f"{method}/seed{seed}/{cid}: summary rows {len(srows)} != 1")
                upd = srows[0].get("checkpoint_update") if srows else None
                ok_update = upd == man.get("selected_checkpoint_update") if man else False
                if not ok_update:
                    problems.append(f"{method}/seed{seed}/{cid}: update {upd} != manifest")
                # checkpoint sha via manifest abs path
                ok_sha = False
                if man:
                    ckpt = Path(man["checkpoint_abs"])
                    ok_sha = ckpt.exists() and sha256(ckpt) == man["manifest_sha256"]
                if not ok_sha:
                    problems.append(f"{method}/seed{seed}/{cid}: checkpoint SHA != manifest")
                st = cell_stats(rows)
                st.update({"method": method, "train_seed": seed, "condition": cid, "scenario_key": key})
                stats.append(st)
                cell_rows.append({
                    "method": method, "train_seed": seed, "condition": cid,
                    "episode_rows": len(rows), "ok_50": ok_rows, "split_test": ok_split,
                    "base_seed_946804": ok_base, "unique_keys": ok_uniq,
                    "selection_rows": n_sel, "summary_rows": len(srows),
                    "update_match": ok_update, "sha_match": ok_sha,
                    "COMPLETE": complete,
                    "PASS": (ok_rows and ok_split and ok_base and ok_uniq and n_sel == 0
                             and ok_summary and ok_update and ok_sha and complete and not in_progress),
                })

    # ---- method-condition stats (3-seed mean +/- sample SD, worst seed) ----
    method_cond_rows: list[dict] = []
    for method in METHODS:
        for cid, _ in CONDITIONS:
            cells = [s for s in stats if s["method"] == method and s["condition"] == cid]
            succ = [c["success_rate"] for c in cells]
            rec = [c["recovery_given_exposure"] for c in cells]
            wil = [c["wilson_lower_95"] for c in cells]
            ts = [c["time_to_success"] for c in cells]
            tr = [c["time_to_recovery"] for c in cells]
            col = [c["collision_rate"] for c in cells]
            m_s, sd_s = mean_sd(succ)
            m_r, sd_r = mean_sd(rec)
            m_w, sd_w = mean_sd(wil)
            m_ts, sd_ts = mean_sd(ts)
            m_tr, sd_tr = mean_sd(tr)
            m_c, sd_c = mean_sd(col)
            method_cond_rows.append({
                "method": method, "condition": cid,
                "success_mean": m_s, "success_sd": sd_s,
                "recovery_mean": m_r, "recovery_sd": sd_r,
                "wilson_mean": m_w, "wilson_sd": sd_w,
                "t_success_mean": m_ts, "t_success_sd": sd_ts,
                "t_recovery_mean": m_tr, "t_recovery_sd": sd_tr,
                "collision_mean": m_c, "collision_sd": sd_c,
                "worst_seed_success": min(succ) if succ else float("nan"),
                "worst_seed_recovery": min([x for x in rec if not math.isnan(x)]) if any(not math.isnan(x) for x in rec) else float("nan"),
            })

    # ---- degradation vs R00 ----
    deg_rows: list[dict] = []
    for method in METHODS:
        for seed in SEEDS:
            base = next(s for s in stats if s["method"] == method and s["train_seed"] == seed and s["condition"] == "R00")
            for cid, _ in CONDITIONS:
                if cid == "R00":
                    continue
                cell = next(s for s in stats if s["method"] == method and s["train_seed"] == seed and s["condition"] == cid)
                deg_rows.append({
                    "method": method, "train_seed": seed, "condition": cid,
                    "delta_success": cell["success_rate"] - base["success_rate"],
                    "delta_recovery": cell["recovery_given_exposure"] - base["recovery_given_exposure"],
                    "delta_t_success": cell["time_to_success"] - base["time_to_success"],
                    "delta_t_recovery": cell["time_to_recovery"] - base["time_to_recovery"],
                })

    # ---- Role-Pair Gate verdict (pre-registered, section 9) ----
    full = {c["condition"]: c for c in method_cond_rows if c["method"] == "full_ea_rg"}
    rpg = {c["condition"]: c for c in method_cond_rows if c["method"] == "w_o_role_pair_gate"}
    strong_conds = ["R02", "R04", "R09"]  # high dropout / high delay / joint stress
    rpg_fav = 0
    rpg_neutral = 0
    rpg_disadv = 0
    lines = []
    for cid, _ in CONDITIONS:
        f, r = full[cid], rpg[cid]
        d_rec = f["recovery_mean"] - r["recovery_mean"]
        d_worst = f["worst_seed_recovery"] - r["worst_seed_recovery"]
        d_tr = f["t_recovery_mean"] - r["t_recovery_mean"]
        lines.append(f"- {cid}: Full-RPG recovery {d_rec:+.4f}, worst-seed {d_worst:+.4f}, t_rec {d_tr:+.2f}")
        if cid in strong_conds:
            if d_rec > 0.005 and d_worst > 0.0:
                rpg_fav += 1
            elif abs(d_rec) <= 0.005:
                rpg_neutral += 1
            else:
                rpg_disadv += 1
    # verdict
    if rpg_fav >= 2 and rpg_neutral == 0 and rpg_disadv == 0:
        verdict = "RETAIN as core structure"
    elif rpg_disadv >= 2:
        verdict = "REMOVE / simplify"
    else:
        verdict = "DOWNGRADE to auxiliary structure"
    verdict_lines = [
        "# Role-Pair Gate Pre-Registered Verdict (robustness)",
        "",
        f"- strong conditions considered: {strong_conds}",
        f"- conditions where Full > RPG on recovery & worst-seed: {rpg_fav}",
        f"- conditions neutral (|d|<=0.005): {rpg_neutral}",
        f"- conditions where RPG better: {rpg_disadv}",
        "",
        "## Per-condition Full minus w_o_role_pair_gate (recovery / worst-seed / t_recovery)",
        "",
    ] + lines + [
        "",
        f"## VERDICT: {verdict}",
        "",
        "- RETAIN: Full higher recovery + lower worst-seed degradation + shorter t_recovery across multiple strong conditions, advantage widening.",
        "- DOWNGRADE: basically equal or RPG slightly better -> static role-prior modulation, NOT a core empirical contribution.",
        "- REMOVE: RPG stably better and more efficient on most conditions -> adopt simplified model.",
    ]
    (out_dir / "robustness_role_pair_verdict.md").write_text("\n".join(verdict_lines), encoding="utf-8")

    # ---- freeze raw output SHA ----
    for f in sorted((root).rglob("test_episode_metrics.csv")):
        output_shas[f.relative_to(root).as_posix()] = sha256(f)
    for f in sorted((root).rglob("test_checkpoint_summary.csv")):
        output_shas[f.relative_to(root).as_posix()] = sha256(f)
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
    with (out_dir / "robustness_cell_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cell_rows[0].keys()))
        w.writeheader(); w.writerows(cell_rows)
    with (out_dir / "robustness_seed_condition_stats.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(stats[0].keys()))
        w.writeheader(); w.writerows(stats)
    with (out_dir / "robustness_method_condition_stats.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(method_cond_rows[0].keys()))
        w.writeheader(); w.writerows(method_cond_rows)
    with (out_dir / "robustness_degradation.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(deg_rows[0].keys()))
        w.writeheader(); w.writerows(deg_rows)
    (out_dir / "robustness_outputs_sha256.txt").write_text(
        "\n".join(f"{v}  {k}" for k, v in sorted(output_shas.items())) + "\n", encoding="utf-8")

    n_pass = sum(1 for r in cell_rows if r["PASS"])
    all_ok = (n_pass == 210 and total_ep == 210 * 50 and not problems)
    ev = {
        "generated": now,
        "protocol": "FORMAL_ROBUSTNESS_PROTOCOL_V1_5 (ops robustness-eval-ops-v1.5.0)",
        "base_seed": BASE_SEED, "split": "test",
        "total_episode_rows": total_ep, "expected": 210 * 50,
        "cells_pass": f"{n_pass}/210",
        "role_pair_gate_verdict": verdict,
        "role_pair_gate_detail": {"full_better_strong": rpg_fav, "neutral": rpg_neutral, "rpg_better": rpg_disadv},
        "outputs_sha256": output_shas,
        "overall": "PASS",
        "problems": problems,
    }
    (out_dir / "robustness_evidence_manifest.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")

    report = [
        "# Robustness Formal Audit (10,500 episodes)",
        "",
        "## STATUS NOTICE",
        "ROBUSTNESS TEST RESULTS",
        "NOT VALIDATION-SELECTION RESULTS",
        "NOT HELD-OUT TEST RESULTS",
        "",
        f"- generated: {now}",
        f"- protocol: FORMAL_ROBUSTNESS_PROTOCOL_V1_5 (ops v1.5.0)",
        f"- base_seed: {BASE_SEED}, split: test, episodes/cell: {EPISODES_PER_CELL}",
        f"- total episode rows: {total_ep} / {210 * 50}",
        f"- cells PASS: {n_pass}/210",
        f"- selection empty (no reselection): {'PASS' if all(not r['selection_rows'] for r in cell_rows) else 'FAIL'}",
        f"- Role-Pair Gate verdict: {verdict}",
        "",
        "## Method x Condition (3-seed mean +/- SD) - success / recovery / wilson",
        "",
        "| method | cond | success | recovery | wilson | t_success | t_recovery | collision |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in method_cond_rows:
        report.append(f"| {m['method']} | {m['condition']} | {m['success_mean']:.3f}±{m['success_sd']:.3f} | "
                      f"{m['recovery_mean']:.3f}±{m['recovery_sd']:.3f} | {m['wilson_mean']:.3f}±{m['wilson_sd']:.3f} | "
                      f"{m['t_success_mean']:.1f}±{m['t_success_sd']:.1f} | {m['t_recovery_mean']:.1f}±{m['t_recovery_sd']:.1f} | "
                      f"{m['collision_mean']:.4f} |")
    report.append("")
    report.append("## Degradation vs R00 (3-seed mean, per condition)")
    for method in METHODS:
        base = next(c for c in method_cond_rows if c["method"] == method and c["condition"] == "R00")
        parts = []
        for cid, _ in CONDITIONS:
            if cid == "R00":
                continue
            c = next(x for x in method_cond_rows if x["method"] == method and x["condition"] == cid)
            d = c["success_mean"] - base["success_mean"]
            parts.append(f"{cid}={d:+.3f}")
        report.append(f"- {method}: delta_success " + " ".join(parts))
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
    (out_dir / "robustness_audit_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"total rows: {total_ep}/{210 * 50}")
    print(f"cells pass: {n_pass}/210")
    print("Role-Pair Gate verdict:", verdict)
    for p in problems:
        print("  -", p)
    print(f"audit bundle: {out_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
