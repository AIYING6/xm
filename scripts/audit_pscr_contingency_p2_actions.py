"""Read-only macro-intent audit for frozen PSCR P2 endpoints."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_predictive_mappo import PSCRContingencyPredictiveMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts.run_pscr_contingency_predictive import PROTOCOL
from scripts.run_pscr_plain_baseline import deterministic_action


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    rng = np.random.default_rng(20260912)
    rows: list[dict[str, object]] = []
    for arm in ("direct", "robust", "masked"):
        for seed in args.seeds:
            checkpoint = args.root / f"{arm}_seed{seed}" / "endpoint.pt"
            payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
            if payload.get("protocol") != PROTOCOL:
                raise ValueError(f"unexpected checkpoint: {checkpoint}")
            agent = PSCRContingencyPredictiveMAPPO(planning_mode=arm)
            agent.load_state_dict(payload["state_dict"])
            for profile in ("bounded_mixture", "urgent_opposite", "routine_aligned"):
                counts: dict[str, Counter[int]] = {"pre_arrival": Counter(), "post_arrival": Counter()}
                episodes = 8
                for _ in range(episodes):
                    env = PSCRContingencyServiceEnv(PSCRConfig(seed=int(rng.integers(0, 2**31 - 1)), adversary_profile=profile, future_deadline_urgent_step=100))
                    env.reset()
                    while not env.done:
                        action = deterministic_action(agent, env)
                        counts["post_arrival" if env.future_active else "pre_arrival"].update(map(int, action))
                        env.step(action)
                for phase, phase_counts in counts.items():
                    total = sum(phase_counts.values())
                    rows.append({"arm": arm, "training_seed": seed, "profile": profile, "phase": phase, "episodes": episodes, "macro_actions": total, **{f"intent_{intent}_fraction": phase_counts[intent] / total if total else 0.0 for intent in range(5)}})
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P2_MACRO_INTENT_AUDIT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
