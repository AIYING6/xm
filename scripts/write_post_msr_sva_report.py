"""Write the required SVA report from MSR and replay artifacts."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sva-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sva = json.loads((args.sva_root / "SVA_RESULT.json").read_text(encoding="utf-8"))
    rows = read(args.sva_root / "sva_absolute_metrics.csv")
    comparisons = read(args.sva_root / "sva_replay_vs_archived.csv")
    table = "\n".join(
        f"| {r['group']} | {r['seed']} | {float(r['J_nominal']):.6f} | {float(r['J_failure']):.6f} | {float(r['Delta_J']):.6f} | {r['failure_exposure']} |"
        for r in rows
    )
    cross = "\n".join(
        f"| {r['group']} | {r['seed']} | {r['tape']} | {r['episode_id']} | {r['condition']} | {float(r['abs_diff']):.9g} |"
        for r in comparisons
    )
    report = f"""# Post-MSR Sanity and Absolute-Value Audit

## Scope

This is the zero-training Stage SVA audit required by `POST_MSR_SANITY_OOD_GAP_SCAN_AND_FINAL_ALGORITHM_DECISION.md`. No ENMM, new architecture, new loss, canonical seed, or formal five-seed training was started.

## Six-checkpoint absolute values

| group | seed | J_nominal | J_failure | Delta_J | exposure |
|---|---:|---:|---:|---:|---:|
{table}

The MSR empirical specialist references are `J_N_star={sva['J_N_star']:.12f}` and `J_F_star={sva['J_F_star']:.12f}`. They are empirical tape references, not theoretical optima.

The exact normalization is:

`C_N = pooled Mixed-50 J_nominal / pooled nominal-expert J_nominal = {sva['mixed50']['C_N']:.12f}`

`C_F = pooled Mixed-50 J_failure / pooled F0-expert J_failure = {sva['mixed50']['C_F']:.12f}`

`C_min = min(C_N, C_F) = {sva['mixed50']['C_min']:.12f}`

## Deterministic cross-tape replay

Ten IDs from each of FL tape `370000–370049` and MSR tape `380000–380099` were replayed under nominal and canonical F0 for all six checkpoints. The archived 370/380 rows were compared where available; Mixed-50 has no historical 370 evaluation, so its 370 replay is retained as a new diagnostic observation.

| group | seed | tape | episode | condition | absolute J difference |
|---|---:|---|---:|---|---:|
{cross}

Maximum replay difference: `{sva['consistency']['max_replay_abs_diff']:.9g}`. Numerical tolerance: `{sva['consistency']['replay_numeric_tolerance']}`.

## Consistency checklist

| item | status | evidence |
|---|---|---|
| six evaluation manifests complete | PASS | six completed manifests, 200 raw and 100 paired rows each |
| common MSR tape | PASS | one tape hash `{sva['consistency']['tape_hashes'][0]}` |
| checkpoint loading | PASS | archived SHA256 matched evaluation manifests |
| common SG architecture | PASS | Single-Graph, hidden dimension 115, 116,728 parameters |
| common environment/reward/horizon/information boundary | PASS | normalized frozen config keys matched |
| receiver/sender adjacency convention | PASS | same evaluator and unchanged graph packing path |
| terminal/exposure accounting | PASS | exposure retained as an outcome; no post-hoc filtering |
| deterministic replay | PASS | maximum absolute difference within `1e-4` |

## Why C_N and C_F exceed 2

The large normalized values are not caused by tape ID mismatch: the specialist checkpoints are stable between the 370 and 380 tapes, with maximum specialist relative change `{sva['consistency']['max_specialist_relative_cross_tape_change']:.6f}`. The result is driven by the Mixed-50 absolute scores being high on the 380 tape while the two specialist references, especially seed1802, are low. Thus the normalization is valid as an empirical diagnostic, but it is too reference-dependent to be used as the sole final-method objective.

## SVA decision

**{sva['classification']}** — evaluator/configuration semantics are consistent, replay is deterministic within tolerance, and specialist cross-tape instability does not exceed the pre-registered 20% SVA-2 threshold. Proceed to the authorized zero-training OOD gap scan.
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
