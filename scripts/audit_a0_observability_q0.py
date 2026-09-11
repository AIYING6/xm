"""Zero-training qualification of A0's viewpoint-complementarity premise."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.observability_active_perception import bearing_information, log_determinant, posterior_covariance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to run without --execute")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    target = np.asarray((0.0, 0.0))
    prior = np.diag((9.0, 1.0))
    variance = 0.20
    fixed_uav = np.asarray((-5.0, 0.0))
    starting_uav = np.asarray((-4.0, -3.5))
    # Both legal endpoints lie at exactly the same travel distance from the
    # current UAV position.  The clustered endpoint is closer to the target
    # and therefore wins individual bearing-information scoring; the orthogonal
    # endpoint has less individual information but complements the fixed view.
    clustered = np.asarray((-2.0, 0.0))
    complementary = np.asarray((0.0, -3.0))
    travel_clustered = float(np.linalg.norm(clustered - starting_uav))
    travel_complementary = float(np.linalg.norm(complementary - starting_uav))

    fixed = bearing_information(fixed_uav, target, variance)
    individual_clustered = bearing_information(clustered, target, variance)
    individual_complementary = bearing_information(complementary, target, variance)
    posterior_clustered = posterior_covariance(prior, [fixed, individual_clustered])
    posterior_complementary = posterior_covariance(prior, [fixed, individual_complementary])
    score_clustered = log_determinant(posterior_clustered)
    score_complementary = log_determinant(posterior_complementary)

    payload = {
        "protocol": "A0-OBSERVABILITY-Q0-V1",
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "geometry": {
            "target": target.tolist(),
            "fixed_uav": fixed_uav.tolist(),
            "movable_uav_start": starting_uav.tolist(),
            "clustered_endpoint": clustered.tolist(),
            "complementary_endpoint": complementary.tolist(),
            "travel_distance_clustered": travel_clustered,
            "travel_distance_complementary": travel_complementary,
        },
        "individual_information_trace": {
            "clustered": float(np.trace(individual_clustered)),
            "complementary": float(np.trace(individual_complementary)),
        },
        "joint_posterior_logdet": {
            "clustered": score_clustered,
            "complementary": score_complementary,
        },
        "checks": {
            "equal_travel_cost": bool(np.isclose(travel_clustered, travel_complementary)),
            "individual_myopic_preference_is_clustered": bool(np.trace(individual_clustered) > np.trace(individual_complementary)),
            "joint_observability_preference_is_complementary": bool(score_complementary < score_clustered),
            "posterior_gap_is_material": bool(score_clustered - score_complementary >= 0.5),
        },
        "interpretation": "This Q0 establishes a geometry-induced conflict between individual bearing information and joint posterior uncertainty under equal travel cost. It does not establish a dynamic task, MARL learnability, method superiority, or real-flight validity.",
    }
    payload["verdict"] = "A0_Q0_PASS" if all(payload["checks"].values()) else "A0_Q0_STOP"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
