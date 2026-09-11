#!/usr/bin/env python3
"""Execute the frozen A0 development pilot sequentially and reproducibly.

This launcher intentionally performs no adaptive scheduling: all arms, seeds,
budgets and endpoint episodes come from the frozen JSON contract.  It is a
development gate, not a confirmatory experiment.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "a0_oc_method_pilot_v1.json"
RUNNER = ROOT / "scripts" / "run_a0_plain_mappo_pilot.py"
AGGREGATE = ROOT / "scripts" / "aggregate_a0_oc_method_pilot.py"


def invoke(args: list[str]) -> None:
    subprocess.run([sys.executable, *args, "--execute"], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to launch without --execute")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    out = args.output_root
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    (out / "run_contract.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    (out / "evaluation_plan.json").write_text(json.dumps({
        "episodes": config["evaluation_episodes"],
        "endpoint": "post-update fixed endpoint",
        "independent_unit": "training_seed",
        "development_only": True,
    }, indent=2) + "\n", encoding="utf-8")

    for arm in config["training_arms"]:
        for seed in config["training_seeds"]:
            run = out / f"{arm}_seed{seed}"
            invoke([str(RUNNER), "train", "--arm", arm, "--seed", str(seed),
                    "--updates", str(config["updates"]), "--parallel-envs", str(config["parallel_envs"]),
                    "--output-root", str(run)])
            eval_out = run / "eval"
            invoke([str(RUNNER), "evaluate", "--arm", arm, "--seed", str(seed + 10_000),
                    "--episodes", str(config["evaluation_episodes"]), "--checkpoint", str(run / "endpoint.pt"),
                    "--output-root", str(eval_out)])

    # Zero-OC is an implementation equivalence test.  Same seed and zero credit
    # must generate the same endpoint as Plain; it is never reported as an arm.
    seed = config["training_seeds"][0]
    zero = out / f"zero_oc_seed{seed}"
    invoke([str(RUNNER), "train", "--arm", "zero_oc", "--seed", str(seed),
            "--updates", str(config["updates"]), "--parallel-envs", str(config["parallel_envs"]),
            "--output-root", str(zero)])
    import torch
    plain_state = torch.load(out / f"plain_seed{seed}" / "endpoint.pt", map_location="cpu", weights_only=True)["state_dict"]
    zero_state = torch.load(zero / "endpoint.pt", map_location="cpu", weights_only=True)["state_dict"]
    exact = all(torch.equal(plain_state[key], zero_state[key]) for key in plain_state)
    (out / "zero_oc_equivalence.json").write_text(json.dumps({
        "seed": seed, "exact_endpoint_parameter_match": exact,
        "interpretation": "Zero-OC is an implementation consistency check, not a performance comparison.",
    }, indent=2) + "\n", encoding="utf-8")
    if not exact:
        raise RuntimeError("plain and zero-oc endpoints differ")
    invoke([str(AGGREGATE), "--root", str(out)])
    print(json.dumps({"status": "A0_OC_METHOD_PILOT_COMPLETE", "output_root": str(out)}, indent=2))


if __name__ == "__main__":
    main()
