# evaluate_mappo_v1_5.py
# Formal MAPPO evaluation entrypoint for v1.5 (③).
# Mirrors evaluate_happo_checkpoint_sweep.py: independent MAPPO load chain,
# same episode/summary/selection schema, same frozen v1_5_wilson selector.
#
# - Loads the MAPPO PPO checkpoint (actor_critic_update_XXXX.pt = full
#   MAPPOAgent3D state dict) with a STRICT load: missing/extra/shape keys fail
#   (the critic must be present and intact in the formal training asset).
# - Update is derived from the file name; --expected-update is an optional
#   consistency guard.
# - Evaluation is deterministic argmax with model.eval(); actor input is
#   local_obs + role one-hot (blue agents only, role_dim=4 frozen).
# - Three output levels: episode CSV, checkpoint-scenario summary CSV, and
#   v1_5_wilson selection CSV (one per train seed).
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_3d_checkpoint_sweep import (  # noqa: E402
    SELECTION_COLUMNS,
    SUMMARY_COLUMNS,
    completed_key,
    display_path,
    failure_exposure_stats,
    mean,
    mean_delayed_recovery,
    mean_delayed_recovery_steps,
    mean_fresh_info_recovery_steps,
    mean_recovery_steps,
    read_existing_csv,
    selection_score,
    select_checkpoints,
    write_csv,
)
from scripts.evaluate_ri_gmappo_3d import (  # noqa: E402
    CSV_COLUMNS,
    build_episode_row,
)
from scripts.evaluate_3d_topology_robustness import SCENARIOS  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    make_env,
)
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPOAgent3D,
    role_onehot,
)

METHOD = "mappo"


@dataclass(frozen=True)
class Candidate:
    train_seed: int
    checkpoint: Path
    update: int


def checkpoint_update(path: Path) -> int:
    match = re.search(r"update_(\d+)", path.name)
    return int(match.group(1)) if match else -99


def discover_candidates(args: argparse.Namespace) -> list[Candidate]:
    candidates: list[Candidate] = []
    allowed_updates = set(args.checkpoint_updates) if args.checkpoint_updates else None
    for seed in args.seeds:
        run_dir = args.mappo_root / args.run_dir_template.format(seed=seed)
        paths = sorted(run_dir.glob(args.checkpoint_glob), key=checkpoint_update)
        if allowed_updates is not None:
            paths = [path for path in paths if checkpoint_update(path) in allowed_updates]
        if not paths:
            message = f"no MAPPO checkpoints matching {args.checkpoint_glob} under {run_dir}"
            if allowed_updates is not None:
                message += f" after filtering updates {sorted(allowed_updates)}"
            if args.allow_missing:
                print(f"skip: {message}", flush=True)
                continue
            raise FileNotFoundError(message)
        for checkpoint in paths:
            candidates.append(Candidate(seed, checkpoint, checkpoint_update(checkpoint)))
    return candidates


def candidates_from_selection(args: argparse.Namespace) -> list[Candidate]:
    if args.selection_csv is None:
        return discover_candidates(args)
    if not args.selection_csv.exists():
        raise FileNotFoundError(args.selection_csv)
    candidates: list[Candidate] = []
    with args.selection_csv.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["graph_encoder"] != METHOD:
                continue
            seed = int(row["train_seed"])
            if seed not in args.seeds:
                continue
            checkpoint = ROOT / row["selected_checkpoint"]
            if not checkpoint.exists():
                if args.allow_missing:
                    print(f"skip missing selected MAPPO checkpoint: {checkpoint}", flush=True)
                    continue
                raise FileNotFoundError(checkpoint)
            candidates.append(Candidate(seed, checkpoint, int(row["selected_checkpoint_update"])))
    return candidates


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def build_config(args: argparse.Namespace) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        eval_episodes=args.episodes,
        target_policy=args.target_policy,
        communication_range_scale=args.communication_range_scale,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
        attack_hold_steps=args.attack_hold_steps,
        min_success_step=args.min_success_step,
        graph_encoder="no_graph",
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        device=args.device,
    )


