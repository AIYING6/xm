"""Run the PSCR phase-release public-plan development pilot."""
from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_phase_release_mappo import PSCRPhaseReleaseMAPPO
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv
from scripts import run_pscr_predictive_mappo as predictive


PROTOCOL = "PSCR-PHASE-RELEASE-PUBLIC-PLAN-P3"


def configure(mode: str) -> None:
    predictive.PSCRPredictiveMAPPO = functools.partial(PSCRPhaseReleaseMAPPO, planning_mode=mode)
    predictive.base.PredictiveServiceChainReconfigurationEnv = PSCRContingencyServiceEnv
    predictive.base.PSCRConfig = functools.partial(PSCRConfig, future_deadline_urgent_step=100)
    predictive.PROTOCOL = PROTOCOL


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("train", "evaluate"))
    parser.add_argument("--planning-mode", choices=("direct", "robust", "masked"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=256)
    parser.add_argument("--parallel-envs", type=int, default=8)
    parser.add_argument("--curriculum", action="store_true")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    configure(args.planning_mode)
    args.output_root.mkdir(parents=True)
    if args.mode == "train":
        predictive.train(args.seed, args.updates, args.parallel_envs, args.output_root, curriculum=args.curriculum)
        return
    if args.checkpoint is None:
        raise ValueError("evaluate requires --checkpoint")
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if payload.get("protocol") != PROTOCOL:
        raise ValueError("unexpected checkpoint protocol")
    agent = PSCRPhaseReleaseMAPPO(planning_mode=args.planning_mode)
    agent.load_state_dict(payload["state_dict"])
    rows, summary = predictive.evaluate(agent, args.seed)
    import csv
    with (args.output_root / "episode_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)
    (args.output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
