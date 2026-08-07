# run_robustness_smoke_v1_5.py
# Phase-2 smoke: real-environment validation of the three robustness chains
# (sweep / happo / mappo) on the joint-stress condition R09, with 2 episodes,
# a deterministic throwaway smoke base seed, and full runtime-value capture.
#
# Frozen inputs:
#   protocol commit   robustness-protocol-freeze-v1.5.0 @ 3b99a7c
#   manifest          docs/robustness_v1_5_assets/robustness_checkpoint_manifest.csv
#   condition         R09 dropout070_delay8_relay_failure_early
#   smoke base seed   derived: SHA256("3b99a7c" + "robustness-smoke-v1.5") -> 344625
#   train seed        0 (same across the three chains)
#   episodes          2 (episode_index 0..1 -> seeds 344625, 344626)
#
# Output (smoke only, never the formal robustness output):
#   _smoke/robustness_v1_5/{sweep,happo,mappo}/...
#   _smoke/robustness_v1_5/smoke_audit/{robustness_smoke_audit.md,
#       robustness_smoke_manifest.json, robustness_smoke_outputs_sha256.txt,
#       robustness_import_identity.csv, robustness_summary_recompute.csv}
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

ROOT = Path(__file__).resolve().parents[1]
PYTHON = r"D:\Anaconda\envs\.conda\envs\cac\python.exe"
PROTOCOL_COMMIT = "3b99a7c"
ANCHOR = "robustness-smoke-v1.5"
RESERVED = {888000, 120000, 641939, 745669, 946804}
SMOKE_BASE_SEED = 344625
TRAIN_SEED = 0
EPISODES = 2
CONDITION = "dropout070_delay8_relay_failure_early"
CONDITION_PARAMS = dict(dropout=0.70, delay=8, agent=1, start=25, duration=80)