def load_agent(args: argparse.Namespace, cfg: RIGMAPPOConfig) -> MAPPOAgent3D:
    """STRICT load of the full MAPPO training checkpoint (actor + critic)."""
    checkpoint = Path(args.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    update = checkpoint_update(checkpoint)
    if getattr(args, "expected_update", None) is not None and update != args.expected_update:
        raise RuntimeError(f"checkpoint update {update} != expected {args.expected_update}")
    sd = torch.load(checkpoint, map_location=args.device, weights_only=True)
    if "actor.net.0.weight" not in sd:
        raise RuntimeError(
            f"not a MAPPO PPO checkpoint (missing actor.net.0.weight): {checkpoint} "
            f"- an actor-only BC checkpoint must not be passed to evaluation"
        )
    obs_in = int(sd["actor.net.0.weight"].shape[1])
    action_out = int(sd["actor.net.4.weight"].shape[0])
    hidden = int(sd["actor.net.0.weight"].shape[0])
    role_dim = obs_in - args.env_obs_dim
    env = make_env(cfg, args.seed, training=False)
    agent = MAPPOAgent3D(
        obs_dim=args.env_obs_dim,
        role_dim=role_dim,
        share_obs_dim=env.share_obs_dim,
        action_dim=action_out,
        hidden_dim=hidden,
    )
    # STRICT: missing/extra/shape keys fail (critic must be present and intact)
    agent.load_state_dict(sd)
    for k in sd:
        kl = k.lower()
        for banned in ("graph", "attention", "edge", "role_pair_gate", "task_support", "relation"):
            if banned in kl:
                raise RuntimeError(f"unexpected key {k} in MAPPO checkpoint")
    agent.to(torch.device(args.device))
    agent.eval()
    return agent


def make_eval_args(args: argparse.Namespace, candidate: Candidate, scenario_name: str) -> argparse.Namespace:
    scenario = SCENARIOS[scenario_name]
    return SimpleNamespace(
        checkpoint=candidate.checkpoint,
        episodes=args.episodes,
        eval_batch_size=args.eval_batch_size,
        seed=candidate.train_seed,
        base_seed=args.base_seed,
        target_policy=args.target_policy,
        communication_range_scale=scenario.communication_range_scale,
        communication_dropout_prob=scenario.communication_dropout_prob,
        message_delay_steps=scenario.message_delay_steps,
        radar_dropout_prob=scenario.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.node_failure_start_step,
        node_failure_duration_steps=scenario.node_failure_duration_steps,
        min_success_step=args.min_success_step,
        attack_hold_steps=args.attack_hold_steps,
        stochastic=False,
        allow_random_policy=False,
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        env_obs_dim=args.env_obs_dim,
        expected_update=getattr(args, "expected_update", None),
        device=args.device,
    )


def evaluate(args: argparse.Namespace) -> list[dict[str, object]]:
    """MAPPO deterministic rollout; episode rows carry recovery metrics + the
    exposure fields required by the v1.5 evaluation schema."""
    cfg = build_config(args)
    agent = load_agent(args, cfg)
    device = torch.device(args.device)
    rows: list[dict[str, object]] = []
    failure_step = float(args.node_failure_start_step)
    eval_batch_size = max(1, int(getattr(args, "eval_batch_size", 1)))
    num_agents = None
    with torch.no_grad():
        for batch_start in range(0, args.episodes, eval_batch_size):
            batch_episodes = list(range(batch_start, min(args.episodes, batch_start + eval_batch_size)))
            envs, obs_list, share_obs_list = [], [], []
            step_infos_list: list[list[dict[str, float]]] = []
            reward_sums: list[float] = []
            active: list[bool] = []
            role_list: list[np.ndarray] = []
            for ep in batch_episodes:
                env = make_env(cfg, args.base_seed + ep, training=False)
                obs, share_obs, graph = env.reset()
                num_agents = env.num_agents
                envs.append(env)
                obs_list.append(obs)
                share_obs_list.append(share_obs)
                role_list.append(np.asarray(graph["role"], dtype=np.int64)[: env.num_agents])
                step_infos_list.append([])
                reward_sums.append(0.0)
                active.append(True)

            while any(active):
                active_indices = [i for i, is_active in enumerate(active) if is_active]
                obs_batch = torch.as_tensor(np.stack([obs_list[i] for i in active_indices]), dtype=torch.float32, device=device)
                share_batch = torch.as_tensor(np.stack([share_obs_list[i] for i in active_indices]), dtype=torch.float32, device=device)
                ro_batch = np.stack([role_onehot(role_list[i].reshape(1, -1), agent.role_dim)[0] for i in active_indices])
                ro_t = torch.as_tensor(ro_batch, dtype=torch.float32, device=device)
                n_env = len(active_indices)
                actor_in = torch.cat([obs_batch.reshape(n_env * num_agents, -1), ro_t.reshape(n_env * num_agents, -1)], dim=-1)
                logits = agent.actor(actor_in)
                actions = torch.argmax(logits, dim=-1).reshape(n_env, num_agents).cpu().numpy()
                for action_i, env_i in enumerate(active_indices):
                    obs, share_obs, graph, rewards, dones, info = envs[env_i].step(actions[action_i])
                    reward_sums[env_i] += float(np.sum(rewards))
                    step_infos_list[env_i].append(info)
                    obs_list[env_i] = obs
                    share_obs_list[env_i] = share_obs
                    role_list[env_i] = np.asarray(graph["role"], dtype=np.int64)[: env.num_agents]
                    if np.all(dones):
                        episode = batch_episodes[env_i]
                        row = build_episode_row(
                            args=args, policy_source="checkpoint",
                            seed=args.base_seed + episode, episode=episode,
                            step_infos=step_infos_list[env_i], final=info,
                            reward_sum=reward_sums[env_i],
                        )
                        steps = float(row["steps"])
                        exposed = steps >= failure_step
                        rec = float(row.get("post_failure_chain_recovered", 0.0)) > 0.5
                        rec_steps = float(row.get("post_failure_chain_recovery_steps", -1.0))
                        row["method"] = METHOD
                        row["node_failure_start_step"] = failure_step
                        row["failure_exposed"] = int(exposed)
                        row["recovered_given_exposure"] = int(rec) if exposed else ""
                        row["time_to_recovery_given_exposure"] = rec_steps if (exposed and rec and rec_steps >= 0) else ""
                        row["time_to_success"] = steps if float(row.get("success", 0.0)) > 0.5 else ""
                        row["checkpoint_sha256"] = sha256(Path(args.checkpoint))
                        row["eval_seed"] = args.base_seed + episode
                        row["episode_index"] = episode
                        rows.append(row)
                        active[env_i] = False
    return rows


def summarize_rows(args: argparse.Namespace, candidate: Candidate, scenario_name: str, rows: list[dict[str, object]]) -> dict[str, str]:
    recovery = mean(rows, "post_failure_chain_recovered")
    recovered_after_loss = mean(rows, "post_failure_chain_recovered_after_loss")
    pre_established = mean(rows, "pre_failure_chain_established")
    pre_maintained = mean(rows, "pre_failure_chain_maintained")
    pre_recovered_after_loss = mean(rows, "pre_failure_chain_recovered_after_loss")
    first_established = mean(rows, "post_failure_chain_first_established")
    never_established = mean(rows, "post_failure_chain_never_established")
    fresh_info_recovered = mean(rows, "post_failure_fresh_info_recovered")
    fresh_without_prior_loss = mean(rows, "post_failure_fresh_info_acquired_without_prior_loss")
    fresh_first_established = mean(rows, "post_failure_fresh_info_first_established")
    fresh_direct_recovered = mean(rows, "post_failure_fresh_direct_recovered")
    fresh_comm_recovered = mean(rows, "post_failure_fresh_comm_recovered")
    post_delivered_old_recovered = mean(rows, "post_failure_post_delivered_old_info_recovered")
    stale_cache_recovered = mean(rows, "post_failure_stale_cache_recovered")
    delayed = mean_delayed_recovery(rows, args.delayed_recovery_min_step)
    recovery_steps = mean_recovery_steps(rows)
    fresh_info_steps = mean_fresh_info_recovery_steps(rows)
    delayed_steps = mean_delayed_recovery_steps(rows, args.delayed_recovery_min_step)
    success = mean(rows, "success")
    collision = mean(rows, "collision")
    if args.selection_metric == "fresh_info_recovery":
        score_recovery, score_steps = fresh_info_recovered, fresh_info_steps
    elif args.selection_metric == "delayed_recovery":
        score_recovery, score_steps = delayed, delayed_steps
    else:
        score_recovery, score_steps = recovery, recovery_steps
    score = selection_score(score_recovery, score_steps, success, collision, args.max_selection_collision_rate, args.selection_success_weight)
    return {
        "split": args.split, "scenario": scenario_name, "graph_encoder": METHOD,
        "graph_relation_ablation": "none", "graph_message_ablation": "none", "graph_input_ablation": "none",
        "train_seed": str(candidate.train_seed), "checkpoint_update": str(candidate.update),
        "checkpoint": display_path(candidate.checkpoint),
        "strict_target_sensing": str(args.strict_target_sensing),
        "agent_target_info_bottleneck": str(args.agent_target_info_bottleneck),
        "target_prior_position": ";".join(f"{float(x):.6g}" for x in args.target_prior_position),
        "max_target_message_age_steps": str(args.max_target_message_age_steps),
        "min_target_confidence": f"{args.min_target_confidence:.6g}",
        "episodes": str(args.episodes),
        "success_mean": f"{success:.6g}",
        "post_failure_chain_recovered_mean": f"{recovery:.6g}",
        "post_failure_chain_recovered_after_loss_mean": f"{recovered_after_loss:.6g}",
        "pre_failure_chain_established_mean": f"{pre_established:.6g}",
        "pre_failure_chain_maintained_mean": f"{pre_maintained:.6g}",
        "pre_failure_chain_recovered_after_loss_mean": f"{pre_recovered_after_loss:.6g}",
        "post_failure_chain_first_established_mean": f"{first_established:.6g}",
        "post_failure_chain_never_established_mean": f"{never_established:.6g}",
        "post_failure_fresh_info_recovered_mean": f"{fresh_info_recovered:.6g}",
        "post_failure_fresh_info_acquired_without_prior_loss_mean": f"{fresh_without_prior_loss:.6g}",
        "post_failure_fresh_info_first_established_mean": f"{fresh_first_established:.6g}",
        "post_failure_fresh_direct_recovered_mean": f"{fresh_direct_recovered:.6g}",
        "post_failure_fresh_comm_recovered_mean": f"{fresh_comm_recovered:.6g}",
        "post_failure_post_delivered_old_info_recovered_mean": f"{post_delivered_old_recovered:.6g}",
        "post_failure_stale_cache_recovered_mean": f"{stale_cache_recovered:.6g}",
        "delayed_recovery_min_step": str(args.delayed_recovery_min_step),
        "delayed_recovery_mean": f"{delayed:.6g}",
        "post_failure_chain_recovery_steps_mean": "inf" if not np.isfinite(recovery_steps) else f"{recovery_steps:.6g}",
        "post_failure_fresh_info_recovery_steps_mean": "inf" if not np.isfinite(fresh_info_steps) else f"{fresh_info_steps:.6g}",
        "delayed_recovery_steps_mean": "inf" if not np.isfinite(delayed_steps) else f"{delayed_steps:.6g}",
        "chain_closed_during_failure_rate_mean": f"{mean(rows, 'chain_closed_during_failure_rate'):.6g}",
        "tracking_during_failure_rate_mean": f"{mean(rows, 'tracking_during_failure_rate'):.6g}",
        "connectivity_during_failure_mean": f"{mean(rows, 'connectivity_during_failure'):.6g}",
        "episode_min_blue_red_distance_mean": f"{mean(rows, 'episode_min_blue_red_distance'):.6g}",
        "episode_min_blue_blue_distance_mean": f"{mean(rows, 'episode_min_blue_blue_distance'):.6g}",
        "steps_mean": f"{mean(rows, 'steps'):.6g}",
        "timeout_mean": f"{mean(rows, 'timeout'):.6g}",
        "collision_mean": f"{collision:.6g}",
        "constraint_violation_mean": f"{mean(rows, 'constraint_violation'):.6g}",
        "selection_score": f"{score:.6g}",
        "selection_metric": args.selection_metric,
        "selection_success_weight": f"{args.selection_success_weight:.6g}",
        "selection_policy": args.selection_policy,
        **failure_exposure_stats(rows, float(SCENARIOS[scenario_name].node_failure_start_step)),
    }


def write_report(path: Path, args: argparse.Namespace, summary_rows: list[dict[str, str]], selected_rows: list[dict[str, str]]) -> None:
    lines = [
        "# 3DOF MAPPO Checkpoint Sweep (v1.5)",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "```text",
        f"split = {args.split}",
        f"seeds = {list(args.seeds)}",
        f"scenarios = {list(args.scenarios)}",
        f"episodes = {args.episodes}",
        f"base_seed = {args.base_seed}",
        f"selection_policy = {args.selection_policy}",
        "```",
        "",
        "| Seed | Update | Recovery | Success | Wilson | Checkpoint |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in selected_rows:
        lines.append(
            f"| {row['train_seed']} | {row['selected_checkpoint_update']} | "
            f"{row['recovery_given_exposure']} | {row['success_mean']} | "
            f"{row['wilson_lower_95']} | `{row['selected_checkpoint']}` |"
        )
    lines.extend(["", "## Boundary", "", "- MAPPO uses the same validation/test selection schema as the paper methods.",
                  "- Test split should use validation-selected checkpoints through `--selection-csv`.",
                  "", f"Evaluated checkpoint-scenario combinations: {len(summary_rows)}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate MAPPO checkpoint snapshots on fixed matched episodes (v1.5).")
    parser.add_argument("--split", choices=("validation", "test"), default="validation")
    parser.add_argument("--seeds", nargs="+", type=int, default=(0,))
    parser.add_argument("--scenarios", nargs="+", choices=tuple(SCENARIOS), default=("relay_failure",))
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--base-seed", type=int, default=120_000)
    parser.add_argument("--env-obs-dim", type=int, default=34)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--strict-target-sensing", action="store_true", default=True)
    parser.add_argument("--no-strict-target-sensing", dest="strict_target_sensing", action="store_false")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--min-success-step", type=int, default=0)
    parser.add_argument("--attack-hold-steps", type=int, default=4)
    parser.add_argument("--mappo-root", type=Path, default=ROOT / "results" / "mappo_3d")
    parser.add_argument("--run-dir-template", type=str, default="ppo_seed{seed}_1m")
    parser.add_argument("--checkpoint-glob", type=str, default="actor_critic_update_*.pt")
    parser.add_argument("--checkpoint-updates", nargs="*", type=int, default=None)
    parser.add_argument("--selection-csv", type=Path, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "mappo_checkpoint_sweep")
    parser.add_argument("--allow-missing", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--expected-update", type=int, default=None)
    parser.add_argument("--selection-group", choices=("scenario", "suite"), default="suite")
    parser.add_argument("--selection-metric", choices=("legacy_recovery", "delayed_recovery", "fresh_info_recovery"), default="legacy_recovery")
    parser.add_argument("--selection-policy", choices=("v1_4_score", "v1_5_wilson"), default="v1_4_score")
    parser.add_argument("--delayed-recovery-min-step", type=int, default=80)
    parser.add_argument("--max-selection-collision-rate", type=float, default=None)
    parser.add_argument("--selection-success-weight", type=float, default=100.0)
    return parser.parse_args()


# episode CSV columns = common sweep prefix + the shared episode schema + the
# MAPPO exposure fields (deduplicated; CSV_COLUMNS already carries the full
# build_episode_row fields, including method/checkpoint/...).
EPISODE_FIELDS = list(
    dict.fromkeys(
        ("split", "scenario", "graph_encoder", "train_seed", "checkpoint_update")
        + CSV_COLUMNS
        + ("node_failure_start_step", "failure_exposed", "recovered_given_exposure",
           "time_to_recovery_given_exposure", "time_to_success", "checkpoint_sha256",
           "eval_seed", "episode_index")
    )
)


def main() -> None:
    args = parse_args()
    candidates = candidates_from_selection(args)
    episode_path = args.out_dir / f"{args.split}_episode_metrics.csv"
    summary_path = args.out_dir / f"{args.split}_checkpoint_summary.csv"
    selection_path = args.out_dir / f"{args.split}_selected_checkpoints.csv"
    report_path = args.out_dir / f"{args.split}_checkpoint_sweep.md"
    episode_rows = read_existing_csv(episode_path) if args.resume else []
    summary_rows = read_existing_csv(summary_path) if args.resume else []
    completed = {completed_key(row) for row in summary_rows}

    for candidate in candidates:
        for scenario_name in args.scenarios:
            key = (args.split, scenario_name, METHOD, "none", "none", "none", str(candidate.train_seed), str(candidate.update))
            if key in completed:
                print(f"skip completed {args.split} {scenario_name} {METHOD} seed={candidate.train_seed} update={candidate.update}", flush=True)
                continue
            print(f"eval {args.split} {scenario_name} {METHOD} seed={candidate.train_seed} update={candidate.update}", flush=True)
            ea = make_eval_args(args, candidate, scenario_name)
            rows = evaluate(ea)
            for row in rows:
                row.update({"split": args.split, "scenario": scenario_name, "graph_encoder": METHOD,
                            "train_seed": candidate.train_seed, "checkpoint_update": candidate.update})
            episode_rows.extend(rows)
            summary_rows.append(summarize_rows(args, candidate, scenario_name, rows))
            completed.add(key)
            write_csv(episode_path, episode_rows, EPISODE_FIELDS)
            write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)

    selected_rows = select_checkpoints(args, summary_rows)
    write_csv(episode_path, episode_rows, EPISODE_FIELDS)
    write_csv(summary_path, summary_rows, SUMMARY_COLUMNS)
    write_csv(selection_path, selected_rows, SELECTION_COLUMNS)
    write_report(report_path, args, summary_rows, selected_rows)
    print(summary_path)
    print(selection_path)
    print(report_path)


if __name__ == "__main__":
    main()
