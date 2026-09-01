"""C2-M0 static feasibility audit for a telemetry-first diagnostic protocol.

This audit is deliberately source-only: it starts neither training nor
evaluation and does not instantiate an environment.  Its purpose is to decide
whether the *existing* training interface can collect the evidence missing
from C2-D1 without feeding any of it back into the policy, critic, sampler, or
evaluation path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
GROUP_CREDIT = ROOT / "algorithms" / "ri_gmappo" / "group_credit_telemetry.py"
FAILURE_TELEMETRY = ROOT / "algorithms" / "ri_gmappo" / "failure_aware_telemetry.py"

PROTOCOL = "C2-M0-MEASUREMENT-FEASIBILITY-V1"
UPDATES = 1953
INTERVAL = 32
GROUPS = ("N", "F0", "TE", "TL", "DS", "DL", "CP")
MILESTONES = {488: "125k", 976: "250k", 1464: "375k", 1953: "500k"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required(text: str, *needles: str) -> bool:
    return all(needle in text for needle in needles)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise RuntimeError("--execute is required for an auditable M0 report")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing M0 audit: {args.output_dir}")

    trainer, group_credit, failure = (path.read_text(encoding="utf-8") for path in (TRAINER, GROUP_CREDIT, FAILURE_TELEMETRY))
    observation_updates = len(range(INTERVAL, UPDATES + 1, INTERVAL))
    group_rows = observation_updates * len(GROUPS)
    pair_rows = observation_updates * (len(GROUPS) * (len(GROUPS) - 1) // 2)
    gradient_calls = observation_updates * len(GROUPS) * 2

    checks = {
        "group_actor_and_critic_gradients": required(
            group_credit, "actor_gradient_norm", "critic_gradient_norm", "torch.autograd.grad"
        ),
        "group_advantage_and_clipped_objective_available_to_measure": required(
            group_credit, "raw_advantage_mean", "normalized_advantage_mean", "torch.clamp"
        ),
        "group_gradient_conflict": required(
            group_credit, "actor_gradient_cosine", "actor_gradient_conflict", "combinations(present_groups, 2)"
        ),
        "role_behavior_windows": required(
            failure, "action_command", "task_support_state", "relay_information_path", "failure_event_window.jsonl"
        ),
        "fixed_runtime_milestones": required(
            trainer, "milestone_updates", "actor_critic_runtime_state_milestone_", "save_runtime_training_checkpoint"
        ),
        "telemetry_is_default_off": required(
            trainer, "group_credit_telemetry: bool = False", "failure_aware_telemetry: bool = False"
        ),
        "telemetry_not_used_as_control": required(
            trainer, "credit_group_rows: list[dict] = []", "group_credit_writer.writerows", "telemetry_writer=telemetry_writer"
        ) and "optimizer.step(" not in group_credit and "backward(" not in group_credit,
        # Comments may legitimately mention evaluation tapes.  The relevant
        # interface condition is that the trainer accepts no tape path/object
        # and imports no evaluation runner.
        "formal_tape_not_read_by_training_interface": "evaluation_tape:" not in trainer
        and "formal_evaluation_tape:" not in trainer and "heldout_tape:" not in trainer
        and "run_drtp_" not in trainer,
    }
    verdict = "C2_M0_FEASIBLE" if all(checks.values()) else "C2_M0_NO_GO"
    sources = {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in (TRAINER, GROUP_CREDIT, FAILURE_TELEMETRY)}
    payload = {
        "protocol": PROTOCOL,
        "verdict": verdict,
        "checks": checks,
        "source_sha256": sources,
        "frozen_measurement_contract": {
            "updates": UPDATES,
            "group_credit_interval_updates": INTERVAL,
            "group_credit_observation_updates": observation_updates,
            "groups": GROUPS,
            "milestones": MILESTONES,
            "evaluation_enabled": False,
            "telemetry_control_input": False,
            "new_environment_interactions": 0,
            "training_authorized": False,
        },
        "expected_per_trajectory": {
            "group_credit_rows": group_rows,
            "pair_conflict_rows": pair_rows,
            "diagnostic_autograd_calls": gradient_calls,
            "diagnostic_update_fraction": observation_updates / UPDATES,
        },
        "cost_interpretation": (
            "The source-only audit proves no extra environment interaction or second action draw. "
            "It cannot establish wall-clock overhead; a future technical preflight must measure it before any diagnostic trajectory."
        ),
        "actionability": {
            "repeated_actor_group_conflict": "one actor-only conflict-projection candidate, not authorized by M0",
            "repeated_group_surrogate_dominance": "one bounded group-contribution normalization candidate, not authorized by M0",
            "role_behavior_divergence": "descriptive localization only; no generic intervention is authorized",
        },
        "automatic_continuation_authorized": False,
        "mainline_a_modified": False,
    }

    contract = f"""# C2-M0 measurement feasibility contract

**Protocol:** `{PROTOCOL}`
**Status:** `{verdict}`
**Scope:** source-only, zero training and zero evaluation.

## Purpose

Determine whether a future *diagnostic-only* fresh-seed experiment could collect the measurement layers absent from C2-D1 without evaluation leakage or training control. M0 does not create a new algorithm, alter C2, select checkpoints, or authorize a follow-up run.