ENTRY_EXTRA = {
    "sweep": ["--graph-encoders", "multi_relation", "--multi-root",
              r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\ea_rg_mappo_s_gate_prior",
              "--run-dir-template", "ppo_seed{seed}_1m",
              "--checkpoint-glob", "actor_critic_update_*.pt",
              "--graph-relation-ablation", "none", "--graph-message-ablation", "none",
              "--role-gate-prior-strength", "0.4", "--role-pair-gate-fixed-value", "0.5"],
    "happo": ["--happo-root",
              r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802\happo",
              "--run-dir-template", "ppo_seed{seed}_1m",
              "--checkpoint-glob", "happo_update_*.pt"],
    "mappo": ["--mappo-root",
              r"D:\Code\Codex\ri_gmappo_uav_mappo_v1.5\results\paper_config_runs\formal_mappo_v1.5_ppo_977_20260806",
              "--run-dir-template", "ppo_seed{seed}",
              "--checkpoint-glob", "actor_critic_update_*.pt"],
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_manifest() -> dict[tuple[str, int], dict]:
    p = ROOT / "docs/robustness_v1_5_assets/robustness_checkpoint_manifest.csv"
    out = {}
    with p.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            out[(r["method"], int(r["train_seed"]))] = r
    return out


def derive_seed() -> int:
    h = hashlib.sha256((PROTOCOL_COMMIT + ANCHOR).encode()).hexdigest().upper()
    cand = (int(h[0:8], 16) % 900000) + 100000
    while cand in RESERVED:
        cand = ((cand + 1) % 900000) + 100000
    return cand


def wilson_lower_95(recovered: float, exposed: float, z: float = 1.96) -> float:
    """Must match the FROZEN implementation (z=1.96) exactly so the smoke
    recompute is identical to the eval summary (1e-10 acceptance)."""
    if exposed <= 0.0:
        return 0.0
    p = recovered / exposed
    denom = 1 + z * z / exposed
    centre = p + z * z / (2 * exposed)
    half = z * math.sqrt(p * (1 - p) / exposed + z * z / (4 * exposed * exposed))
    return (centre - half) / denom


def run_entry(entry: str, manifest_row: dict, out_dir: Path) -> dict:
    facts: dict = {}
    facts["entry"] = entry
    facts["method"] = manifest_row["method"]
    facts["train_seed"] = int(manifest_row["train_seed"])
    facts["checkpoint_update"] = manifest_row["selected_checkpoint_update"]
    facts["checkpoint_path"] = manifest_row["checkpoint_abs"]
    facts["checkpoint_sha256"] = manifest_row["file_sha256"]
    facts["manifest_sha256"] = manifest_row["manifest_sha256"]
    facts["condition"] = CONDITION
    facts.update(CONDITION_PARAMS)
    facts["smoke_base_seed"] = SMOKE_BASE_SEED
    facts["episodes"] = EPISODES
    facts["episode_seeds"] = [SMOKE_BASE_SEED + i for i in range(EPISODES)]

    log_path = out_dir / f"{entry}_smoke.log"
    cmd = [
        PYTHON, "-B",
        str(ROOT / "scripts/evaluate_robustness_v1_5.py"),
        "--entry", entry,
        "--split", "test",
        "--base-seed", str(SMOKE_BASE_SEED),
        "--episodes", str(EPISODES),
        "--eval-batch-size", "1",
        "--scenarios", CONDITION,
        "--seeds", str(TRAIN_SEED),
        "--checkpoint-updates", facts["checkpoint_update"],
        "--target-policy", "straight", "--strict-target-sensing",
        "--agent-target-info-bottleneck",
        "--target-prior-position", "10000", "0", "5000",
        "--max-target-message-age-steps", "80", "--min-target-confidence", "0.2",
        "--selection-metric", "legacy_recovery", "--selection-success-weight", "100",
        "--max-selection-collision-rate", "0.0",
        "--selection-policy", "v1_5_wilson", "--selection-group", "suite",
        "--device", "cuda",
        "--out-dir", str(out_dir),
    ] + ENTRY_EXTRA[entry]
    with log_path.open("w", encoding="utf-8") as f:
        r = subprocess.run(cmd, cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    facts["exit_code"] = r.returncode
    facts["log_path"] = str(log_path)
    # module identity from log
    log = log_path.read_text(encoding="utf-8", errors="replace")
    for line in log.splitlines():
        if line.startswith("[robustness] entry="):
            m = line.split("module=", 1)
            if len(m) == 2:
                facts["module_file"] = m[1].split(" sha=", 1)[0].strip()
            s = line.split("sha=", 1)
            if len(s) == 2:
                facts["module_sha256"] = s[1].strip()
        if "SCENARIOS identity=" in line:
            facts["scenarios_identity"] = line.split("identity=", 1)[1].split()[0]
    return facts


def recompute_summary(ep_csv: Path) -> dict:
    with ep_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    n = len(rows)
    success = sum(1 for r in rows if float(r.get("success", 0.0)) > 0.5)
    collision = sum(1 for r in rows if float(r.get("collision", 0.0)) > 0.5)
    # exposed rule: steps >= node_failure_start_step (per scenario)
    exposed = 0
    recovered = 0
    rec_steps = []
    succ_steps = [float(r["steps"]) for r in rows if float(r.get("success", 0.0)) > 0.5]
    for r in rows:
        fs = r.get("node_failure_start_step")
        if fs in (None, ""):
            continue
        fstep = float(fs)
        steps = float(r.get("steps", 0.0))
        if steps >= fstep:
            exposed += 1
            if float(r.get("post_failure_chain_recovered", 0.0)) > 0.5:
                recovered += 1
                rs = float(r.get("post_failure_chain_recovery_steps", -1.0))
                if rs >= 0:
                    rec_steps.append(rs)
    rec_given = recovered / exposed if exposed > 0 else float("nan")
    return {
        "episode_count": n,
        "success_count": success, "success_rate": success / n if n else float("nan"),
        "collision_count": collision, "collision_rate": collision / n if n else float("nan"),
        "exposed_count": exposed,
        "recovered_count": recovered,
        "recovery_given_exposure": rec_given,
        "time_to_success": float(sum(succ_steps) / len(succ_steps)) if succ_steps else float("nan"),
        "time_to_recovery": float(sum(rec_steps) / len(rec_steps)) if rec_steps else float("nan"),
        "wilson_lower_95": wilson_lower_95(float(recovered), float(exposed)),
        "estimate_unstable": 1 if exposed < 10 else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-dir", type=Path, default=ROOT / "_smoke/robustness_v1_5")
    args = parser.parse_args()
    smoke_dir: Path = args.smoke_dir
    audit_dir = smoke_dir / "smoke_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    recomputed_seed = derive_seed()
    if recomputed_seed != SMOKE_BASE_SEED:
        print("SMOKE BASE SEED DRIFT:", recomputed_seed, SMOKE_BASE_SEED)
        return 1

    manifest = load_manifest()
    all_facts: list[dict] = []
    problems: list[str] = []

    for entry, method in (("sweep", "full_ea_rg"), ("happo", "happo"), ("mappo", "mappo")):
        row = manifest[(method, TRAIN_SEED)]
        out_dir = smoke_dir / entry
        out_dir.mkdir(parents=True, exist_ok=True)
        facts = run_entry(entry, row, out_dir)
        all_facts.append(facts)
        ep = out_dir / "test_episode_metrics.csv"
        su = out_dir / "test_checkpoint_summary.csv"
        sel = out_dir / "test_selected_checkpoints.csv"
        ok_ep = ep.exists() and len(list(csv.DictReader(ep.open(encoding="utf-8")))) == EPISODES
        ok_su = su.exists() and len(list(csv.DictReader(su.open(encoding="utf-8")))) == 1
        ok_sel = sel.exists() and len(list(csv.DictReader(sel.open(encoding="utf-8")))) == 0
        ok_exit = facts["exit_code"] == 0
        facts.update({
            "episode_rows_ok": ok_ep, "summary_rows_ok": ok_su,
            "selection_rows_ok": ok_sel, "exit_ok": ok_exit,
            "PASS": ok_exit and ok_ep and ok_su and ok_sel,
        })
        if not facts["PASS"]:
            problems.append(f"{entry}: exit={facts['exit_code']} ep={ok_ep} su={ok_su} sel={ok_sel}")

    # summary recompute comparison
    comp_rows: list[dict] = []
    for facts in all_facts:
        entry = facts["entry"]
        su_csv = smoke_dir / entry / "test_checkpoint_summary.csv"
        with su_csv.open("r", encoding="utf-8", newline="") as f:
            srows = list(csv.DictReader(f))
        s0 = srows[0] if srows else {}
        rec = recompute_summary(smoke_dir / entry / "test_episode_metrics.csv")
        # the frozen eval writes floats with f"{x:.6g}" (6 significant digits);
        # compare the SAME formatting to avoid false mismatches
        def fmt(x):
            if isinstance(x, float):
                if math.isnan(x):
                    return "nan"
                if math.isinf(x):
                    return "inf"
                return f"{x:.6g}"
            return str(x)
        checks = {
            "episode_count": rec["episode_count"] == EPISODES,
            "exposed_count": rec["exposed_count"] == int(float(s0.get("failure_exposed_count", 0) or 0)),
            "recovered_count": rec["recovered_count"] == int(float(s0.get("recovered_given_exposure_count", 0) or 0)),
            "success_rate": fmt(rec["success_rate"]) == fmt(float(s0.get("success_mean", 0) or 0)),
            "collision_rate": fmt(rec["collision_rate"]) == fmt(float(s0.get("collision_mean", 0) or 0)),
            "recovery": fmt(rec["recovery_given_exposure"]) == fmt(float(s0.get("recovery_given_exposure", 0) or 0)),
            "wilson": fmt(rec["wilson_lower_95"]) == fmt(float(s0.get("wilson_lower_95", 0) or 0)),
        }
        ok = all(checks.values())
        comp_rows.append({
            "entry": entry, **{f"chk_{k}": v for k, v in checks.items()},
            "recomputed": json.dumps(rec, default=str), "summary": json.dumps(dict(s0), default=str),
            "match": "PASS" if ok else "FAIL",
        })
        if not ok:
            problems.append(f"{entry}: summary recompute mismatch {checks}")

    n_pass = sum(1 for f in all_facts if f["PASS"]) + sum(1 for c in comp_rows if c["match"] == "PASS")
    all_ok = (len(all_facts) == 3 and len(comp_rows) == 3
              and all(f["PASS"] for f in all_facts) and all(c["match"] == "PASS" for c in comp_rows)
              and not problems)

    # outputs SHA
    sha_map = {}
    for entry in ("sweep", "happo", "mappo"):
        for f in (smoke_dir / entry).glob("*.csv"):
            sha_map[f.relative_to(smoke_dir).as_posix()] = sha256_file(f)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with (audit_dir / "robustness_import_identity.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_facts[0].keys()))
        w.writeheader(); w.writerows(all_facts)
    with (audit_dir / "robustness_summary_recompute.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comp_rows[0].keys()))
        w.writeheader(); w.writerows(comp_rows)
    (audit_dir / "robustness_smoke_outputs_sha256.txt").write_text(
        "\n".join(f"{v}  {k}" for k, v in sorted(sha_map.items())) + "\n", encoding="utf-8")
    smoke_manifest = {
        "generated": now,
        "protocol_commit": PROTOCOL_COMMIT,
        "smoke_base_seed": SMOKE_BASE_SEED,
        "condition": CONDITION, "condition_params": CONDITION_PARAMS,
        "train_seed": TRAIN_SEED, "episodes": EPISODES,
        "chains": all_facts, "summary_recompute": comp_rows,
        "overall": "PASS" if all_ok else "FAIL",
        "problems": problems,
    }
    (audit_dir / "robustness_smoke_manifest.json").write_text(json.dumps(smoke_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Robustness Phase-2 Smoke Audit (3 chains, R09)",
        "",
        f"- generated: {now}",
        f"- protocol: FORMAL_ROBUSTNESS_PROTOCOL_V1_5 (phase-1 freeze @ {PROTOCOL_COMMIT})",
        f"- smoke base seed: {SMOKE_BASE_SEED} (derived: SHA256('{PROTOCOL_COMMIT}' + '{ANCHOR}'))",
        f"- condition: {CONDITION} (dropout={CONDITION_PARAMS['dropout']} delay={CONDITION_PARAMS['delay']} "
        f"agent={CONDITION_PARAMS['agent']} start={CONDITION_PARAMS['start']} dur={CONDITION_PARAMS['duration']})",
        f"- train seed: {TRAIN_SEED}, episodes: {EPISODES} (seeds {SMOKE_BASE_SEED}..{SMOKE_BASE_SEED + EPISODES - 1})",
        "",
        "## Per-chain facts",
        "",
    ]
    for f in all_facts:
        md.append(f"- [{('PASS' if f['PASS'] else 'FAIL')}] {f['entry']}: exit={f['exit_code']} "
                  f"module={f.get('module_file')} sha={f.get('module_sha256')} "
                  f"scenarios_id={f.get('scenarios_identity')} ckpt={f['checkpoint_sha256'][:16]}...")
        md.append(f"    episode_rows_ok={f['episode_rows_ok']} summary_rows_ok={f['summary_rows_ok']} "
                  f"selection_rows_ok={f['selection_rows_ok']}")
    md.append("")
    md.append("## Summary recompute (from 2 episode rows)")
    for c in comp_rows:
        md.append(f"- [{c['match']}] {c['entry']}")
    md.append("")
    if problems:
        md.append("## PROBLEMS")
        for p in problems:
            md.append(f"- {p}")
        md.append("")
    md.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    (audit_dir / "robustness_smoke_audit.md").write_text("\n".join(md), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    print(f"smoke dir: {smoke_dir}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
