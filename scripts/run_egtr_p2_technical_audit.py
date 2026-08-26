"""EGTR P2 implementation audit; no evaluation tape or long training."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import torch

from algorithms.ri_gmappo.drtp_topology_sampler import (
    ALL_GROUPS, FAILURE_GROUPS, EGTR_TRUST_REGION_L1, EGTRTopologySampler,
    DRTPSelection, DRTPTopologySampler, UNIFORM_Q,
)
from algorithms.ri_gmappo.simple_ri_gmappo import load_matching_state_dict, train_ri_gmappo
from scripts.run_drtp_sg_technical_verification import build_sg, frozen_cfg


OUT = ROOT / "results" / "development" / "egtr_p2_technical_audit_v3"


def selection(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, -1 if group == "N" else 44, 0 if group == "N" else 80,
                         -1 if group == "N" else 1)


def fill(sampler, values: dict[str, float], count: int = 16, omit: set[str] | None = None) -> None:
    omit = omit or set()
    for group in ALL_GROUPS:
        if group in omit:
            continue
        for _ in range(count):
            sampler.record_completed_return(selection(group), values[group])


def boundary_run(sampler, values, start=32, stop=160, omit=None):
    rows = []
    for update in range(start, stop + 1, 32):
        fill(sampler, values, omit=omit)
        rows.append(sampler.maybe_update(update))
    return rows


def audit_sampler() -> dict:
    checks = {}
    stable = {"N": 200.0, **{group: 100.0 + index * 5.0 for index, group in enumerate(FAILURE_GROUPS)}}
    low_noise = {"N": 100.0, **{group: 99.0 for group in FAILURE_GROUPS}}

    # Empty one group must not globally reset all adaptive evidence.
    partial = EGTRTopologySampler(3001, 3907)
    boundary_run(partial, stable, omit={"CP"})
    checks["single_empty_group_not_global_reset"] = partial.last_rho > 0.0 and any(
        abs(partial.q[group] - UNIFORM_Q) > 1e-12 for group in FAILURE_GROUPS
    )

    # Full-confidence, no-difficulty case recovers DRTP exactly.
    drtp = DRTPTopologySampler("drtp", 3002, 3907)
    egtr = EGTRTopologySampler(3002, 3907)
    for group in FAILURE_GROUPS:
        egtr.confidence_ema[group] = 1.0
    for update in (32, 64, 96, 128, 160):
        fill(drtp, low_noise)
        fill(egtr, low_noise)
        drtp.maybe_update(update)
        egtr.maybe_update(update)
    checks["full_confidence_drtp_recovery"] = all(
        math.isclose(egtr.q[group], drtp.q[group], abs_tol=1e-12) for group in FAILURE_GROUPS
    ) and not egtr.last_trust_active

    # Final output, not an intermediate vector, satisfies the L1 bound.
    checks["final_trust_region_hard_bound"] = egtr.last_q_step_l1 <= EGTR_TRUST_REGION_L1 + 1e-10
    checks["simplex_and_bounds"] = math.isclose(sum(egtr.q.values()), 1.0, abs_tol=1e-10) and all(
        0.05 - 1e-12 <= egtr.q[group] <= 0.35 + 1e-12 for group in FAILURE_GROUPS
    )

    # Translation and positive scaling preserve the gap evidence.
    base = EGTRTopologySampler(3003, 3907)
    shifted = EGTRTopologySampler(3003, 3907)
    scaled = EGTRTopologySampler(3003, 3907)
    values = {"N": 120.0, **{group: 80.0 + index for index, group in enumerate(FAILURE_GROUPS)}}
    shifted_values = {group: value + 1000.0 for group, value in values.items()}
    scaled_values = {group: value * 3.0 for group, value in values.items()}
    for update in (32, 64, 96, 128, 160):
        fill(base, values); fill(shifted, shifted_values); fill(scaled, scaled_values)
        base.maybe_update(update); shifted.maybe_update(update); scaled.maybe_update(update)
    checks["translation_invariance"] = all(
        math.isclose(base.confidence_ema[g], shifted.confidence_ema[g], abs_tol=1e-10) for g in FAILURE_GROUPS
    )
    checks["positive_scale_invariance"] = all(
        math.isclose(base.confidence_ema[g], scaled.confidence_ema[g], rel_tol=1e-8, abs_tol=1e-10) for g in FAILURE_GROUPS
    )

    signed = EGTRTopologySampler(3004, 3907)
    signed_values = {"N": 0.0, **{group: -10.0 for group in FAILURE_GROUPS}}
    rows = boundary_run(signed, signed_values)
    checks["signed_and_zero_median_finite"] = all(
        math.isfinite(float(row["rho"])) and math.isfinite(float(row["q_step_l1"])) for row in rows if row is not None
    )

    # Mid-window save/reload must match the uninterrupted boundary.
    left = EGTRTopologySampler(3005, 3907)
    right = EGTRTopologySampler(3005, 3907)
    fill(left, stable, count=7)
    state = left.state_dict()
    right.load_state_dict(state)
    fill(left, stable, count=9)
    fill(right, stable, count=9)
    left_row, right_row = left.maybe_update(32), right.maybe_update(32)
    checks["mid_window_save_reload_exact"] = left_row == right_row and left.state_dict() == right.state_dict()

    # Deterministic replay over all internal state.
    replay_a = EGTRTopologySampler(3006, 3907)
    replay_b = EGTRTopologySampler(3006, 3907)
    rows_a = boundary_run(replay_a, stable)
    rows_b = boundary_run(replay_b, stable)
    checks["deterministic_replay"] = rows_a == rows_b and replay_a.state_dict() == replay_b.state_dict()
    checks["telemetry_fields"] = all(field in EGTRTopologySampler.log_fields() for field in (
        "rho", "trust_region_distance", "trust_region_active", "q_uniform_distance", "q_step_l1",
        "confidence_ema_F0", "stale_duration_F0", "evidence_gap_F0", "evidence_r_F0",
    ))
    return checks


def one_update_smoke() -> dict:
    out = OUT / "egtr_one_update"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    cfg = frozen_cfg(3010, out, "egtr", True)
    train_ri_gmappo(cfg)
    checkpoint = out / "actor_critic_latest.pt"
    reloaded = build_sg(3010)
    load_matching_state_dict(reloaded, str(checkpoint), torch.device("cpu"))
    manifest = json.loads((out / "drtp_topology_sampler_manifest.json").read_text(encoding="utf-8"))
    return {
        "train_log": (out / "train_log.csv").exists(),
        "checkpoint": checkpoint.exists() and checkpoint.stat().st_size > 0,
        "sampler_log": (out / "drtp_topology_sampler_log.csv").exists(),
        "mode": manifest["mode"],
        "protocol": manifest["protocol"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    checks = audit_sampler()
    smoke = one_update_smoke()
    result = {
        "protocol": "EGTR-DRTP-P2-TECHNICAL-AUDIT-V1",
        "checks": checks,
        "one_update_smoke": smoke,
        "new_evaluation_tape": False,
        "heldout_or_canonical_used": False,
        "long_training_started": False,
    }
    result["all_checks_pass"] = all(checks.values()) and all(
        smoke[key] is True for key in ("train_log", "checkpoint", "sampler_log")
    ) and smoke["mode"] == "egtr" and smoke["protocol"] == "EGTR-DRTP-SG-MAPPO-CONTRACT-V1"
    result["status"] = "PASS" if result["all_checks_pass"] else "REVISE"
    path = OUT / "EGTR_DRTP_P2_TECHNICAL_AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(path)}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
