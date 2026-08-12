"""Phase 2IA5 E0 eligibility-triggered-failure DEVELOPMENT_ONLY executor.

The executor is deliberately separate from the canonical evaluator.  It loads
only a fixed final development checkpoint, observes a four-step chain hold,
then injects the frozen relay failure on the next timestep.  Invocation is
fail-closed: callers must supply ``--execute`` after the independent executor
audit and launch record are committed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluate_ri_gmappo_3d import (  # noqa: E402
    CSV_COLUMNS,
    append_chain_timestep_trace,
    build_agent,
    build_config,
    build_episode_row,
)
from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402


ARMS = {"full_gate": "relation_conditioned", "no_role_gate": "none"}
SEEDS = (101, 202, 303)
EPISODE_ID_FORMULA = "510000 + 10000 * seed + episode_index"
DEFAULT_TRAINING_ROOT = ROOT / "archival" / "results" / "development" / "role_gate_phase2ia4" / "runs"
DEFAULT_OUT = ROOT / "results" / "development" / "role_gate_phase2ia5_e0"


def episode_id(seed: int, episode_index: int) -> int:
    return 510000 + 10000 * seed + episode_index


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to create an empty raw table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def eligibility_trigger_step(chain_history: list[bool], hold_steps: int = 4) -> int | None:
    """Return the triggering timestep (1-indexed) after a fixed all-true hold."""
    if hold_steps != 4:
        raise ValueError("Phase2IA5 freezes the eligibility hold at four steps")
    if len(chain_history) < hold_steps or not all(chain_history[-hold_steps:]):
        return None
    return len(chain_history)


def base_args(checkpoint: Path, arm: str, seed: int, episodes: int, device: str) -> SimpleNamespace:
    return SimpleNamespace(
        checkpoint=checkpoint, method=arm, episodes=episodes, eval_batch_size=1,
        seed=seed, base_seed=episode_id(seed, 0), episode_id_base=episode_id(seed, 0),
        target_policy="straight", communication_range_scale=1.0,
        communication_dropout_prob=0.30, message_delay_steps=2, radar_dropout_prob=0.0,
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        target_prior_position=(10000.0, 0.0, 5000.0), max_target_message_age_steps=80,
        min_target_confidence=0.20, failed_blue_agent=-1, node_failure_start_step=0,
        node_failure_duration_steps=0, min_success_step=0, attack_hold_steps=4,
        stochastic=False, allow_random_policy=False, hidden_dim=64, role_dim=8,
        intent_dim=8, graph_encoder="multi_relation", graph_relation_ablation="none",
        graph_message_ablation="none", graph_input_ablation="none",
        role_gate_mode=ARMS[arm], multi_relation_global_residual_weight=1.0,
        device=device,
    )


def choose_action(agent, obs, share_obs, graph, device: torch.device) -> np.ndarray:
    from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs

    stacked = stack_graphs([graph])
    actions, _, _, _, _, _, _ = agent.get_action_and_value(
        torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
        torch.as_tensor(stacked["node_feat"], dtype=torch.float32, device=device),
        torch.as_tensor(stacked["edge_feat"], dtype=torch.float32, device=device),
        torch.as_tensor(stacked["role"], dtype=torch.long, device=device),
        torch.as_tensor(stacked["adj"], dtype=torch.float32, device=device),
        torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
        relation_adj=torch.as_tensor(stacked["relation_adj"], dtype=torch.float32, device=device),
        deterministic=True,
        intent_label=torch.as_tensor(stacked["intent_label"], dtype=torch.long, device=device),
        detach_intent=False,
        oracle_intent=False,
    )
    return actions.cpu().numpy()[0]


def run_episode(agent, args: SimpleNamespace, arm: str, seed: int, episode: int, trace_path: Path) -> dict:
    """Run one paired E0 episode and return raw endpoint plus trigger fields."""
    # Failure is disabled at environment creation and is activated only after
    # the frozen observable eligibility predicate becomes true.
    cfg = build_config(args)
    env = make_env(cfg, episode_id(seed, episode), training=False)
    obs, share_obs, graph = env.reset()
    chain_history: list[bool] = []
    step_infos: list[dict] = []
    reward_sum = 0.0
    trigger_step: int | None = None
    failure_start: int | None = None
    eligibility_closed = False
    device = torch.device(args.device)
    while True:
        action = choose_action(agent, obs, share_obs, graph, device)
        obs, share_obs, graph, rewards, dones, info = env.step(action)
        step_infos.append(info)
        reward_sum += float(np.sum(rewards))
        chain_history.append(float(info.get("chain_closed", 0.0)) > 0.5)
        if not eligibility_closed and trigger_step is None:
            candidate = eligibility_trigger_step(chain_history)
            if candidate is not None and candidate <= 220:
                trigger_step = candidate
                failure_start = trigger_step + 1
                env.config.failed_blue_agent = 1
                env.config.node_failure_start_step = failure_start
                env.config.node_failure_duration_steps = 80
            elif len(chain_history) >= 220:
                # The protocol cap is an eligibility boundary, not a delayed
                # fixed-time fault.  Leave the episode fault-free thereafter.
                eligibility_closed = True
        if np.all(dones):
            break

    endpoint_args = SimpleNamespace(**vars(args))
    if failure_start is not None:
        endpoint_args.failed_blue_agent = 1
        endpoint_args.node_failure_start_step = failure_start
        endpoint_args.node_failure_duration_steps = 80
    row = build_episode_row(endpoint_args, "checkpoint", episode_id(seed, episode), episode, step_infos, info, reward_sum)
    row.update({
        "artifact_class": "DEVELOPMENT_ONLY_E0",
        "arm": arm,
        "train_seed": seed,
        "development_episode_id": episode_id(seed, episode),
        "eligibility_hold_steps": 4,
        "eligibility_cap_step": 220,
        "eligible_before_cap": float(trigger_step is not None and trigger_step <= 220),
        "eligibility_trigger_step": -1 if trigger_step is None else trigger_step,
        "actual_failure_start_step": -1 if failure_start is None else failure_start,
        "not_eligible_before_cap": float(trigger_step is None or trigger_step > 220),
    })
    append_chain_timestep_trace(trace_path, row, step_infos, episode_id_base=episode_id(seed, 0), episode_index=episode)
    return row


def execute(args: argparse.Namespace) -> None:
    rows: list[dict] = []
    manifest = {
        "artifact_class": "DEVELOPMENT_ONLY_E0", "protocol": "PHASE2IA5-ETF-V1",
        "episode_id_formula": EPISODE_ID_FORMULA, "episodes_per_arm_seed": args.episodes,
        "eligibility_hold_steps": 4, "eligibility_cap_step": 220,
        "failure": {"agent": 1, "duration_steps": 80, "activation": "trigger_step + 1"},
        "arms": {}, "canonical_data_used": False,
    }
    for arm in args.arms:
        manifest["arms"][arm] = {"role_gate_mode": ARMS[arm], "seeds": {}}
        for seed in args.seeds:
            checkpoint = args.training_root / arm / f"seed{seed}" / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            manifest["arms"][arm]["seeds"][str(seed)] = {"checkpoint": str(checkpoint), "sha256": sha256(checkpoint)}
            local_args = base_args(checkpoint, arm, seed, args.episodes, args.device)
            agent, _ = build_agent(local_args, build_config(local_args))
            trace = args.out_dir / "raw_timestep_chain" / f"{arm}_seed{seed}.csv"
            if trace.exists():
                raise FileExistsError(f"Refusing to overwrite E0 trace: {trace}")
            for episode in range(args.episodes):
                rows.append(run_episode(agent, local_args, arm, seed, episode, trace))
    raw_path = args.out_dir / "raw_validation" / "episode_metrics.csv"
    if raw_path.exists():
        raise FileExistsError(f"Refusing to overwrite E0 raw data: {raw_path}")
    write_csv(raw_path, rows)
    manifest["raw_validation_sha256"] = sha256(raw_path)
    (args.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "episodes": len(rows), "raw_validation_sha256": manifest["raw_validation_sha256"]}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-root", type=Path, default=DEFAULT_TRAINING_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--arms", nargs="+", choices=tuple(ARMS), default=list(ARMS))
    parser.add_argument("--seeds", nargs="+", type=int, choices=SEEDS, default=list(SEEDS))
    parser.add_argument("--execute", action="store_true", help="Required after the separately committed E0 launch record.")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: executor is implemented but E0 requires --execute after the audit and launch record.")
    execute(args)


if __name__ == "__main__":
    main()
