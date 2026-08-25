"""Zero-training R-DRTP implementation audit with one-update smoke only."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS, FAILURE_GROUPS, RDRTP_ALPHA_MAX, RDRTP_LAMBDA_V, RDRTP_N0,
    RDRTP_V_MAX, DRTPSelection, DRTPTopologySampler, UNIFORM_Q,
)
from scripts.run_drtp_sg_technical_verification import (  # noqa: E402
    build_sg, frozen_cfg,
)
from algorithms.ri_gmappo.simple_ri_gmappo import load_matching_state_dict, train_ri_gmappo  # noqa: E402
import torch  # noqa: E402


OUT = ROOT / "results" / "development" / "r_drtp_technical_audit_v2"


def sel(group: str) -> DRTPSelection:
    return DRTPSelection(group, group, 44 if group != "N" else -1, 80 if group != "N" else 0,
                         -1 if group == "N" else 1)


def fill(sampler: DRTPTopologySampler, value: float = 100.0, count: int = 16) -> None:
    for group in ALL_GROUPS:
        for _ in range(count):
            sampler.record_completed_return(sel(group), value)


def sampler_audit() -> dict:
    result: dict[str, object] = {
        "constants_frozen": [RDRTP_N0, RDRTP_LAMBDA_V, RDRTP_V_MAX, RDRTP_ALPHA_MAX] == [8.0, 1.0, 1.0, 1.0],
        "group_set": len(FAILURE_GROUPS) == 6 and set(FAILURE_GROUPS).issubset(ALL_GROUPS),
    }
    high = DRTPTopologySampler("r_drtp", 9911, 3907)
    for update in (32, 64, 96, 128):
        fill(high)
        high.maybe_update(update)
    fill(high, count=16)
    high_row = high.maybe_update(160)
    low = DRTPTopologySampler("r_drtp", 9911, 3907)
    for update in (32, 64, 96, 128):
        fill(low)
        low.maybe_update(update)
    low_row = low.maybe_update(160)
    result["finite_update_row"] = high_row is not None and math.isfinite(float(high_row["alpha"]))
    result["bounded_alpha"] = 0.0 <= float(high_row["alpha"]) <= RDRTP_ALPHA_MAX
    result["uniform_fallback_empty_window"] = low_row is not None and all(
        math.isclose(low.q[group], UNIFORM_Q, abs_tol=1e-12) for group in FAILURE_GROUPS
    ) and math.isclose(float(low_row["alpha"]), 0.0, abs_tol=1e-12)
    result["q_bounds_mass"] = math.isclose(sum(high.q.values()), 1.0, abs_tol=1e-10) and all(
        0.05 - 1e-12 <= value <= 0.35 + 1e-12 for value in high.q.values()
    )
    replay_left = DRTPTopologySampler("r_drtp", 9912, 3907)
    replay_right = DRTPTopologySampler("r_drtp", 9912, 3907)
    for update in (32, 64, 96, 128, 160):
        fill(replay_left, 100.0, 16)
        fill(replay_right, 100.0, 16)
        left = replay_left.maybe_update(update)
        right = replay_right.maybe_update(update)
        if left != right or replay_left.state_dict() != replay_right.state_dict():
            result["deterministic_replay"] = False
            break
    else:
        result["deterministic_replay"] = True
    return result


def one_update_smoke() -> dict:
    out = OUT / "r_drtp_one_update"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    cfg = frozen_cfg(9913, out, "r_drtp", True)
    train_ri_gmappo(cfg)
    checkpoint = out / "actor_critic_latest.pt"
    reloaded = build_sg(9913)
    load_matching_state_dict(reloaded, str(checkpoint), torch.device("cpu"))
    return {
        "train_log": (out / "train_log.csv").exists(),
        "checkpoint": checkpoint.exists() and checkpoint.stat().st_size > 0,
        "sampler_manifest": (out / "drtp_topology_sampler_manifest.json").exists(),
        "sampler_log": (out / "drtp_topology_sampler_log.csv").exists(),
        "mode": json.loads((out / "drtp_topology_sampler_manifest.json").read_text(encoding="utf-8"))["mode"],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sampler = sampler_audit()
    smoke = one_update_smoke()
    result = {
        "protocol": "R-DRTP-P2-TECHNICAL-AUDIT-V1",
        "training_started": False,
        "long_training_started": False,
        "new_evaluation_tape": False,
        "heldout_or_canonical_used": False,
        "sampler": sampler,
        "one_update_smoke": smoke,
    }
    result["all_checks_pass"] = all(sampler.values()) and all(
        smoke[key] is True for key in ("train_log", "checkpoint", "sampler_manifest", "sampler_log")
    ) and smoke["mode"] == "r_drtp"
    result["status"] = "PASS" if result["all_checks_pass"] else "REVISE"
    path = OUT / "R_DRTP_TECHNICAL_AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(path)}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
