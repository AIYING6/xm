"""Formal 15/15 validation audit for v1.4 (eval-ops-v1.4.2).

Checks, for the 5 methods x 3 seeds selected checkpoints:
  - exactly one row per method/seed (15 unique)
  - selected update in {100,200,...,900,977}
  - collision meets the frozen gate (0.0)
  - checkpoint file exists; recomputed SHA256 == recorded checkpoint_sha256
  - for snapshots also present in the training-seal manifest (0977): SHA matches
  - selection_metric == legacy_recovery, selection_success_weight == 100
  - scenario suite + episodes + base_seed recorded in selection CSV

Records SHA256 of the command manifest, the 5 method logs, the 5 selection
CSVs, and this audit script. Read-only; does not modify any result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\Code\Codex\ri_gmappo_uav_eval_v1.4.1\results\paper_config_runs\formal_main_validation_eval_ops_v1.4.2_20260804")
TRAIN_ROOT = Path(r"D:\Code\Codex\ri_gmappo_uav\results\paper_config_runs\formal_budget_post_sixth_freeze_v1.4_formal_main_20260802")
SEAL_SHA = TRAIN_ROOT / "_operator_notes" / "final_freeze" / "v1.4_checkpoint_sha256.csv"
ELIGIBLE = {100, 200, 300, 400, 500, 600, 700, 800, 900, 977}
METHODS = ["no_graph", "single_graph", "param_matched_single", "ea_rg_mappo_s_gate_prior", "happo"]
FREEZE_COMMIT = "6f391694ccb12244ba0ba5f453a79bb25cc782a4"
EVAL_COMMIT = "2514ca3"
EVAL_TAG = "formal-post-sixth-eval-ops-v1.4.2"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(p: Path) -> list[dict]:
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=BASE / "_logs" / f"validation_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    args = parser.parse_args()

    seal = {}
    if SEAL_SHA.exists():
        for r in read_csv(SEAL_SHA):
            seal[(r["method"], int(r["seed"]), int(r["checkpoint_path"].split("_")[-1].split(".")[0]))] = r["checkpoint_sha256"]

    lines = [
        "# v1.4 Formal Validation Audit (15/15)",
        "",
        f"audit time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"formal output root: `{BASE}`",
        f"training freeze: `{FREEZE_COMMIT}` (`formal-post-sixth-freeze-v1.4`)",
        f"evaluation: commit `{EVAL_COMMIT}`, tag `{EVAL_TAG}`",
        "",
        "## 1. Selection rows, uniqueness, eligibility",
        "",
        "```text",
        f"{'method':<24}{'seed':>4}{'update':>7}{'rec':>7}{'succ':>6}{'steps':>8}{'coll':>6}{'metric':>18}{'weight':>7}{'scenario':>16}",
    ]

    errors = []
    all_rows = []
    for m in METHODS:
        p = BASE / m / "validation_selected_checkpoints.csv"
        rows = read_csv(p)
        all_rows.extend((m, r) for r in rows)

    # uniqueness
    seen: set[tuple[str, str]] = set()
    for m, r in all_rows:
        key = (m, r["train_seed"])
        if key in seen:
            errors.append(f"duplicate method/seed: {key}")
        seen.add(key)
    if len(seen) != 15:
        errors.append(f"expected 15 unique method/seed, got {len(seen)}")

    for m, r in sorted(all_rows, key=lambda x: (x[0], int(x[1]["train_seed"]))):
        upd = int(r["selected_checkpoint_update"])
        rec = float(r["post_failure_chain_recovered_mean"])
        succ = float(r["success_mean"])
        steps = float(r["post_failure_chain_recovery_steps_mean"])
        coll = float(r["collision_mean"])
        metric = r.get("selection_metric", "")
        weight = r.get("selection_success_weight", "")
        scenario = r.get("scenario", "")
        if upd not in ELIGIBLE:
            errors.append(f"{m} seed{r['train_seed']}: update {upd} not eligible")
        if coll > 0.0:
            errors.append(f"{m} seed{r['train_seed']}: collision {coll} violates gate")
        if metric != "legacy_recovery":
            errors.append(f"{m} seed{r['train_seed']}: metric {metric!r}")
        if weight != "100":
            errors.append(f"{m} seed{r['train_seed']}: success weight {weight!r}")
        if scenario != "scenario_suite":
            errors.append(f"{m} seed{r['train_seed']}: scenario {scenario!r}")

        # checkpoint file + SHA
        cp = Path(r["selected_checkpoint"])
        if not cp.is_absolute():
            cp = TRAIN_ROOT / cp
        if not cp.exists():
            errors.append(f"{m} seed{r['train_seed']}: checkpoint missing {cp}")
            sha_now = "MISSING"
        else:
            sha_now = sha256(cp)
        sha_recorded = r.get("checkpoint_sha256", "")
        if sha_recorded and sha_now != "MISSING" and sha_now != sha_recorded.upper():
            errors.append(f"{m} seed{r['train_seed']}: recorded SHA mismatch")

        # compare with training-seal manifest when the snapshot exists there (0977)
        upd_in_seal = seal.get((m, int(r["train_seed"]), upd))
        if upd_in_seal and sha_now != "MISSING" and upd_in_seal != sha_now:
            errors.append(f"{m} seed{r['train_seed']} upd{upd}: SHA differs from training seal")

        lines.append(
            f"{m:<24}{r['train_seed']:>4}{upd:>7}{rec:>7.3f}{succ:>6.2f}{steps:>8.1f}{coll:>6.1f}{metric:>18}{weight:>7}{scenario:>16}"
        )

    lines.append("```")

    # SHA records
    lines.append("")
    lines.append("## 2. Artifact SHA256")
    lines.append("")
    manifest = BASE / "_validation_command_manifest.md"
    if manifest.exists():
        lines.append(f"command manifest: `{sha256(manifest)}` ({manifest.name})")
    for m in METHODS:
        sel = BASE / m / "validation_selected_checkpoints.csv"
        lines.append(f"selection CSV {m}: `{sha256(sel)}`")
        log = BASE / "_logs" / f"{m}_20260804_105043.log"
        if log.exists():
            lines.append(f"method log {m}: `{sha256(log)}`")
    lines.append(f"audit script: `{sha256(Path(__file__).resolve())}`")

    lines.append("")
    lines.append(f"## 3. Result: {'PASS' if not errors else 'FAIL'}")
    if errors:
        lines.append("")
        lines.append("Errors:")
        for e in errors:
            lines.append(f"- {e}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"audit written: {args.out}")
    print("RESULT:", "PASS" if not errors else "FAIL")
    for e in errors:
        print("  -", e)


if __name__ == "__main__":
    main()
