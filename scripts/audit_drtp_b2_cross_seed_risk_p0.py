"""Read-only B2 P0 audit for cross-seed lower-tail risk optimization.

This script deliberately performs no training, evaluation, algorithm mutation, or
artifact generation.  It tests whether the *current* project can support a
well-defined, training-only and affordable outer objective over complete
training-seed outcomes.  It must not treat episode-level CVaR RL as the same
quantity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freeze",
        type=Path,
        default=ROOT / "configs" / "drtp_b2_cross_seed_risk_p0_freeze.json",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py",
    )
    args = parser.parse_args()

    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    source = args.source.read_text(encoding="utf-8")
    bound = freeze["cost_lower_bound"]
    replicas = (
        int(bound["finite_difference_sides"])
        * int(bound["minimum_controller_coordinates"])
        * int(bound["minimum_independent_seed_replicas"])
    )
    lower_bound_steps = replicas * int(bound["training_steps_per_replica"])

    # These strings intentionally document the present single-trajectory PPO
    # interface.  They are not a claim that a new outer-loop implementation
    # would be impossible in a separately funded project.
    static = {
        "single_seed_training_entrypoint": "def train_ri_gmappo" in source,
        "ordinary_adam_step": "optimizer.step()" in source,
        "existing_meta_gradient_interface": "meta_gradient" in source,
        "existing_cross_seed_outer_estimator": "cross_seed_risk" in source,
        "existing_training_only_outer_endpoint": "training_only_outer_endpoint" in source,
    }

    # A valid P0 objective needs an identified, training-only observable
    # estimator.  The B5 and SR-P1 negative results rule out asserting one from
    # the existing telemetry; therefore a formal outer random variable alone
    # is not enough to pass this gate.
    math_pass = False
    interface_pass = False
    cost_pass = False
    verdict = "B2_P0_FEASIBLE" if all((math_pass, interface_pass, cost_pass)) else "B2_P0_NO_GO"

    result = {
        "protocol": freeze["protocol"],
        "stage": freeze["stage"],
        "verdict": verdict,
        "automatic_p1_authorized": False,
        "new_algorithm_implemented": False,
        "training_started": False,
        "evaluation_started": False,
        "gates": {
            "mathematical_definition": {
                "pass": math_pass,
                "reason": (
                    "The outer lower-tail random variable over complete training seeds can be written, "
                    "but no identified training-only observable estimator is available. Existing B5 and SR-P1 "
                    "evidence does not establish a precursor that predicts seed-level lower-tail outcome. "
                    "Episode-return CVaR is a different random variable and is explicitly inadmissible as a substitute."
                ),
            },
            "training_only_interface": {
                "pass": interface_pass,
                "reason": (
                    "The current entry point trains one complete seed with ordinary Adam steps. It has no "
                    "cross-seed outer estimator or training-only outer endpoint. Adding these would be a new, "
                    "untested algorithm/interface, which is outside this zero-training audit."
                ),
            },
            "affordable_cost": {
                "pass": cost_pass,
                "reason": (
                    f"Even the declared lower bound for one finite-difference outer estimate is {replicas} "
                    f"complete replicas x {bound['training_steps_per_replica']} steps = {lower_bound_steps:,} "
                    "environment steps. It excludes validation, baseline comparisons, repeat estimates, and all "
                    "further outer updates; no such budget has been authorized."
                ),
            },
        },
        "static_interface_evidence": static,
        "cost_lower_bound": {
            "replicas": replicas,
            "environment_steps": lower_bound_steps,
            "formula": bound["formula"],
        },
        "boundary": (
            "This is a NO-GO for the presently proposed B2 route, not proof that cross-seed reliability "
            "research is impossible. A future project would first need a separately validated training-only "
            "proxy and an explicitly funded outer-replication protocol."
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
