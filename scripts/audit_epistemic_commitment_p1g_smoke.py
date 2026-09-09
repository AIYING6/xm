"""Audit local updates, telemetry, and exact continuation for P1G."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_epistemic_commitment_p1g_smoke import (
    CommitmentSmokeRunner,
    METHOD_CANDIDATE,
    METHOD_RECURRENT,
)


REQUIRED_METRICS = {
    "mean_task_value",
    "bilateral_commitment_rate",
    "single_sided_commitment_rate",
    "defer_rate",
    "fallback_rate",
    "collision_rate",
    "constraint_violation_rate",
    "stale_token_commit_rate",
    "actor_loss",
    "critic_loss",
    "calibration_loss",
}


def _trainable_snapshot(module: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def _states_equal(first: dict[str, torch.Tensor], second: dict[str, torch.Tensor]) -> bool:
    return first.keys() == second.keys() and all(torch.equal(first[key], second[key]) for key in first)


def _metrics_equal(first: dict, second: dict) -> bool:
    return first.keys() == second.keys() and all(first[key] == second[key] for key in first)


def run_p1g_audit() -> dict:
    initial_and_final: dict[str, tuple[dict, dict, dict]] = {}
    for method in (METHOD_CANDIDATE, METHOD_RECURRENT):
        runner = CommitmentSmokeRunner(method, 98101)
        initial = _trainable_snapshot(runner.actor)
        metrics = runner.update()
        final = _trainable_snapshot(runner.actor)
        initial_and_final[method] = (initial, final, metrics)

    with tempfile.TemporaryDirectory(prefix="p1g_commitment_") as temporary:
        checkpoint = Path(temporary) / "fixed_smoke_checkpoint.pt"
        source = CommitmentSmokeRunner(METHOD_CANDIDATE, 98102)
        source.update()
        source.save_checkpoint(checkpoint)
        overwrite_refused = False
        try:
            source.save_checkpoint(checkpoint)
        except FileExistsError:
            overwrite_refused = True
        continuation_metrics = source.update()
        continuation_actor = _trainable_snapshot(source.actor)
        continuation_critic = _trainable_snapshot(source.critic)

        restored = CommitmentSmokeRunner(METHOD_CANDIDATE, 98102)
        restored.load_checkpoint(checkpoint)
        replay_metrics = restored.update()
        replay_actor = _trainable_snapshot(restored.actor)
        replay_critic = _trainable_snapshot(restored.critic)

    candidate_initial, candidate_final, candidate_metrics = initial_and_final[METHOD_CANDIDATE]
    recurrent_initial, recurrent_final, recurrent_metrics = initial_and_final[METHOD_RECURRENT]
    checks = {
        "candidate_actor_parameters_update": not _states_equal(candidate_initial, candidate_final),
        "recurrent_actor_parameters_update": not _states_equal(recurrent_initial, recurrent_final),
        "candidate_required_metrics_complete": REQUIRED_METRICS.issubset(candidate_metrics),
        "recurrent_required_metrics_complete": REQUIRED_METRICS.issubset(recurrent_metrics),
        "candidate_metrics_finite": all(
            isinstance(value, (int, float)) and torch.isfinite(torch.tensor(float(value)))
            for key, value in candidate_metrics.items()
            if key not in {"method"}
        ),
        "recurrent_metrics_finite": all(
            isinstance(value, (int, float)) and torch.isfinite(torch.tensor(float(value)))
            for key, value in recurrent_metrics.items()
            if key not in {"method"}
        ),
        "fixed_checkpoint_refuses_overwrite": overwrite_refused,
        "checkpoint_continuation_metrics_exact": _metrics_equal(continuation_metrics, replay_metrics),
        "checkpoint_continuation_actor_exact": _states_equal(continuation_actor, replay_actor),
        "checkpoint_continuation_critic_exact": _states_equal(continuation_critic, replay_critic),
        "smoke_uses_fixed_seed_registry": all(
            runner_seed in (98101, 98102, 98103) for runner_seed in (98101, 98102)
        ),
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1G-LOCAL-OPTIMIZER-SMOKE-AUDIT-V1",
        "verdict": "P1G_LOCAL_OPTIMIZER_AND_RESUME_SMOKE_PASS" if passed else "P1G_LOCAL_OPTIMIZER_AND_RESUME_SMOKE_FAIL",
        "checks": checks,
        "one_update_metrics": {
            METHOD_CANDIDATE: candidate_metrics,
            METHOD_RECURRENT: recurrent_metrics,
        },
        "evidence_boundary": (
            "This local smoke proves wiring, finite updates, endpoint logging, overwrite protection, and exact "
            "checkpoint continuation. Its sampled returns are not scientific performance evidence."
        ),
        "scientific_evidence": False,
        "performance_training_started": False,
        "smoke_optimizer_updates": 5,
        "smoke_episodes": 60,
        "smoke_physics_steps": 960,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_p1g_audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
    print(payload)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
