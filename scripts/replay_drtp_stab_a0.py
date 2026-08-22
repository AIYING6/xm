"""Offline-only DRTP A0 replay characterization.

This script transforms recorded sampler trajectories only. It does not load a
model, environment, optimizer, or checkpoint and cannot affect a policy.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
UNIFORM = [1.0 / len(GROUPS)] * len(GROUPS)
Q_MIN, Q_MAX = 0.05, 0.35


def bounded_simplex(values: list[float]) -> list[float]:
    low, high = min(value - Q_MAX for value in values), max(value - Q_MIN for value in values)
    for _ in range(100):
        middle = (low + high) / 2.0
        total = sum(min(Q_MAX, max(Q_MIN, value - middle)) for value in values)
        if total > 1.0:
            low = middle
        else:
            high = middle
    projected = [min(Q_MAX, max(Q_MIN, value - high)) for value in values]
    residual = 1.0 - sum(projected)
    for index, value in enumerate(projected):
        if abs(residual) < 1e-12:
            break
        room = Q_MAX - value if residual > 0 else value - Q_MIN
        delta = math.copysign(min(abs(residual), max(0.0, room)), residual)
        projected[index] += delta
        residual -= delta
    return projected


def load(path: Path) -> tuple[list[int], list[list[float]], list[list[float]]]:
    updates, weights, difficulties = [], [], []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("record_type") != "weight_update":
                continue
            updates.append(int(row["update"]))
            weights.append([float(row[f"q_{group}"]) for group in GROUPS])
            difficulties.append([float(row[f"difficulty_{group}"]) for group in GROUPS])
    return updates, weights, difficulties


def l1(left: list[float], right: list[float]) -> float:
    return sum(abs(a - b) for a, b in zip(left, right))


def metrics(vectors: list[list[float]]) -> tuple[float, float, float]:
    jumps = [l1(now, previous) for previous, now in zip(vectors, vectors[1:])]
    return (
        sum(jumps) / len(jumps),
        sum(jumps),
        sum(l1(vector, UNIFORM) for vector in vectors) / len(vectors),
    )


def difficulty_ema(difficulties: list[list[float]]) -> list[list[float]]:
    """Characterization-only beta=0.8 replay using frozen 0.5 base smoothing."""
    output, prior, state = [], UNIFORM[:], None
    for difficulty in difficulties:
        state = difficulty[:] if state is None else [0.8 * old + 0.2 * new for old, new in zip(state, difficulty)]
        centered = [value - sum(state) / len(state) for value in state]
        logits = [value * math.exp(logit) for value, logit in zip(prior, centered)]
        normalizer = sum(logits)
        candidate = [value / normalizer for value in logits]
        prior = bounded_simplex([0.5 * old + 0.5 * new for old, new in zip(prior, candidate)])
        output.append(prior[:])
    return output


def inertial(weights: list[list[float]]) -> list[list[float]]:
    output, state = [], weights[0][:]
    for target in weights:
        state = [0.5 * old + 0.5 * new for old, new in zip(state, target)]
        output.append(state[:])
    return output


def trust_region(weights: list[list[float]], radius: float = 0.05) -> list[list[float]]:
    output, state = [], weights[0][:]
    for target in weights:
        distance = l1(target, state)
        scale = min(1.0, radius / distance) if distance else 1.0
        state = [old + scale * (new - old) for old, new in zip(state, target)]
        output.append(state[:])
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline-only DRTP A0 replay characterization")
    parser.add_argument("--seed-log", action="append", default=[], metavar="SEED=CSV")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for item in args.seed_log:
        seed, separator, value = item.partition("=")
        if not separator:
            raise ValueError("--seed-log requires SEED=CSV")
        _, weights, difficulties = load(Path(value))
        transforms = {
            "original": weights,
            "R1_difficulty_ema_beta_0.8": difficulty_ema(difficulties),
            "R2_inertial_alpha_0.5": inertial(weights),
            "R3_trust_region_l1_0.05": trust_region(weights),
        }
        original_mean, original_tv, _ = metrics(weights)
        for name, vectors in transforms.items():
            mean_jump, total_variation, distance_to_uniform = metrics(vectors)
            rows.append({
                "seed": seed,
                "replay": name,
                "mean_l1_step": mean_jump,
                "total_variation": total_variation,
                "mean_l1_distance_to_utr": distance_to_uniform,
                "variation_fraction_of_original": total_variation / original_tv if original_tv else float("nan"),
                "updates": len(vectors),
            })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["seed", "replay"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
