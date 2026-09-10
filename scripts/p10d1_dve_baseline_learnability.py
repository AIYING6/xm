#!/usr/bin/env python3
"""Baseline-only admission learnability gate; sealed test is never materialized."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn


def make_split(seed: int, size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    valid = rng.random(size) < 0.5
    elapsed = rng.uniform(0.2, 1.2, size)
    relative_error = np.empty(size)
    reserved = np.zeros(size, dtype=np.float32)

    valid_count = int(valid.sum())
    relative_error[valid] = rng.uniform(0.2, 1.9, valid_count)
    invalid_indices = np.flatnonzero(~valid)
    invalid_by_reservation = rng.random(len(invalid_indices)) < 0.5
    reserved[invalid_indices[invalid_by_reservation]] = 1.0
    relative_error[invalid_indices[invalid_by_reservation]] = rng.uniform(0.2, 1.9, invalid_by_reservation.sum())
    relative_error[invalid_indices[~invalid_by_reservation]] = rng.uniform(2.1, 3.8, (~invalid_by_reservation).sum())
    proposal = np.ones(size, dtype=np.float32)
    features = np.column_stack((elapsed, relative_error, reserved, proposal)).astype(np.float32)
    labels = valid.astype(np.float32)
    invalid_accept_value = np.where(reserved > 0, -10.0, -6.0).astype(np.float32)
    return features, labels, invalid_accept_value


class AdmissionMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def policy_value(actions: np.ndarray, labels: np.ndarray, invalid_accept: np.ndarray) -> float:
    values = np.where(
        actions,
        np.where(labels > 0.5, 8.0, invalid_accept),
        3.0,
    )
    return float(values.mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))

    train_x, train_y, _ = make_split(cfg["train_seed"], cfg["train_samples"])
    val_x, val_y, val_invalid = make_split(cfg["validation_seed"], cfg["validation_samples"])
    # The sealed split is represented only by a commitment to its generator inputs.
    sealed_commitment_payload = {
        "protocol": cfg["protocol"],
        "seed": cfg["sealed_test_seed"],
        "size": cfg["sealed_test_samples"],
        "generator": "make_split_v1",
    }
    sealed_commitment = hashlib.sha256(
        json.dumps(sealed_commitment_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    train_tensor = torch.from_numpy(train_x)
    train_labels = torch.from_numpy(train_y)
    val_tensor = torch.from_numpy(val_x)
    best_constant = max(
        policy_value(np.ones_like(val_y, dtype=bool), val_y, val_invalid),
        policy_value(np.zeros_like(val_y, dtype=bool), val_y, val_invalid),
    )

    seed_results = []
    for seed in cfg["model_seeds"]:
        torch.manual_seed(seed)
        model = AdmissionMLP(train_x.shape[1], cfg["model"]["hidden_dim"])
        optimizer = torch.optim.Adam(model.parameters(), lr=cfg["model"]["learning_rate"])
        criterion = nn.BCEWithLogitsLoss()
        for _ in range(cfg["model"]["epochs"]):
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(train_tensor), train_labels)
            loss.backward()
            optimizer.step()
        with torch.no_grad():
            probabilities = torch.sigmoid(model(val_tensor)).numpy()
        actions = probabilities >= 0.5
        accuracy = float(np.mean(actions == (val_y > 0.5)))
        accept_rate = float(actions.mean())
        value = policy_value(actions, val_y, val_invalid)
        lower, upper = cfg["gates"]["accept_rate_range"]
        passed = (
            accuracy >= cfg["gates"]["minimum_validation_accuracy"]
            and value - best_constant >= cfg["gates"]["minimum_validation_value_gain_over_best_constant"]
            and lower <= accept_rate <= upper
        )
        seed_results.append(
            {
                "model_seed": seed,
                "validation_accuracy": accuracy,
                "validation_accept_rate": accept_rate,
                "validation_mean_value": value,
                "gain_over_best_constant": value - best_constant,
                "passed": passed,
            }
        )

    passing = sum(row["passed"] for row in seed_results)
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P10D1_BASELINE_LEARNABILITY_PASS" if passing >= cfg["gates"]["minimum_passing_seeds"] else "P10D1_BASELINE_LEARNABILITY_STOP",
        "baseline": "generic_mlp_admission_only",
        "best_constant_validation_value": best_constant,
        "passing_seeds": passing,
        "required_passing_seeds": cfg["gates"]["minimum_passing_seeds"],
        "seed_results": seed_results,
        "sealed_test_commitment": sealed_commitment,
        "sealed_test_materialized": False,
        "sealed_test_evaluated": False,
        "candidate_method_implemented": False,
        "candidate_training_started": False,
        "scope": "admission baseline learnability only; no DVE performance claim",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
