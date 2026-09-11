"""Run a short, reproducible MAPPO learnability pilot on CrazyRL Escort.

The training loop is imported from the pinned public CrazyRL checkout.  This
script changes only the task factory: CrazyRL's bundled example hard-codes
``Catch``, whereas this pilot uses its moving-target ``Escort`` task.  It is
not a new method comparison and must not be used as paper evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CRAZYRL_ROOT = ROOT / "third_party" / "CrazyRL"
if str(CRAZYRL_ROOT) not in sys.path:
    sys.path.insert(0, str(CRAZYRL_ROOT))
if str(CRAZYRL_ROOT / "learning" / "fulljax") not in sys.path:
    sys.path.insert(0, str(CRAZYRL_ROOT / "learning" / "fulljax"))

import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
import mappo_fulljax as crazyrl_mappo  # noqa: E402
from crazy_rl.multi_agent.jax.escort import Escort  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=97011)
    parser.add_argument("--total-timesteps", type=int, default=32_768)
    parser.add_argument("--num-envs", type=int, default=32)
    parser.add_argument("--num-steps", type=int, default=16)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def escort_factory(
    num_drones: int,
    init_flying_pos: jnp.ndarray,
    init_target_location: jnp.ndarray,
    target_speed: float,
    multi_obj: bool = False,
    size: float = 1.0,
) -> Escort:
    """Adapt CrazyRL's Catch call signature to the built-in Escort task."""
    del target_speed
    return Escort(
        num_drones=num_drones,
        init_flying_pos=init_flying_pos,
        init_target_location=init_target_location,
        final_target_location=jnp.array([0.75, 0.75, 1.25]),
        num_intermediate_points=40,
        multi_obj=multi_obj,
        size=size,
    )


def main() -> None:
    args = parse_args()
    if args.total_timesteps % (args.num_envs * args.num_steps):
        raise ValueError("total-timesteps must be divisible by num-envs × num-steps")
    args.output_dir.mkdir(parents=True, exist_ok=False)

    # Preserve all source MAPPO hyperparameters except the explicitly exposed
    # short-pilot budget and rollout dimensions.
    source_args = argparse.Namespace(
        exp_name="crazyrl_escort_baseline_pilot",
        seed=args.seed,
        debug=False,
        num_envs=args.num_envs,
        num_steps=args.num_steps,
        total_timesteps=args.total_timesteps,
        update_epochs=2,
        num_minibatches=2,
        gamma=0.99,
        lr=1e-3,
        gae_lambda=0.99,
        clip_eps=0.2,
        ent_coef=0.0,
        vf_coef=0.8,
        max_grad_norm=0.5,
        activation="tanh",
        anneal_lr=True,
    )
    crazyrl_mappo.Catch = escort_factory
    started = time.perf_counter()
    train = jax.jit(crazyrl_mappo.make_train(source_args))
    output = jax.block_until_ready(train(jax.random.PRNGKey(args.seed), None))
    elapsed_seconds = time.perf_counter() - started

    metrics = jax.tree_util.tree_map(np.asarray, output["metrics"])
    returns = metrics["returned_episode_returns"]
    lengths = metrics["returned_episode_lengths"]
    nonzero_returns = returns[np.nonzero(returns)]
    nonzero_lengths = lengths[np.nonzero(lengths)]
    summary = {
        "protocol": "CRAZYRL_ESCORT_MAPPO_LEARNABILITY_PILOT_V1",
        "diagnostic_only": True,
        "public_checkout": "third_party/CrazyRL",
        "seed": args.seed,
        "total_timesteps": args.total_timesteps,
        "num_envs": args.num_envs,
        "num_steps": args.num_steps,
        "num_updates": args.total_timesteps // (args.num_envs * args.num_steps),
        "elapsed_seconds": elapsed_seconds,
        "episodes_logged": int(nonzero_returns.size),
        "mean_nonzero_episode_return": float(nonzero_returns.mean()) if nonzero_returns.size else None,
        "last_nonzero_episode_return": float(nonzero_returns[-1]) if nonzero_returns.size else None,
        "mean_nonzero_episode_length": float(nonzero_lengths.mean()) if nonzero_lengths.size else None,
        "jax_platform": jax.devices()[0].platform,
        "return_tensor_shape": list(returns.shape),
        "length_tensor_shape": list(lengths.shape),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (args.output_dir / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["update", "rollout_step", "environment", "agent", "episode_return", "episode_length"])
        for index, value in np.ndenumerate(returns):
            if value != 0:
                # Episode length is shared by all agents in the same parallel
                # environment and therefore has no final agent dimension.
                writer.writerow([*index, float(value), float(lengths[index[:-1]])])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
