"""UTR-only V3.1 qualification, reusing V3 learner code under frozen V3.1 semantics."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_drtp_6uav_v3_utr_pilot as core
from scripts.run_drtp_6uav_v31_q0 import GROUPS, fault_spec, make_env

PROTOCOL = "DRTP-6UAV-V31-UTR-LEARNABILITY-PILOT-V1"
SEEDS = (95011, 95012, 95013)


def configure_core() -> None:
    """Reuse the exact PPO implementation; patch only frozen task bindings."""
    core.PROTOCOL = PROTOCOL
    core.SEEDS = SEEDS
    core.GROUPS = GROUPS
    core.make_env = make_env

    def fault(env, group):
        if group != "nominal" and env.step_count == env.semantic_config.fault_transition - 1:
            spec = fault_spec(env, group); env.set_failure(spec["edges"], spec["nodes"])
    core.fault = fault


def aggregate(root: Path) -> None:
    """V3.1-labelled endpoint aggregation; episodes are not training repeats."""
    files = [root / "evaluations" / f"seed{seed}_final.csv" for seed in SEEDS]
    if not all(path.is_file() for path in files):
        raise RuntimeError("missing fixed-endpoint V3.1 pilot evaluation")
    rows = [row for path in files for row in csv.DictReader(path.open(encoding="utf-8"))]
    summary = []
    for seed in SEEDS:
        for group in GROUPS:
            values = [row for row in rows if int(row["seed"]) == seed and row["group"] == group]
            summary.append({"seed": seed, "group": group, "mean_score": float(np.mean([float(x["score"]) for x in values])), "success": float(np.mean([float(x["success"]) for x in values])), "timeout": float(np.mean([float(x["timeout"]) for x in values])), "collision": float(np.mean([float(x["collision"]) for x in values]))})
    nominal = [row["success"] for row in summary if row["group"] == "nominal"]
    perturbed = [row["success"] for row in summary if row["group"] != "nominal"]
    checks = {"nominal_learnable_two_of_three": sum(x >= .50 for x in nominal) >= 2, "perturbed_not_ceiling": float(np.mean(perturbed)) < .90, "perturbed_not_global_failure": float(np.mean(perturbed)) > .10}
    payload = {"protocol": PROTOCOL, "verdict": "V31_UTR_LEARNABILITY_PILOT_PASS" if all(checks.values()) else "V31_UTR_LEARNABILITY_PILOT_FAIL", "training_seeds": SEEDS, "fixed_endpoint_updates": core.UPDATES, "checks": checks, "summary": summary, "drtp_training_started": False, "automatic_continuation": False}
    diag = root / "diagnostics"; diag.mkdir(parents=True, exist_ok=True)
    with (diag / "V31_UTR_PILOT_ENDPOINTS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    (diag / "V31_UTR_PILOT_VERDICT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (diag / "V31_UTR_PILOT_REPORT.md").write_text("# V3.1 UTR learnability pilot\n\n`" + payload["verdict"] + "`\n\nThis UTR-only qualification does not compare DRTP or authorize a manuscript claim.\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("train", "evaluate", "aggregate")); parser.add_argument("--seed", type=int, choices=SEEDS); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute required")
    if args.mode in {"train", "evaluate"} and args.seed is None: raise SystemExit("--seed required")
    configure_core()
    device = core.torch.device("cuda" if core.torch.cuda.is_available() else "cpu")
    if args.mode == "train":
        core.train(args.output_root, args.seed, device)
        print(json.dumps({"protocol": PROTOCOL, "status": "completed", "seed": args.seed, "drtp_training_started": False}))
    elif args.mode == "evaluate": core.evaluate(args.output_root, args.seed, device)
    else: aggregate(args.output_root)


if __name__ == "__main__": main()
