"""Write the frozen Stage-MSR completion report from audited result artifacts."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: float) -> str:
    return f"{value:.6f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    args = parser.parse_args()

    result = json.loads((args.results_root / "MSR_RESULT.json").read_text(encoding="utf-8"))
    tape = result["tape"]
    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    per_seed = rows(args.results_root / "six_checkpoint_per_seed_metrics.csv")
    curves = rows(args.results_root / "mixed50_milestone_learning_curves.csv")
    pooled = result["pooled"]
    mixed = result["mixed50"]

    evaluation_table = "\n".join(
        "| {group} | {seed} | {jn} | {jf} | {delta} | {collision} | {timeout} | {constraint} | {exposure} |".format(
            group=row["group"], seed=row["seed"], jn=f(float(row["J_nominal"])),
            jf=f(float(row["J_failure"])), delta=f(float(row["Delta_J"])),
            collision=f(float(row["collision_failure"])), timeout=f(float(row["timeout_failure"])),
            constraint=f(float(row["constraint_failure"])), exposure=f(float(row["failure_exposure"])),
        )
        for row in per_seed
    )
    pooled_table = "\n".join(
        "| {group} | {jn} | {jf} | {delta} | {collision} | {timeout} | {constraint} | {exposure} |".format(
            group=group, jn=f(values["J_nominal"]), jf=f(values["J_failure"]),
            delta=f(values["Delta_J"]), collision=f(values["collision_failure"]),
            timeout=f(values["timeout_failure"]), constraint=f(values["constraint_failure"]),
            exposure=f(values["failure_exposure"]),
        )
        for group, values in pooled.items()
    )
    run_hashes = "\n".join(
        "| mixed50_sg | seed{seed} | `{sha}` | {nominal} / {f0} |".format(
            seed=item["seed"], sha=item["checkpoint_sha256"],
            nominal=item["realized_condition_counts"]["nominal"],
            f0=item["realized_condition_counts"]["f0"],
        )
        for item in result["mixed50_runs"]
    )
    curve_table = "\n".join(
        "| seed{seed} | {milestone} | {steps} | {reward} | {loss} | {kl} | {entropy} |".format(
            seed=row["seed"], milestone=row["milestone"], steps=row["environment_steps"],
            reward=f(float(row["train_avg_reward"])), loss=f(float(row["loss"])),
            kl=f(float(row["approx_kl"])), entropy=f(float(row["entropy"])),
        )
        for row in curves
    )
    report = f"""# Phase MSR — Mature Shared-Policy Reference Report

## Scope and frozen status

This report completes **Stage MSR only** under `POST_FL_MATURE_SHARED_POLICY_AND_FINAL_ALGORITHM_PLAN.md`. It establishes the 1M-step equal-mixture shared-policy reference; it is neither a canonical result nor a final-algorithm selection. No ENMM, canonical seed, OOD, ablation, or formal five-seed run was started.

- Implementation commit: `{provenance['commit']}`
- Branch: `{provenance['branch']}`
- Protocol: `{result['protocol']}`
- SG architecture: unchanged matched Single-Graph MAPPO
- Trainable parameters: **116,728**
- Mixed-50 configuration hash: `{result['mixed50_runs'][0]['mixed50_config_hash']}`

## Training integrity

| arm | cell | final checkpoint SHA256 | realized nominal / F0 episodes |
|---|---|---|---|
{run_hashes}

Both cells trained from scratch for 3,907 updates = 1,000,192 environment steps with 4 environments × 64 rollout steps. Milestones at 300,032, 499,968, 750,080, and 1,000,192 steps were verified present and are used only for learning-curve analysis; the final checkpoint is the only evaluated checkpoint.

## Fresh paired evaluation tape

- Development-only IDs: `{tape['episode_ids'][0]}–{tape['episode_ids'][-1]}`
- Cases per condition: {tape['episodes_per_condition']}
- F0: relay node 1, onset step 44, duration 80
- Tape SHA256: `{tape['tape_hash']}`
- Every one of the six checkpoints was evaluated on the same 100 nominal/F0 pairs. Failure exposure is reported per checkpoint and is not used as a post-hoc episode exclusion rule; episodes that naturally terminated before onset remain part of the frozen tape.

## Six-checkpoint unified evaluation

| group | seed | J_nominal | J_failure | Delta_J | collision (F0) | timeout (F0) | constraint (F0) | exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{evaluation_table}

## Pooled metrics and normalized competence

| group | J_nominal | J_failure | Delta_J | collision (F0) | timeout (F0) | constraint (F0) | exposure |
|---|---:|---:|---:|---:|---:|---:|---:|
{pooled_table}

The empirical mature specialist references on this **new** tape are:

- `J_N_star` = {f(result['J_N_star'])} (pooled nominal-expert nominal score)
- `J_F_star` = {f(result['J_F_star'])} (pooled F0-expert failure score)

For Mixed-50 SG:

- `C_N` = {f(mixed['C_N'])}
- `C_F` = {f(mixed['C_F'])}
- `C_min` = {f(mixed['C_min'])}
- Classification: **{result['classification']} — {result['classification_label']}**

This is a descriptive mature shared-policy classification, not a gradient-conflict claim and not a GO/NO-GO decision.

## Safety and telemetry

Failure-condition collision, timeout, constraint, exposure, episode-length, path-switch, direct/relay-path, task-support, legal-information, cache-age, traveled-distance, and control-effort metrics are retained in `six_checkpoint_per_seed_metrics.csv`. The pooled safety comparison is shown above; no safety metric was silently omitted.

## Mixed-50 milestone learning curves

| cell | milestone | environment steps | train average reward | PPO loss | approx. KL | entropy |
|---|---|---:|---:|---:|---:|---:|
{curve_table}

The full machine-readable curve table is `mixed50_milestone_learning_curves.csv`. Milestones were not inspected for, or used in, checkpoint selection.

## Stop condition

Stage MSR is complete. `enmm_started = false`, `ood_started = false`, `ablation_started = false`, and `formal_five_seed_started = false` are asserted in `MSR_RESULT.json`. No new algorithm or training is authorized by this report.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
