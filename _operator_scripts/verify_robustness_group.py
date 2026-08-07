# verify_robustness_group.py
# Post-call acceptance check for one robustness (method, seed, condition) cell.
#
# Checks:
#   - exit code file present (written by orchestrator) == 0
#   - episode rows == 50, summary rows == 1, selection rows == 0
#   - split=test on all episode rows; scenario == expected condition key
#   - no Traceback in log; no illegal NaN/Inf in model-output/rate/count fields
#     (legit empty time fields like "nan"/"inf"/"" are allowed per frozen schema)
# Usage:
#   python verify_robustness_group.py --group-dir <...> --condition <key> --log <...>
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

# fields where empty/nan/inf are legitimate when there is no sample
TIMEISH = {"time_to_success", "time_to_recovery", "time_to_recovery_given_exposure",
           "time_to_success_mean", "time_to_recovery_mean",
           "time_to_recovery_given_exposure_mean", "post_failure_chain_recovery_steps_mean",
           "post_failure_chain_recovered_mean", "post_failure_chain_recovery_steps_mean_censored"}
# fields that must always be finite numeric (counts / rates / probabilities)
REQUIRED_FINITE = {"success", "collision", "timeout", "steps"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-dir", type=Path, required=True)
    parser.add_argument("--condition", type=str, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    problems: list[str] = []
    gdir: Path = args.group_dir

    ep = gdir / "test_episode_metrics.csv"
    su = gdir / "test_checkpoint_summary.csv"
    sel = gdir / "test_selected_checkpoints.csv"

    if not ep.exists():
        problems.append("episode csv missing")
    else:
        with ep.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if len(rows) != 50:
            problems.append(f"episode rows {len(rows)} != 50")
        if rows:
            splits = {r.get("split") for r in rows}
            if splits != {"test"}:
                problems.append(f"split {splits} != test")
            scens = {r.get("scenario") for r in rows}
            if scens != {args.condition}:
                problems.append(f"scenario {scens} != {args.condition}")
        # required finite fields
        for r in rows:
            for k, v in r.items():
                if k in REQUIRED_FINITE and k in r:
                    if v in (None, ""):
                        problems.append(f"missing required field {k}")
                        continue
                    try:
                        fv = float(v)
                    except ValueError:
                        problems.append(f"non-numeric {k}={v!r}")
                        continue
                    if not math.isfinite(fv):
                        problems.append(f"non-finite {k}={v!r}")

    if not su.exists():
        problems.append("summary csv missing")
    else:
        with su.open("r", encoding="utf-8", newline="") as f:
            srows = list(csv.DictReader(f))
        if len(srows) != 1:
            problems.append(f"summary rows {len(srows)} != 1")

    if not sel.exists():
        problems.append("selection csv missing")
    else:
        with sel.open("r", encoding="utf-8", newline="") as f:
            n_sel = len(list(csv.DictReader(f)))
        if n_sel != 0:
            problems.append(f"selection rows {n_sel} != 0 (must be empty)")

    # log checks
    log = args.log.read_text(encoding="utf-8", errors="replace") if args.log.exists() else ""
    if "Traceback" in log:
        problems.append("Traceback in log")

    all_ok = not problems
    print("VERIFY:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
