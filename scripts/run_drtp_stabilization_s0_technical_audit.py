"""Zero-training technical audit for frozen DRTP-TR and Conservative-DRTP.

This is intentionally sampler-only: it creates no environment, policy,
checkpoint, evaluation tape rollout, optimizer step, or training result.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS, CONSERVATIVE_UNIFORM_ANCHOR, DRTP_TRUST_REGION_L1,
    DRTPSelection, DRTPTopologySampler, FAILURE_GROUPS, Q_MAX, Q_MIN, UNIFORM_Q,
)

OUT = ROOT / "docs" / "drtp_stabilization_s0"


def select(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, -1 if group == "N" else 44, 0 if group == "N" else 80,
                         -1 if group == "N" else 1)


def fill(sampler: DRTPTopologySampler, values: dict[str, float], repeats: int = 16) -> None:
    for group in ALL_GROUPS:
        for _ in range(repeats):
            sampler.record_completed_return(select(group), values[group])


def boundary_sequence(sampler: DRTPTopologySampler, values: dict[str, float]) -> list[dict]:
    rows = []
    for update in (32, 64, 96, 128, 160, 192, 224):
        fill(sampler, values)
        row = sampler.maybe_update(update)
        if row is not None:
            rows.append(row)
    return rows


def q_valid(sampler: DRTPTopologySampler) -> bool:
    return math.isclose(sum(sampler.q.values()), 1.0, abs_tol=1e-10) and all(
        Q_MIN - 1e-12 <= sampler.q[group] <= Q_MAX + 1e-12 for group in FAILURE_GROUPS
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    steep = {"N": 200.0, "F0": 1.0, "TE": 25.0, "TL": 50.0, "DS": 75.0, "DL": 100.0, "CP": 125.0}
    nearly_flat = {"N": 100.0, **{group: 99.99 for group in FAILURE_GROUPS}}
    checks: dict[str, bool] = {}

    # The three modes share all pre-update logic.  A small candidate movement
    # must therefore recover original DRTP exactly when TR is inactive.
    original = DRTPTopologySampler("drtp", 9011, 3907)
    tr_flat = DRTPTopologySampler("drtp_tr", 9011, 3907)
    boundary_sequence(original, nearly_flat); boundary_sequence(tr_flat, nearly_flat)
    checks["drtp_tr_recovers_original_when_final_movement_within_delta"] = all(
        math.isclose(original.q[group], tr_flat.q[group], abs_tol=1e-12) for group in FAILURE_GROUPS
    ) and not tr_flat.last_trust_region_active

    tr = DRTPTopologySampler("drtp_tr", 9012, 3907)
    tr_rows = boundary_sequence(tr, steep)
    adapted = [row for row in tr_rows if row["adapted"]]
    checks["drtp_tr_activates_on_steep_target"] = any(bool(row["trust_region_active"]) for row in adapted)
    checks["drtp_tr_final_l1_bound"] = all(float(row["q_step_l1"]) <= DRTP_TRUST_REGION_L1 + 1e-10 for row in adapted)
    checks["drtp_tr_simplex_floor_cap"] = q_valid(tr)

    conservative = DRTPTopologySampler("conservative_drtp", 9013, 3907)
    conservative_rows = boundary_sequence(conservative, steep)
    adapted_conservative = [row for row in conservative_rows if row["adapted"]]
    checks["conservative_final_l1_bound"] = all(
        float(row["q_step_l1"]) <= DRTP_TRUST_REGION_L1 + 1e-10 for row in adapted_conservative
    )
    checks["conservative_simplex_floor_cap"] = q_valid(conservative)
    checks["conservative_remains_nonuniform_under_steep_evidence"] = any(
        abs(conservative.q[group] - UNIFORM_Q) > 1e-8 for group in FAILURE_GROUPS
    )

    # Save/reload in the middle of a return window must retain candidate state.
    left, right = DRTPTopologySampler("drtp_tr", 9014, 3907), DRTPTopologySampler("drtp_tr", 9014, 3907)
    fill(left, steep, repeats=7)
    right.load_state_dict(left.state_dict())
    fill(left, steep, repeats=9); fill(right, steep, repeats=9)
    checks["drtp_tr_mid_window_save_resume_exact"] = left.maybe_update(32) == right.maybe_update(32) and left.state_dict() == right.state_dict()

    # Candidate modes do not alter selection RNG before any adaptation.
    baseline, candidate = DRTPTopologySampler("drtp", 9015, 3907), DRTPTopologySampler("drtp_tr", 9015, 3907)
    checks["pre_adaptation_rng_selection_equivalence"] = [baseline.select(64, 0, i) for i in range(32)] == [candidate.select(64, 0, i) for i in range(32)]
    checks["candidate_telemetry_fields_present"] = all(field in DRTPTopologySampler.log_fields() for field in (
        "target_l1", "q_step_l1", "trust_region_active"
    ))
    checks["constants_match_s0_freeze"] = math.isclose(DRTP_TRUST_REGION_L1, 0.02513300038143937, abs_tol=0.0) and math.isclose(CONSERVATIVE_UNIFORM_ANCHOR, .20, abs_tol=0.0)

    result = {
        "protocol": "DRTP-STABILIZATION-S0-TECHNICAL-AUDIT-V1",
        "training_started": False, "evaluation_started": False, "environment_created": False,
        "checks": checks, "delta_q_l1": DRTP_TRUST_REGION_L1,
        "uniform_anchor": CONSERVATIVE_UNIFORM_ANCHOR,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "implementation_order": "adaptive target -> bounded simplex projection -> [S2 target anchor] -> final L1 trust region; no post-TR projection",
        "scope_note": "Forced-target history replay tests algebra only; counterfactual learning is not claimed.",
    }
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    path = OUT / "S0_TECHNICAL_AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "S0_TECHNICAL_AUDIT.md").write_text(
        "# S0 DRTP-TR technical audit\n\n"
        f"Status: `{result['status']}`\n\n"
        "This sampler-only audit ran no environment, optimizer, checkpoint, evaluation, or training.\n\n"
        "- Final bound: `||q_(u+1)-q_u||_1 <= 0.02513300038143937`.\n"
        "- S2 ordering: adaptive target → simplex projection → 20% uniform target anchor → final L1 TR.\n"
        "- No projection is applied after the final TR, because the clipped point is a convex combination of valid simplex points.\n"
        f"- Checks: `{json.dumps(checks, sort_keys=True)}`.\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
