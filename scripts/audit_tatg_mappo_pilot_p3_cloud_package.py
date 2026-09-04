"""Static cloud-package audit for the frozen TATG pilot training phase."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LAUNCHER = ROOT / "scripts" / "launch_tatg_mappo_pilot_autodl.sh"
BUNDLER = ROOT / "scripts" / "build_tatg_mappo_pilot_cloud_bundle.py"
FREEZE = ROOT / "configs" / "tatg_mappo_pilot_p3_cloud_package_freeze.json"


def collect_checks() -> tuple[dict[str, bool], dict[str, object]]:
    launcher = LAUNCHER.read_text(encoding="utf-8")
    bundler = BUNDLER.read_text(encoding="utf-8")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    checks = {
        "frozen_four_arms_and_three_seeds_are_enumerated": all(item in launcher for item in (*freeze["arms"], *map(str, freeze["seeds"]))),
        "launcher_uses_bounded_dynamic_slots": "MAX_PARALLEL" in launcher and "wait -n" in launcher,
        "launcher_requires_all_twelve_completion_manifests": '"$completed" -ne 12' in launcher,
        "launcher_has_no_evaluation_or_aggregation_command": " evaluate " not in launcher and " aggregate " not in launcher,
        "launcher_rejects_an_evaluation_directory": "must not create an evaluation directory" in launcher,
        "launcher_does_not_shutdown_the_instance": "shutdown" not in launcher,
        "bundle_is_source_only_and_hashes_each_input": "INCLUDED_TREES" in bundler and "sha256" in bundler and "results" not in bundler.split("INCLUDED_FILES", 1)[1].split("def sources", 1)[0],
        "package_contract_remains_unlaunched": freeze["status"] == "PACKAGE_READY_NOT_LAUNCHED" and not freeze["automatic_continuation"] and not freeze["automatic_shutdown"],
    }
    return checks, {"launcher_sha256": hashlib.sha256(LAUNCHER.read_bytes()).hexdigest(), "bundler_sha256": hashlib.sha256(BUNDLER.read_bytes()).hexdigest(), "training_started": False, "evaluation_started": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to write package audit output without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    checks, details = collect_checks()
    result = {"protocol": "TATG-MAPPO-FRESH-SEED-PILOT-CLOUD-PACKAGE-AUDIT-V1", "verdict": "TATG_PILOT_P3_CLOUD_PACKAGE_READY" if all(checks.values()) else "TATG_PILOT_P3_CLOUD_PACKAGE_NO_GO", "checks": checks, "details": details, "automatic_continuation": False}
    output.mkdir(parents=True)
    (output / "TATG_PILOT_P3_RESULT.json").write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    (output / "TATG_PILOT_P3_REPORT.md").write_bytes(("# TATG-MAPPO pilot P3 cloud-package audit\n\n**Verdict:** `" + result["verdict"] + "`.\n\nThe package is training-only and has not been launched.\n").encode("utf-8"))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
