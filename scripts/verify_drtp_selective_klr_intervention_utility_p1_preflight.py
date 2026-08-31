"""Technical gate for the prospective, observational P1 shadow audit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from run_drtp_selective_klr_intervention_utility_p1_single import SEEDS, config

FREEZE = ROOT / "configs" / "drtp_selective_klr_intervention_utility_p1_freeze.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    probes = [config(seed, args.output / "config_probe" / str(seed)) for seed in SEEDS]
    checks = {
        "p1_authorized": freeze["authorization"]["p1_shadow_audit_authorized"] is True,
        "selective_klr_not_authorized": freeze["authorization"]["selective_klr_training_authorized"] is False,
        "mainline_a_unchanged": freeze["authorization"]["mainline_a_unchanged"] is True,
        "ten_clean_frozen_seeds": tuple(freeze["cohorts"]["A"] + freeze["cohorts"]["B"]) == SEEDS,
        "original_drtp_only": all(c.drtp_sampler_mode == "drtp" and c.policy_update_guard_mode == "none" and c.target_kl is None for c in probes),
        "alarm_exact": all(c.intervention_utility_audit_enabled and c.intervention_utility_alarm_kl == 0.02 for c in probes),
        "probe_exact": all(c.intervention_utility_probe_count == 4 for c in probes),
        "budget_exact": all(c.updates == 1953 and c.num_envs == 4 and c.rollout_steps == 64 for c in probes),
        "formal_eval_disabled": all(c.evaluation_enabled is False for c in probes),
    }
    payload = {"status": "P1_PREFLIGHT_PASS" if all(checks.values()) else "P1_PREFLIGHT_FAIL", "checks": checks, "freeze_sha256": sha(FREEZE)}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if not all(checks.values()): raise SystemExit(2)


if __name__ == "__main__":
    main()
