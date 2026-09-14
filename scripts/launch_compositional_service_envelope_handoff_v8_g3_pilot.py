"""Launch the frozen V8 relation-value development pilot.

The script intentionally has no parameter sweep and no fallback task settings.
It creates exactly nine runs: three fixed development seeds times the ordinary,
aligned, and semantic-shuffle arms registered in the G3 freeze contract.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "configs" / "commitment_handoff_v8_relation_value_g3_pilot_freeze_20260914.json"
RUNNER = ROOT / "scripts" / "run_compositional_service_envelope_handoff_plain_mappo.py"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this launches development training")
    if args.out_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_root}")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    args.out_root.mkdir(parents=True)
    (args.out_root / "pilot_freeze_contract.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    task = contract["frozen_task"]
    budget = contract["fixed_training_budget"]
    for arm, arm_spec in contract["arms"].items():
        for seed in contract["training_seeds"]:
            out_dir = args.out_root / arm / f"seed{seed}"
            command = [
                args.python, str(RUNNER), "--seed", str(seed), "--updates", str(budget["updates"]),
                "--num-envs", str(budget["num_envs"]), "--rollout-steps", str(budget["rollout_steps"]),
                "--hidden-dim", str(arm_spec["hidden_dim"]), "--entropy-coef", str(budget["entropy_coef"]),
                "--initial-retain-logit-bias", str(budget["initial_retain_logit_bias"]),
                "--selection-eval-episodes", str(budget["selection_eval_episodes"]),
                "--endpoint-episodes-per-profile", str(budget["endpoint_episodes_per_profile"]),
                "--service-envelope-mode", task["service_envelope_mode"],
                "--future-corridor-lateral-offset", str(task["future_corridor_lateral_offset"]),
                "--branch-step", str(task["branch_step"]),
                "--authorization-start-step", str(task["authorization_start_step"]),
                "--authorization-deadline", str(task["authorization_deadline"]),
                "--authorization-decision-step", str(task["authorization_decision_step"]),
                "--commitment-decision-mode", task["commitment_decision_mode"],
                "--handoff-safety-mode", task["handoff_safety_mode"],
                "--relation-value-mode", arm_spec["relation_value_mode"], "--device", args.device,
                "--out-dir", str(out_dir), "--execute",
            ]
            print("LAUNCH", " ".join(command))
            subprocess.run(command, check=True, cwd=ROOT)
    print(f"COMPLETE: frozen G3 pilot at {args.out_root}")


if __name__ == "__main__":
    main()
