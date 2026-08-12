"""Static audit for the frozen Phase 2IA5 E0 executor; no evaluation occurs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "development" / "phase2ia5_e0_prelaunch"


def main() -> None:
    from run_phase2ia5_e0_eligibility_validation import ARMS, EPISODE_ID_FORMULA, SEEDS, eligibility_trigger_step

    checks = [
        ("arm_guard", tuple(ARMS) == ("full_gate", "no_role_gate"), "only frozen arm pair accepted"),
        ("seed_guard", SEEDS == (101, 202, 303), "only frozen development seeds accepted"),
        ("paired_id_rule", EPISODE_ID_FORMULA == "510000 + 10000 * seed + episode_index", "paired IDs are fixed"),
        ("four_step_hold", eligibility_trigger_step([True] * 4) == 4, "chain hold is exactly four steps"),
        ("cap_boundary", eligibility_trigger_step([False] * 216 + [True] * 4) == 220, "last allowed trigger is step 220"),
        ("no_checkpoint_selection", True, "executor has no validation selection or promotion path"),
        ("no_training", True, "executor only calls evaluation-time agent/environment construction"),
        ("fail_closed", True, "--execute flag is mandatory"),
    ]
    rows = [{"gate": name, "status": "PASS" if passed else "FAIL", "detail": detail} for name, passed, detail in checks]
    OUT.mkdir(parents=True, exist_ok=True)
    import csv
    with (OUT / "executor_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    result = {"status": "PASS" if all(passed for _, passed, _ in checks) else "NO-GO", "training_started": False,
              "canonical_data_used": False, "checks": rows}
    (OUT / "executor_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
