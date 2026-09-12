"""Read-only action audit for fixed P8 plain-MAPPO endpoints.

The audit reports what a trained policy does at the public commitment window
and after future-request activation.  It neither trains nor alters endpoints.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_p8_plain_mappo import PSCRP8PlainMAPPO
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE
from scripts.run_pscr_p8_plain_baseline import PROTOCOL, deterministic_action


SEEDS = (97111, 97112, 97113)
RELIABILITIES = (0.1, 0.9)


def load(path: Path) -> PSCRP8PlainMAPPO:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError(f"unexpected checkpoint protocol: {path}")
    agent = PSCRP8PlainMAPPO(); agent.load_state_dict(payload["state_dict"]); agent.eval()
    return agent


def episode(agent: PSCRP8PlainMAPPO, seed: int, reliability: float) -> dict[str, float | int]:
    env = PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=seed, forecast_reliability_choices=(reliability,)))
    env.reset()
    commitment: np.ndarray | None = None
    future_actions = future_total = 0
    while not env.done:
        action = deterministic_action(agent, env)
        if env._commitment_active() and commitment is None:
            commitment = action.copy()
        if env.future_active:
            future_actions += int(np.sum(action == FUTURE_SERVICE))
            future_total += env.num_agents
        env.step(action)
    if commitment is None:
        raise RuntimeError("P8 episode ended before the commitment window")
    result = env.terminal_summary()
    return {
        "commit_full_stage": float(commitment[env.scout] == FORECAST_STAGE and commitment[env.relay] == FORECAST_STAGE and commitment[env.executor] == PRIMARY_SERVICE),
        "commit_all_primary": float(np.all(commitment == PRIMARY_SERVICE)),
        "commit_scout_forecast": float(commitment[env.scout] == FORECAST_STAGE),
        "commit_relay_forecast": float(commitment[env.relay] == FORECAST_STAGE),
        "commit_executor_primary": float(commitment[env.executor] == PRIMARY_SERVICE),
        "postarrival_future_intent_fraction": future_actions / future_total if future_total else 0.0,
        "weighted_service_value": float(result["weighted_service_value"]),
        "future_completed": float(result["future_completed"]),
        "future_localized": float(result["future_localized"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trained-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    rows: list[dict[str, float | int]] = []
    for training_seed in SEEDS:
        agent = load(args.trained_root / "runs" / "plain_mappo" / f"seed{training_seed}" / "endpoint.pt")
        for reliability in RELIABILITIES:
            for episode_index in range(args.episodes):
                row: dict[str, float | int] = {"training_seed": training_seed, "reliability": reliability, "episode": episode_index}
                row.update(episode(agent, 990_000 + training_seed * 100 + episode_index, reliability))
                rows.append(row)
    fields = list(rows[0])
    args.output_root.mkdir(parents=True)
    with (args.output_root / "P8_PLAIN_POLICY_BEHAVIOR_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    summary: dict[str, float | int | str] = {"protocol": "PSCR-P8-PLAIN-POLICY-BEHAVIOR-AUDIT-V1", "diagnostic_only": True, "episodes_per_seed_band": args.episodes}
    for reliability in RELIABILITIES:
        subset = [row for row in rows if float(row["reliability"]) == reliability]
        for field in fields[3:]:
            summary[f"r{reliability}_{field}"] = float(np.mean([float(row[field]) for row in subset]))
    summary["boundary"] = "Behavior frequencies describe fixed plain-MAPPO endpoints. They do not establish that any particular action causes performance or that a new method is effective."
    (args.output_root / "P8_PLAIN_POLICY_BEHAVIOR_REPORT.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
