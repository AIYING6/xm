"""Zero-training semantic audit for the frozen Stable-DRTP R1 protocol."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS, CONSERVATIVE_UNIFORM_ANCHOR, DRTP_TRUST_REGION_L1,
    FAILURE_GROUPS, Q_MAX, Q_MIN, UNIFORM_Q, DRTPSelection, DRTPTopologySampler,
)


def selection(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, -1 if group == "N" else 44,
                         0 if group == "N" else 80, -1 if group == "N" else 1)


def feed(sampler: DRTPTopologySampler, values: dict[str, float], count: int) -> None:
    for group in ALL_GROUPS:
        for _ in range(count):
            sampler.record_completed_return(selection(group), values[group])


def valid(q: dict[str, float]) -> bool:
    return math.isclose(sum(q.values()), 1.0, abs_tol=1e-10) and all(
        Q_MIN - 1e-12 <= q[group] <= Q_MAX + 1e-12 for group in FAILURE_GROUPS
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    steep = {"N": 200.0, "F0": 1.0, "TE": 25.0, "TL": 50.0,
             "DS": 75.0, "DL": 100.0, "CP": 125.0}
    sampler = DRTPTopologySampler("conservative_drtp", 9301, 3907)
    rows = []
    for update in (32, 64, 96, 128, 160, 192, 224):
        feed(sampler, steep, 16)
        row = sampler.maybe_update(update)
        if row is not None:
            rows.append(row)
    adapted = [row for row in rows if row["adapted"]]
    checks = {
        "mode_is_conservative_drtp": sampler.mode == "conservative_drtp",
        "delta_exact": DRTP_TRUST_REGION_L1 == 0.02513300038143937,
        "anchor_exact": CONSERVATIVE_UNIFORM_ANCHOR == 0.20,
        "anchored_target_formula": all(all(math.isclose(
            float(row[f"anchored_target_{g}"]),
            .8 * float(row[f"projected_target_{g}"]) + .2 * UNIFORM_Q,
            abs_tol=1e-12) for g in FAILURE_GROUPS) for row in adapted),
        "projected_and_anchored_simplex": all(math.isclose(
            sum(float(row[f"projected_target_{g}"]) for g in FAILURE_GROUPS), 1.0, abs_tol=1e-10
        ) and math.isclose(sum(float(row[f"anchored_target_{g}"]) for g in FAILURE_GROUPS), 1.0, abs_tol=1e-10)
            for row in adapted),
        "final_simplex_floor_cap": valid(sampler.q),
        "final_l1_bound": all(float(row["q_step_l1"]) <= DRTP_TRUST_REGION_L1 + 1e-10 for row in adapted),
        "telemetry_fields": all(field in DRTPTopologySampler.log_fields() for field in (
            "pre_tr_l1", "trust_region_active", *[f"anchored_target_{g}" for g in FAILURE_GROUPS]
        )),
    }
    left = DRTPTopologySampler("conservative_drtp", 9302, 3907)
    right = DRTPTopologySampler("conservative_drtp", 9302, 3907)
    feed(left, steep, 7)
    right.load_state_dict(left.state_dict())
    feed(left, steep, 9); feed(right, steep, 9)
    checks["mid_window_save_resume_exact"] = (
        left.maybe_update(32) == right.maybe_update(32) and left.state_dict() == right.state_dict()
    )
    original = DRTPTopologySampler("drtp", 9303, 3907)
    candidate = DRTPTopologySampler("conservative_drtp", 9303, 3907)
    checks["pre_adaptation_rng_equivalence"] = [original.select(64, 0, i) for i in range(32)] == [candidate.select(64, 0, i) for i in range(32)]

    payload = {
        "protocol": "DRTP-STABLE-R1-TECHNICAL-AUDIT-V1",
        "training_started": False,
        "environment_created": False,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "delta_q_l1": DRTP_TRUST_REGION_L1,
        "uniform_anchor": CONSERVATIVE_UNIFORM_ANCHOR,
        "order": "adaptive target -> bounded-simplex projection -> 0.80 adaptive + 0.20 uniform -> final L1 trust region",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
