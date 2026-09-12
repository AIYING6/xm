"""Read-only P4 G0 macro-action audit for the fixed endpoint checkpoints."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_contingency_mappo import PSCRContingencyMAPPO
from scripts.run_pscr_p4_reliability_endpoint import RELIABILITY_BANDS, p4_config
from scripts.run_pscr_plain_baseline import deterministic_action
from envs.pscr_contingency_service_env import PSCRContingencyServiceEnv


INTENT_NAMES = ("primary_service", "forecast_stage", "future_service", "safe_hold", "contingency_stage")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--agent-kind", choices=("plain", "rc"), default="plain")
    parser.add_argument("--arm", choices=("full", "phase_control", "permuted_reliability"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=24)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if args.agent_kind == "plain":
        agent = PSCRContingencyMAPPO()
    else:
        from algorithms.pscr_reliability_commitment_mappo import PSCRReliabilityCommitmentMAPPO
        if args.arm is None:
            raise ValueError("--arm is required for --agent-kind rc")
        if payload.get("arm") != args.arm:
            raise ValueError("checkpoint arm does not match --arm")
        agent = PSCRReliabilityCommitmentMAPPO(mode=args.arm)
    agent.load_state_dict(payload["state_dict"])
    rng = np.random.default_rng(args.seed + 91_000)
    rows: list[dict[str, object]] = []
    for reliability in RELIABILITY_BANDS:
        counter: Counter[tuple[str, int]] = Counter()
        total: Counter[str] = Counter()
        for _ in range(args.episodes):
            env = PSCRContingencyServiceEnv(p4_config(int(rng.integers(0, 2**31 - 1)), reliability))
            env.reset()
            while not env.done:
                phase = "post_arrival" if env.future_active else "pre_arrival"
                action = deterministic_action(agent, env)
                for intent in action:
                    counter[(phase, int(intent))] += 1
                    total[phase] += 1
                env.step(action)
        for phase in ("pre_arrival", "post_arrival"):
            for intent, name in enumerate(INTENT_NAMES):
                rows.append({
                    "training_seed": args.seed,
                    "reliability_band": f"r{reliability:.2f}",
                    "phase": phase,
                    "intent": name,
                    "action_count": counter[(phase, intent)],
                    "phase_action_total": total[phase],
                    "action_fraction": counter[(phase, intent)] / total[phase] if total[phase] else 0.0,
                })
    args.output_root.mkdir(parents=True)
    with (args.output_root / "action_fractions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {
        "protocol": "PSCR-P4-G0-ENDPOINT-ACTION-AUDIT-V1",
        "training_seed": args.seed,
        "read_only": True,
        "interpretation_boundary": "Intent fractions describe the deterministic endpoint behaviour; they do not establish why a policy selected an action.",
    }
    (args.output_root / "action_audit_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
