"""Read-only diagnostic: failure-exposure classification of selected checkpoints.

For each method/seed/scenario (selected checkpoint only), classify the 50
validation episodes into:
  pre_failure_success        : success before failure step (no exposure)
  exposed_and_recovered      : reached failure step AND recovered
  exposed_and_not_recovered  : reached failure step AND not recovered
  pre_failure_other          : ended before failure without success

Reports recovery_rate_given_exposure with the exposure sample size N_exposed.
This analysis does NOT modify any frozen v1.4 selection result.

Outputs (when --out-dir given):
  failure_exposure_by_method_seed_scenario.csv
  failure_exposure_summary.md
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\Code\Codex\ri_gmappo_uav_eval_v1.4.1\results\paper_config_runs\formal_main_validation_eval_ops_v1.4.2_20260804")
METHODS = ["no_graph", "single_graph", "param_matched_single", "ea_rg_mappo_s_gate_prior", "happo"]


def read_csv(p: Path) -> list[dict]:
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--no-overwrite", action="store_true", default=True,
                        help="Refuse to write into an existing out-dir (default True).")
    args = parser.parse_args()

    out_rows = []
    md_lines = [
        "# Failure-Exposure Diagnostic (read-only)",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "**Status: diagnostic only. Does not participate in v1.4 checkpoint",
        "selection; does not modify any frozen score or replace the frozen",
        "formal metric.**",
        "",
        "Per selected checkpoint, 50 validation episodes are classified into:",
        "pre_failure_success (success before failure step), exposed_and_recovered,",
        "exposed_and_not_recovered, pre_failure_other.",
        "",
        "```text",
        "method  seed  update  scenario        N  pre_succ  exp_rec  exp_unrec  pre_other  rec_given_exposure  N_exposed",
    ]

    for m in METHODS:
        sel_path = BASE / m / "validation_selected_checkpoints.csv"
        if not sel_path.exists():
            md_lines.append(f"{m}: selection CSV not found (still running?)")
            continue
        sel = read_csv(sel_path)
        episodes = read_csv(BASE / m / "validation_episode_metrics.csv")
        md_lines.append("")
        for srow in sel:
            seed = srow["train_seed"]
            upd = srow["selected_checkpoint_update"]
            rows = [r for r in episodes if r["train_seed"] == seed and r["checkpoint_update"] == upd]
            for sc in sorted({r["scenario"] for r in rows}):
                r_sc = [r for r in rows if r["scenario"] == sc]
                N = len(r_sc)
                pre_succ = 0
                exposed = []
                for r in r_sc:
                    steps = float(r["steps"])
                    fail = float(r["node_failure_start_step"])
                    if steps < fail:
                        if float(r["success"]) > 0.5:
                            pre_succ += 1
                    else:
                        exposed.append(r)
                exp_rec = sum(1 for r in exposed if float(r["post_failure_chain_recovered"]) > 0.5)
                exp_unrec = len(exposed) - exp_rec
                pre_other = N - pre_succ - len(exposed)
                rec_given = (exp_rec / len(exposed)) if exposed else float("nan")
                sc_short = sc.replace("dropout030_delay2_", "")
                out_rows.append({
                    "method": m, "train_seed": seed, "selected_update": upd,
                    "scenario": sc_short, "N_episodes": N,
                    "pre_failure_success": pre_succ,
                    "exposed_and_recovered": exp_rec,
                    "exposed_and_not_recovered": exp_unrec,
                    "pre_failure_other": pre_other,
                    "recovery_rate_given_exposure": f"{rec_given:.3f}" if exposed else "nan",
                    "N_exposed": len(exposed),
                })
                md_lines.append(
                    f"{m:<24} {seed}  {upd:>4}  {sc_short:<24} {N:>2}  {pre_succ:>7}  {exp_rec:>8}  {exp_unrec:>9}  {pre_other:>9}  {rec_given if exposed else float('nan'):>18.3f}  {len(exposed):>9}"
                )

    md_lines.append("```")
    md_lines.append("")
    md_lines.append(
        "Caveat: recovery_rate_given_exposure is unstable when N_exposed is small "
        "(e.g. 1-2 episodes). Do not compare percentages across methods with "
        "different exposure rates."
    )

    if args.out_dir is not None:
        if args.out_dir.exists() and args.no_overwrite:
            raise SystemExit(f"refusing to overwrite existing out-dir: {args.out_dir}")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        csv_path = args.out_dir / "failure_exposure_by_method_seed_scenario.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()) if out_rows else [])
            w.writeheader()
            w.writerows(out_rows)
        (args.out_dir / "failure_exposure_summary.md").write_text("\n".join(md_lines), encoding="utf-8")

        # input files SHA256
        input_rows = []
        for m in METHODS:
            for name in ("validation_selected_checkpoints.csv", "validation_episode_metrics.csv"):
                p = BASE / m / name
                if p.exists():
                    input_rows.append({"file": f"{m}/{name}", "sha256": sha256(p)})
        (args.out_dir / "input_files_sha256.csv").write_text(
            "file,sha256\n" + "\n".join(f"{r['file']},{r['sha256']}" for r in input_rows), encoding="utf-8")

        # copy the diagnostic script itself
        script_copy = args.out_dir / "analyze_failure_exposure.py"
        shutil.copy2(Path(__file__).resolve(), script_copy)

        # artifact SHA256
        artifact_rows = [
            {"artifact": "failure_exposure_by_method_seed_scenario.csv", "sha256": sha256(csv_path)},
            {"artifact": "failure_exposure_summary.md", "sha256": sha256(args.out_dir / "failure_exposure_summary.md")},
            {"artifact": "input_files_sha256.csv", "sha256": sha256(args.out_dir / "input_files_sha256.csv")},
            {"artifact": "analyze_failure_exposure.py", "sha256": sha256(script_copy)},
        ]
        (args.out_dir / "diagnostic_artifacts_sha256.csv").write_text(
            "artifact,sha256\n" + "\n".join(f"{r['artifact']},{r['sha256']}" for r in artifact_rows), encoding="utf-8")

        print(f"wrote diagnostic bundle to {args.out_dir}")
    else:
        print("\n".join(md_lines))


if __name__ == "__main__":
    main()
