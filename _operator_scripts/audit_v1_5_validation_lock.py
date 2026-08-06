# audit_v1_5_validation_lock.py
# READ-ONLY final audit + immutable lock of the 24 v1.5 validation selections.
#   VALIDATION DATA - USED FOR CHECKPOINT SELECTION, NOT HELD-OUT TEST RESULTS
# Produces assets under _operator_notes/final_validation_audit_v1_5/.
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(r"D:\Code\Codex\ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))
VROOT = ROOT / "results" / "paper_config_runs" / "formal_ablation_v1.5_validation_selector_v1.5.1_20260805"
OUT = VROOT / "_operator_notes" / "final_validation_audit_v1_5"
MANIFEST = VROOT / "_operator_notes" / "v1.5_validation_checkpoints_sha256.csv"
METHODS = ["full_ea_rg", "w_o_gate_prior", "w_o_task_support", "w_o_role_pair_gate",
           "no_graph", "single_graph", "param_matched_single", "happo"]
SCENARIOS = ["dropout030_delay2_relay_failure_early", "dropout030_delay2_relay_failure",
             "dropout030_delay2_relay_failure_delayed", "dropout030_delay2_relay_failure_late"]
ELIGIBLE = [100, 200, 300, 400, 500, 600, 700, 800, 900, 977]
EVAL_TAG = "formal-ablation-eval-ops-v1.5.0"
EVAL_COMMIT = "9e48fe7"
BASE_SEED = 641939
SELECTOR_DOC = "V1_5_CHECKPOINT_SELECTOR_ADJUDICATION.md"
SPLIT_DOC = "V1_5_VALIDATION_SPLIT_FREEZE.md"

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    aggregate_suite_rows,
    parse_score,
    select_checkpoints,
    wilson_lower_95,
)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def make_suite_args(scenarios: list[str]) -> argparse.Namespace:
    return SimpleNamespace(
        split="validation",
        scenarios=scenarios,
        selection_group="suite",
        selection_metric="legacy_recovery",
        selection_success_weight=100.0,
        max_selection_collision_rate=0.0,
        delayed_recovery_min_step=80,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        selection_policy="v1_5_wilson",
    )


