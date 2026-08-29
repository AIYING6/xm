"""Zero-training readiness audit for the pre-frozen Conservative-DRTP S2 shot."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS, CONSERVATIVE_UNIFORM_ANCHOR, DRTP_TRUST_REGION_L1, FAILURE_GROUPS,
    Q_MAX, Q_MIN, UNIFORM_Q, DRTPSelection, DRTPTopologySampler,
)


def selection(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, -1 if group == "N" else 44, 0 if group == "N" else 80, -1 if group == "N" else 1)


def feed(sampler: DRTPTopologySampler, values: dict[str, float], count: int) -> None:
    for group in ALL_GROUPS:
        for _ in range(count):
            sampler.record_completed_return(selection(group), values[group])


def valid(q: dict[str, float]) -> bool:
    return math.isclose(sum(q.values()), 1.0, abs_tol=1e-10) and all(Q_MIN - 1e-12 <= q[group] <= Q_MAX + 1e-12 for group in FAILURE_GROUPS)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("--execute required")
    if args.output_dir.exists() and any(args.output_dir.iterdir()): raise FileExistsError(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    steep = {"N": 200.0, "F0": 1.0, "TE": 25.0, "TL": 50.0, "DS": 75.0, "DL": 100.0, "CP": 125.0}
    sampler = DRTPTopologySampler("conservative_drtp", 9201, 1953)
    rows = []
    for update in (32, 64, 96, 128, 160, 192, 224):
        feed(sampler, steep, 16); row = sampler.maybe_update(update)
        if row is not None: rows.append(row)
    adapted = [row for row in rows if row["adapted"]]
    checks = {
        "anchor_exact": all(all(math.isclose(float(row[f"anchored_target_{group}"]), .8 * float(row[f"projected_target_{group}"]) + .2 * UNIFORM_Q, abs_tol=1e-12) for group in FAILURE_GROUPS) for row in adapted),
        "projection_and_anchor_simplex": all(math.isclose(sum(float(row[f"projected_target_{group}"]) for group in FAILURE_GROUPS), 1.0, abs_tol=1e-10) and math.isclose(sum(float(row[f"anchored_target_{group}"]) for group in FAILURE_GROUPS), 1.0, abs_tol=1e-10) for row in adapted),
        "final_simplex_floor_cap": valid(sampler.q),
        "final_l1_bound": all(float(row["q_step_l1"]) <= DRTP_TRUST_REGION_L1 + 1e-10 for row in adapted),
        "pre_tr_l1_matches_anchored_target": all(math.isclose(float(row["pre_tr_l1"]), sum(abs(float(row[f"anchored_target_{group}"]) - float(row[f"q_{group}"])) for group in FAILURE_GROUPS) + float(row["q_step_l1"]), rel_tol=0.0, abs_tol=DRTP_TRUST_REGION_L1 + 1e-10) for row in adapted),
        "telemetry_fields_present": all(field in DRTPTopologySampler.log_fields() for field in ("pre_tr_l1", "trust_region_active", *[f"anchored_target_{group}" for group in FAILURE_GROUPS])),
        "frozen_constants": CONSERVATIVE_UNIFORM_ANCHOR == .20 and DRTP_TRUST_REGION_L1 == 0.02513300038143937,
    }
    # Exact state restoration during a partially filled sampler window.
    left, right = DRTPTopologySampler("conservative_drtp", 9202, 1953), DRTPTopologySampler("conservative_drtp", 9202, 1953)
    feed(left, steep, 7); right.load_state_dict(left.state_dict()); feed(left, steep, 9); feed(right, steep, 9)
    checks["mid_window_save_resume_exact"] = left.maybe_update(32) == right.maybe_update(32) and left.state_dict() == right.state_dict()
    original, candidate = DRTPTopologySampler("drtp", 9203, 1953), DRTPTopologySampler("conservative_drtp", 9203, 1953)
    checks["pre_adaptation_rng_equivalence"] = [original.select(64, 0, index) for index in range(32)] == [candidate.select(64, 0, index) for index in range(32)]
    result = {"protocol": "DRTP-STABILIZATION-S2-TECHNICAL-AUDIT-V1", "training_started": False,
              "environment_created": False, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
              "delta_q_l1": DRTP_TRUST_REGION_L1, "uniform_anchor": CONSERVATIVE_UNIFORM_ANCHOR,
              "order": "adaptive target -> bounded simplex projection -> 0.80 adaptive + 0.20 uniform -> final L1 trust region"}
    (args.output_dir / "S2_TECHNICAL_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS": raise SystemExit(1)


if __name__ == "__main__": main()
