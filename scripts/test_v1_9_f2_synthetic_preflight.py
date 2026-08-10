"""Synthetic-only F2 input-layout smoke test.

This test intentionally has no import from the environment or evaluator.  It
checks only the bookkeeping invariant required for an eventual F2 evaluation:
every frozen checkpoint receives the same ordered paired episode identifiers.
No real F2 seed, generator, checkpoint, result, or training artifact is read.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path


METHODS = ("pcrf_r2", "single_r2", "matched_nongraph_r2")
FORMAL_SEEDS = tuple(range(8))
SYNTHETIC_EPISODES = tuple(f"synthetic-{index:03d}" for index in range(300))
SYNTHETIC_SELECTED_UPDATES = (120, 180, 240, 300)


def synthetic_selection_manifest() -> dict:
    selections = []
    for method in METHODS:
        for seed in FORMAL_SEEDS:
            selected_update = SYNTHETIC_SELECTED_UPDATES[seed % len(SYNTHETIC_SELECTED_UPDATES)]
            selections.append(
                {
                    "method": method,
                    "seed": seed,
                    "selected_update": selected_update,
                    "selected_checkpoint_sha256": hashlib.sha256(
                        f"synthetic:{method}:{seed}".encode("utf-8")
                    ).hexdigest(),
                }
            )
    return {"confirmatory_heldout_accessed": False, "selections": selections}


def build_synthetic_plan(manifest: dict) -> dict:
    selections = manifest["selections"]
    expected = {(method, seed) for method in METHODS for seed in FORMAL_SEEDS}
    observed = {(row["method"], int(row["seed"])) for row in selections}
    if observed != expected or len(selections) != len(expected):
        raise AssertionError("synthetic F1 selection manifest is not 3 methods x 8 seeds")
    if manifest.get("confirmatory_heldout_accessed") is not False:
        raise AssertionError("synthetic manifest incorrectly marks confirmatory access")
    return {
        "mode": "SYNTHETIC_ONLY",
        "episodes_per_checkpoint": len(SYNTHETIC_EPISODES),
        "paired_episode_ids": list(SYNTHETIC_EPISODES),
        "checkpoint_plans": [
            {
                "method": row["method"],
                "training_seed": row["seed"],
                "checkpoint_sha256": row["selected_checkpoint_sha256"],
                "episode_ids": list(SYNTHETIC_EPISODES),
            }
            for row in selections
        ],
    }


def main() -> None:
    manifest = synthetic_selection_manifest()
    plan = build_synthetic_plan(manifest)
    with tempfile.TemporaryDirectory(prefix="v1_9_f2_synthetic_") as directory:
        output = Path(directory) / "synthetic_plan.json"
        output.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
        loaded = json.loads(output.read_text(encoding="utf-8"))
        assert loaded["mode"] == "SYNTHETIC_ONLY"
        assert loaded["episodes_per_checkpoint"] == 300
        assert len(loaded["checkpoint_plans"]) == 24
        assert all(row["episode_ids"] == list(SYNTHETIC_EPISODES) for row in loaded["checkpoint_plans"])
        assert {
            row["selected_update"] for row in manifest["selections"]
        } == set(SYNTHETIC_SELECTED_UPDATES)
        assert not any("results" in str(value).lower() for value in loaded.values())
    print("F2_SYNTHETIC_PREFLIGHT_PASS: 24 checkpoint plans x 300 paired synthetic episodes")


if __name__ == "__main__":
    main()