def read_csv(p: Path) -> list[dict]:
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report: list[str] = []
    ok_all = True
    audit_rows: list[dict] = []
    recompute_rows: list[dict] = []
    sha_rows: list[dict] = []
    desc_rows: list[dict] = []

    report.append("# v1.5 Validation Lock Audit (24/24)")
    report.append("")
    report.append("```text")
    report.append("VALIDATION DATA - USED FOR CHECKPOINT SELECTION")
    report.append("NOT HELD-OUT TEST RESULTS")
    report.append("```")
    report.append("")
    report.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    report.append(f"eval tag: {EVAL_TAG} @ {EVAL_COMMIT}")
    report.append(f"validation base_seed: {BASE_SEED}")
    report.append(f"selection policy: v1_5_wilson")
    report.append(f"methods: {len(METHODS)} x 3 seeds = 24")
    report.append(f"candidate manifest: {MANIFEST.name} (240)")
    report.append("")

    # 240 manifest sha map
    man = {f"{r['method']}:{r['train_seed']}:{r['checkpoint_update']}": r["checkpoint_sha256"] for r in read_csv(MANIFEST)}

    # per method
    for m in METHODS:
        d = VROOT / m
        complete = (d / "COMPLETE").exists()
        report.append(f"## {m}: COMPLETE={complete}")
        ok_all &= complete
        if not complete:
            continue

        # selection csv
        sel = read_csv(d / "validation_selected_checkpoints.csv")
        sel_ok = len(sel) == 3
        report.append(f"- selection rows: {len(sel)} (expect 3) -> {'PASS' if sel_ok else 'FAIL'}")
        ok_all &= sel_ok

        # summary
        sm = read_csv(d / "validation_checkpoint_summary.csv")
        sm_ok = len(sm) == 120
        report.append(f"- summary rows: {len(sm)} (expect 120) -> {'PASS' if sm_ok else 'FAIL'}")
        ok_all &= sm_ok
        scen_set = set(r["scenario"] for r in sm)
        scen_ok = set(SCENARIOS) <= scen_set
        report.append(f"- scenarios covered: {len(scen_set)}/4 -> {'PASS' if scen_ok else 'FAIL'}")
        ok_all &= scen_ok
        upd_set = sorted({int(r["checkpoint_update"]) for r in sm if r["checkpoint_update"].isdigit()})
        upd_ok = upd_set == ELIGIBLE
        report.append(f"- updates covered: {len(upd_set)}/10 -> {'PASS' if upd_ok else 'FAIL'}")
        ok_all &= upd_ok

        # per-seed selection checks
        for r in sel:
            key = f"{m}:{r['train_seed']}:{r['selected_checkpoint_update']}"
            sha_ok = man.get(key) == r.get("checkpoint_sha256", "")
            exposed = int(r.get("failure_exposed_count", "0") or 0)
            rec = int(r.get("recovered_given_exposure_count", "0") or 0)
            unstable = r.get("estimate_unstable", "")
            unstable_ok = (unstable == "1") if exposed < 10 else (unstable == "0")
            coll_ok = float(r.get("collision_mean", "1") or 1) <= 0.0
            policy_ok = r.get("selection_policy", "") == "v1_5_wilson"
            upd_member = int(r["selected_checkpoint_update"]) in ELIGIBLE
            line = (f"- seed{r['train_seed']} upd={r['selected_checkpoint_update']} "
                    f"exp={exposed} rec={rec} wilson={r.get('wilson_lower_95','')} "
                    f"policy={r.get('selection_policy','')} coll={r.get('collision_mean','')} "
                    f"unstable={unstable}({'OK' if unstable_ok else 'BAD'}) "
                    f"sha={'OK' if sha_ok else 'BAD'} upd_ok={upd_member}")
            report.append(line)
            row_ok = exposed > 0 and unstable_ok and coll_ok and policy_ok and upd_member and sha_ok
            ok_all &= row_ok
            audit_rows.append({
                "method": m, "train_seed": r["train_seed"], "selected_checkpoint_update": r["selected_checkpoint_update"],
                "selected_checkpoint": r.get("selected_checkpoint", ""), "checkpoint_sha256": r.get("checkpoint_sha256", ""),
                "failure_exposed_count": exposed, "recovered_given_exposure_count": rec,
                "recovery_given_exposure": r.get("recovery_given_exposure", ""),
                "wilson_lower_95": r.get("wilson_lower_95", ""), "estimate_unstable": unstable,
                "collision_mean": r.get("collision_mean", ""), "success_mean": r.get("success_mean", ""),
                "time_to_recovery_given_exposure": r.get("time_to_recovery_given_exposure", ""),
                "time_to_success": r.get("time_to_success", ""), "selection_policy": r.get("selection_policy", ""),
                "audit_status": "PASS" if row_ok else "FAIL",
            })
            desc_rows.append({
                "method": m, "train_seed": r["train_seed"], "checkpoint_update": r["selected_checkpoint_update"],
                "recovery_given_exposure": r.get("recovery_given_exposure", ""),
                "wilson_lower_95": r.get("wilson_lower_95", ""),
                "success_mean": r.get("success_mean", ""),
                "time_to_success": r.get("time_to_success", ""),
            })

        # selector recompute from summary (aggregate suite + v1_5_wilson select)
        args = make_suite_args(SCENARIOS)
        suite = aggregate_suite_rows(args, sm)
        recomputed = select_checkpoints(args, sm)
        rec_map = {f"{x['train_seed']}": x["selected_checkpoint_update"] for x in recomputed}
        for r in sel:
            seed = r["train_seed"]
            same = rec_map.get(seed) == r["selected_checkpoint_update"]
            ok_all &= same
            report.append(f"- RECOMPUTE seed{seed}: selected={rec_map.get(seed)} csv={r['selected_checkpoint_update']} -> {'PASS' if same else 'FAIL'}")
            recompute_rows.append({"method": m, "train_seed": seed, "csv_update": r["selected_checkpoint_update"],
                                   "recomputed_update": rec_map.get(seed), "match": same})

    # 240 candidate sha audit (from summary csv checkpoint paths)
    cand_rows: list[dict] = []
    cand_ok = True
    for m in METHODS:
        d = VROOT / m
        sm = read_csv(d / "validation_checkpoint_summary.csv")
        seen: set[tuple] = set()
        for r in sm:
            upd = int(r["checkpoint_update"])
            seed = r["train_seed"]
            if (seed, upd) in seen:
                continue
            seen.add((seed, upd))
            cp = ROOT / r["checkpoint"]
            if not cp.exists():
                cand_ok = False
                cand_rows.append({"method": m, "train_seed": seed, "checkpoint_update": upd, "checkpoint": r["checkpoint"], "sha_ok": False, "note": "MISSING"})
                continue
            s = sha256(cp)
            msha = man.get(f"{m}:{seed}:{upd}", "")
            sha_ok = s == msha
            cand_ok &= sha_ok
            cand_rows.append({"method": m, "train_seed": seed, "checkpoint_update": upd,
                              "checkpoint": r["checkpoint"], "current_sha256": s, "manifest_sha256": msha, "sha_ok": sha_ok})
    report.append(f"\n## Candidate SHA audit: {len(cand_rows)} unique (expect 240) -> {'PASS' if len(cand_rows) == 240 and cand_ok else 'FAIL'}")
    ok_all &= len(cand_rows) == 240 and cand_ok

    # raw output sha (frozen evidence)
    for m in METHODS:
        for name in ("validation_episode_metrics.csv", "validation_checkpoint_summary.csv", "validation_selected_checkpoints.csv"):
            p = VROOT / m / name
            if p.exists():
                sha_rows.append({"file": f"{m}/{name}", "sha256": sha256(p)})
    latest_summary = sorted((VROOT / "_operator_notes" / "logs").glob("v15_validation_summary_*.txt"), key=lambda p: p.stat().st_mtime)[-1]
    sha_rows.append({"file": f"_operator_notes/logs/{latest_summary.name}", "sha256": sha256(latest_summary)})
    sha_rows.append({"file": "_operator_notes/v1.5_validation_checkpoints_sha256.csv", "sha256": sha256(MANIFEST)})
    for doc in (SELECTOR_DOC, SPLIT_DOC):
        p = ROOT / "docs" / doc
        if p.exists():
            sha_rows.append({"file": f"docs/{doc}", "sha256": sha256(p)})

    report.append(f"\n## FINAL: {'PASS' if ok_all else 'FAIL'}")

    # write assets
    def wcsv(name: str, rows: list[dict], fieldnames: list[str]) -> None:
        with (OUT / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

    (OUT / "validation_audit_report.md").write_text("\n".join(report), encoding="utf-8")
    wcsv("selected_checkpoints_24.csv", audit_rows, list(audit_rows[0].keys()) if audit_rows else [])
    wcsv("candidate_sha_audit_240.csv", cand_rows, list(cand_rows[0].keys()) if cand_rows else [])
    wcsv("selector_recompute_audit.csv", recompute_rows, list(recompute_rows[0].keys()) if recompute_rows else [])
    wcsv("validation_results_descriptive.csv", desc_rows, list(desc_rows[0].keys()) if desc_rows else [])
    (OUT / "validation_output_sha256.txt").write_text("\n".join(f"{r['file']}  {r['sha256']}" for r in sha_rows) + "\n", encoding="utf-8")

    manifest_json = {
        "title": "v1.5 validation 24-checkpoint immutable lock",
        "eval_tag": EVAL_TAG, "eval_commit": EVAL_COMMIT, "base_seed": BASE_SEED,
        "selection_policy": "v1_5_wilson", "methods": METHODS, "scenarios": SCENARIOS,
        "eligible_updates": ELIGIBLE, "audit_pass": bool(ok_all),
        "generated": datetime.now().isoformat(timespec="seconds"),
        "assets": {n: sha256(OUT / n) for n in
                   ["validation_audit_report.md", "selected_checkpoints_24.csv", "candidate_sha_audit_240.csv",
                    "selector_recompute_audit.csv", "validation_results_descriptive.csv", "validation_output_sha256.txt"]},
    }
    (OUT / "selected_checkpoints_24_manifest.json").write_text(json.dumps(manifest_json, indent=2), encoding="utf-8")
    (OUT / "evidence_manifest.json").write_text(json.dumps({
        "raw_output_sha256": sha_rows, "audit_assets_sha256": manifest_json["assets"],
        "audit_pass": bool(ok_all),
    }, indent=2), encoding="utf-8")

    print(f"FINAL: {'PASS' if ok_all else 'FAIL'}")
    print(f"assets written to {OUT}")


if __name__ == "__main__":
    main()