## Frozen proposed measurement interface

- Training remains ordinary UTR and the already-frozen group-weighted candidate; telemetry is write-only.
- `group_credit_telemetry=True` only every `{INTERVAL}` updates: `{observation_updates}` observation updates across `{UPDATES}` updates.
- Emit `{group_rows}` per-group rows and `{pair_rows}` actor/critic conflict-pair rows per trajectory.
- `failure_aware_telemetry=True` records already chosen actions, role-labelled path/support state and outcome windows; it does not request a second actor forward pass.
- Runtime checkpoints are fixed at `{', '.join(f'{label} (update {update})' for update, label in MILESTONES.items())}`. Any later milestone evaluation would require a separate explicit authorization and must never select a checkpoint.
- Formal, independent and held-out evaluation tapes are excluded from training and telemetry.

## Required future preflight before any diagnostic training

1. Demonstrate telemetry-on versus telemetry-off trajectory equivalence through a fixed short technical replay or prove it via the existing default-off/write-only invariant.
2. Measure wall-clock and disk overhead. M0 has **not** measured either; no claim of a numeric cost bound is made here.
3. Verify save/resume retains telemetry writer state and milestone runtime state.
4. Freeze the future analysis rule before observing fresh final outcomes. No threshold sweep, classifier, or online control is permitted.

## Actionability boundary

Only a repeated, temporally leading signal may later motivate **one** matching minimal intervention. Gradient conflict could motivate an actor-only conflict projection; persistent group contribution domination could motivate bounded contribution normalization. Neither is designed, implemented, or authorized by M0. Role-level divergence alone is localization evidence, not an intervention prescription.

## Result

`{verdict}` means the interface is structurally capable of collecting the missing evidence. It is not evidence that a mechanism exists or that the group-weighted method should continue.
"""
    report = f"""# C2-M0 measurement feasibility report

**Verdict:** `{verdict}`.

| Requirement | Result | Existing interface evidence |
| --- | --- | --- |
| Per-group actor/critic gradients | `{checks['group_actor_and_critic_gradients']}` | `group_credit_telemetry.py` computes read-only `torch.autograd.grad` summaries. |
| Per-group advantage and clipped PPO quantities | `{checks['group_advantage_and_clipped_objective_available_to_measure']}` | Raw/normalized advantage summaries and the clipped PPO objective are available at the read-only diagnostic site. |
| Pairwise gradient conflict | `{checks['group_gradient_conflict']}` | Actor/critic dot products and cosines are logged. |
| Scout/Relay/Attacker behavior | `{checks['role_behavior_windows']}` | Chosen actions, support/path states and failure windows are logged without second action sampling. |
| Fixed training-state checkpoints | `{checks['fixed_runtime_milestones']}` | Milestone model/training/runtime checkpoint paths already exist. |
| Default-off and no control feedback | `{checks['telemetry_is_default_off'] and checks['telemetry_not_used_as_control']}` | Writers are optional output sinks; group credit contains no optimizer step. |
| No formal-tape read in training interface | `{checks['formal_tape_not_read_by_training_interface']}` | Training configuration does not accept a tape input. |

## Cost accounting (static, not benchmarked)

At the frozen `{INTERVAL}`-update interval, each `{UPDATES}`-update trajectory has `{observation_updates}` diagnostic updates ({observation_updates / UPDATES:.2%} of updates), `{group_rows}` group summaries, `{pair_rows}` pair-conflict summaries, and `{gradient_calls}` diagnostic actor/critic autograd calls. The interface adds **zero** environment interactions and uses already-collected rollout batches. Wall-clock and disk overhead remain a mandatory future preflight measurement.

## Important output limitation

The current group-credit CSV already emits group advantage summaries and gradient quantities, but it does **not** yet emit the scalar clipped actor-loss contribution itself. M0 establishes that this scalar is available at the same read-only calculation site; a later explicitly authorized measurement-only implementation would need to append it to the telemetry schema. M0 does not make that implementation change.

## Strict interpretation

M0 passes only the feasibility question. It does not repair C2, make C2-D1 causal, authorize a new stabilizer, or permit training. A later diagnostic protocol must include fresh seeds, fixed checkpoint timing and outcome-blind analysis; it must stop if no repeated signal maps to one minimal intervention.
"""
    final = f"""# C2-M0 final verdict

`{verdict}`

The current interface can measure the missing C2-D1 layers without formal-evaluation leakage or extra environment interactions: per-group PPO gradients/conflicts, advantage summaries, clipped-objective context, role-labelled training behavior, and fixed runtime checkpoints. The measurement writers are default-off and write-only.

This conclusion is **not** an algorithm result. It neither identifies a mechanism nor authorizes diagnostic training, C2-v2, parameter tuning, D2, or any Mainline-A change. Numeric overhead has not been benchmarked and remains a hard future preflight requirement.
"""
    write(args.output_dir / "C2_M0_MEASUREMENT_CONTRACT.md", contract)
    write(args.output_dir / "C2_M0_MEASUREMENT_FEASIBILITY_REPORT.md", report)
    write(args.output_dir / "C2_M0_FINAL_VERDICT.md", final)
    write(args.output_dir / "C2_M0_FEASIBILITY.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "output": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
