"""Zero-training M1 preflight for C2's telemetry-only diagnostic interface."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TELEMETRY = ROOT / "algorithms" / "ri_gmappo" / "group_credit_telemetry.py"
TRAINER = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
TEST = "tests/test_drtp_b5_group_credit_telemetry.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def no_mutation_calls(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"backward", "step", "zero_grad"}
    return not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in forbidden
        for node in ast.walk(tree)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise RuntimeError("--execute is required")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_dir}")

    source = TELEMETRY.read_text(encoding="utf-8")
    trainer = TRAINER.read_text(encoding="utf-8")
    checks = {
        "three_new_scalar_fields": all(field in source for field in (
            '"clipped_surrogate_mean"', '"entropy_bonus_mean"', '"actor_loss_mean"'
        )),
        "uses_existing_preupdate_expressions": all(token in source for token in (
            "clipped_surrogate_per_graph", "entropy_bonus_per_graph", "actor_per_graph"
        )),
        "telemetry_module_has_no_mutating_calls": no_mutation_calls(TELEMETRY),
        "telemetry_default_off": "group_credit_telemetry: bool = False" in trainer,
        "collection_precedes_ppo_update": trainer.index("summarize_group_credit_assignment(") < trainer.index("train_info = update_policy("),
        "no_tape_argument": "evaluation_tape:" not in trainer and "formal_evaluation_tape:" not in trainer,
        "runtime_checkpoint_support": "actor_critic_runtime_state_milestone_" in trainer,
    }
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TEST], cwd=ROOT, text=True, capture_output=True
    )
    passed = all(checks.values()) and completed.returncode == 0
    verdict = "C2_M1_TELEMETRY_READY" if passed else "C2_M1_TELEMETRY_NOT_READY"
    payload = {
        "protocol": "C2-M1-TELEMETRY-PREFLIGHT-V1",
        "verdict": verdict,
        "checks": checks,
        "pytest": {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr},
        "training_started": False,
        "evaluation_started": False,
        "algorithm_modification": False,
        "mainline_a_modified": False,
        "next_step_authorized": False,
        "required_future_preflight": "benchmark telemetry-on wall-clock and disk growth before any fresh-seed diagnostic run",
    }
    write(args.output_dir / "C2_M1_TELEMETRY_PREFLIGHT.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    report = [
        "# C2-M1 telemetry technical preflight", "", f"**Verdict:** `{verdict}`.", "",
        "This is a zero-training, zero-evaluation verification. The three added scalars are observational outputs from the existing pre-update PPO calculation; no sampling, reward, PPO objective, optimizer step, or actor action path was changed.", "",
        "| Check | Result |", "| --- | --- |",
        *[f"| {name} | `{'PASS' if value else 'FAIL'}` |" for name, value in checks.items()],
        f"| targeted pytest | `{'PASS' if completed.returncode == 0 else 'FAIL'}` |", "",
        "No fresh-seed diagnostic run is authorized by this preflight. Before any such authorization, the cloud preflight must benchmark telemetry-on wall-clock and disk growth, preserve the fixed milestone plan, and keep all telemetry out of online training control.",
    ]
    write(args.output_dir / "C2_M1_TELEMETRY_PREFLIGHT.md", "\n".join(report) + "\n")
    print(json.dumps({"verdict": verdict, "output": str(args.output_dir)}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
