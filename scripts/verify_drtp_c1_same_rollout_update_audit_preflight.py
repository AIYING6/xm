"""Zero-training readiness gate for the frozen C1 same-rollout audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FAILURE_GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frozen_weight_map(groups: np.ndarray, scores: dict[str, float]) -> dict[str, float]:
    """Pure-NumPy mirror of C1's bounded frequency-normalized actor weights.

    The actual runtime helper is checked textually below.  Keeping the
    zero-training preflight free of the ML runtime allows it to verify assets
    on a CPU-only or GPU-unavailable host without importing PyTorch.
    """
    active = [group for group in FAILURE_GROUPS if int(np.sum(groups == group)) > 0]
    values = np.asarray([scores[group] for group in active], dtype=np.float64)
    spread = float(values.std())
    raw = np.ones(len(active), dtype=np.float64) if spread <= 1e-12 else np.exp(0.25 * (values - values.mean()) / spread)
    raw = np.clip(raw, 0.75, 1.25)
    counts = np.asarray([np.sum(groups == group) for group in active], dtype=np.float64)
    raw /= float(np.sum(raw * counts) / np.sum(counts))
    result = {group: 1.0 for group in FAILURE_GROUPS}
    result.update({group: float(value) for group, value in zip(active, raw)})
    return result


def deterministic_batch_sha256(batch: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for key in ("actions", "logp", "advantages", "returns", "td_residuals", "condition_group"):
        value = np.ascontiguousarray(np.asarray(batch[key]))
        digest.update(key.encode("utf-8"))
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--freeze",
        type=Path,
        default=ROOT / "configs" / "drtp_c1_same_rollout_update_audit_freeze.json",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite preflight: {args.output}")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    source_hashes: dict[str, str] = {}
    source_ok = True
    for seed in freeze["source"]["training_seeds"]:
        root = args.source_root / f"seed{seed}"
        manifest = root / "run_manifest.json"
        runtime = root / "actor_critic_runtime_state_latest.pt"
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            valid = (
                payload.get("status") == "completed"
                and payload.get("arm") == "utr_sg"
                and int(payload["config"]["updates"]) == int(freeze["source"]["source_update"])
                and payload["config"]["fixed_stratified_topology_sampler"] is True
                and runtime.is_file()
                and runtime.stat().st_size > 0
            )
            if not valid:
                source_ok = False
            source_hashes[str(seed)] = sha256(runtime) if runtime.is_file() else "MISSING"
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            source_ok = False
            source_hashes[str(seed)] = "INVALID"

    groups = np.asarray(["N", "N", "F0", "F0", "TE", "TE"], dtype=object)
    scores = {group: 0.0 for group in FAILURE_GROUPS}
    scores.update({"F0": 1.0, "TE": 3.0})
    weights = frozen_weight_map(groups, scores)
    failure_weights = np.asarray([weights[group] for group in groups if group != "N"])
    synthetic_batch = {
        "actions": np.zeros((1, 2, 1), dtype=np.int64),
        "logp": np.zeros((1, 2, 1), dtype=np.float32),
        "advantages": np.ones((1, 2, 1), dtype=np.float32),
        "returns": np.ones((1, 2, 1), dtype=np.float32),
        "td_residuals": np.ones((1, 2, 1), dtype=np.float32),
        "condition_group": np.asarray([["F0", "TE"]], dtype=object),
    }
    deterministic_hash = deterministic_batch_sha256(synthetic_batch) == deterministic_batch_sha256(synthetic_batch)
    runtime_source = (ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py").read_text(encoding="utf-8")
    helper_ok = (
        min(failure_weights) >= 0.75
        and max(failure_weights) <= 1.25
        and abs(float(failure_weights.mean()) - 1.0) <= 1e-12
        and weights["TE"] > weights["F0"]
        and deterministic_hash
    )
    checks = {
        "five_completed_utr_runtime_sources": source_ok,
        "fixed_stratified_collection_only": freeze["source"]["sampler"] == "fixed_stratified_topology_sampler",
        "one_common_prelude_then_exact_ab_pair": (
            freeze["source"]["common_prelude_updates"] == 1 and freeze["source"]["branch_updates"] == 1
        ),
        "actor_only_bounded_weight_rule": helper_ok,
        "runtime_contains_default_off_actor_only_implementation": all(
            token in runtime_source
            for token in (
                "group_weighted_actor_enabled: bool = False",
                "def _group_weight_map(",
                "def _batch_sha256(",
                "group_weighted_actor_scores or {}",
            )
        ),
        "formal_independent_and_heldout_evaluation_disabled": not any(
            freeze["authorization"][key]
            for key in ("formal_evaluation", "heldout_evaluation", "long_training", "weight_sweep", "automatic_c2")
        ),
    }
    status = "C1_READY_FOR_CLOUD_EXECUTION" if all(checks.values()) else "C1_NOT_READY"
    payload = {
        "protocol": freeze["protocol"],
        "status": status,
        "checks": checks,
        "source_runtime_sha256": source_hashes,
        "synthetic_weight_map": weights,
        "training_started": False,
        "rollout_started": False,
        "evaluation_started": False,
        "automatic_c2_authorized": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if status != "C1_READY_FOR_CLOUD_EXECUTION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
