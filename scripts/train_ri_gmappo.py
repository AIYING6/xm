from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo import RIGMAPPOConfig, train_ri_gmappo


def parse_args() -> RIGMAPPOConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--env-name", choices=("2d_pursuit", "3d_intercept"), default="2d_pursuit")
    parser.add_argument("--num-envs", type=int, default=8)
    parser.add_argument("--rollout-steps", type=int, default=128)
    parser.add_argument("--updates", type=int, default=200)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-encoder", choices=("single", "multi_relation"), default="single")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--entropy-coef", type=float, default=0.01)
    parser.add_argument("--intent-coef", type=float, default=0.1)
    parser.add_argument("--intent-balanced-loss", action="store_true")
    parser.add_argument("--detach-intent", action="store_true")
    parser.add_argument("--oracle-intent", action="store_true")
    parser.add_argument("--eval-interval", type=int, default=10)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--communication-radius", type=float, default=8.0)
    parser.add_argument("--comm-radius-random-min", type=float, default=None)
    parser.add_argument("--comm-radius-random-max", type=float, default=None)
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-range-random-min", type=float, default=None)
    parser.add_argument("--communication-range-random-max", type=float, default=None)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--communication-dropout-random-min", type=float, default=None)
    parser.add_argument("--communication-dropout-random-max", type=float, default=None)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--message-delay-random-min", type=int, default=None)
    parser.add_argument("--message-delay-random-max", type=int, default=None)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--radar-dropout-random-min", type=float, default=None)
    parser.add_argument("--radar-dropout-random-max", type=float, default=None)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-random-prob", type=float, default=0.0)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-start-random-min", type=int, default=None)
    parser.add_argument("--node-failure-start-random-max", type=int, default=None)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--node-failure-duration-random-min", type=int, default=None)
    parser.add_argument("--node-failure-duration-random-max", type=int, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "results" / "ri_gmappo"))
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--resume", type=str, default=None)
    args = parser.parse_args()
    return RIGMAPPOConfig(
        seed=args.seed,
        env_name=args.env_name,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=args.graph_encoder,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        lr=args.lr,
        entropy_coef=args.entropy_coef,
        intent_coef=args.intent_coef,
        intent_balanced_loss=args.intent_balanced_loss,
        detach_intent=args.detach_intent,
        oracle_intent=args.oracle_intent,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        target_policy=args.target_policy,
        target_speed=args.target_speed,
        communication_radius=args.communication_radius,
        comm_radius_random_min=args.comm_radius_random_min,
        comm_radius_random_max=args.comm_radius_random_max,
        communication_range_scale=args.communication_range_scale,
        communication_range_random_min=args.communication_range_random_min,
        communication_range_random_max=args.communication_range_random_max,
        communication_dropout_prob=args.communication_dropout_prob,
        communication_dropout_random_min=args.communication_dropout_random_min,
        communication_dropout_random_max=args.communication_dropout_random_max,
        message_delay_steps=args.message_delay_steps,
        message_delay_random_min=args.message_delay_random_min,
        message_delay_random_max=args.message_delay_random_max,
        radar_dropout_prob=args.radar_dropout_prob,
        radar_dropout_random_min=args.radar_dropout_random_min,
        radar_dropout_random_max=args.radar_dropout_random_max,
        strict_target_sensing=args.strict_target_sensing,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_random_prob=args.node_failure_random_prob,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_start_random_min=args.node_failure_start_random_min,
        node_failure_start_random_max=args.node_failure_start_random_max,
        node_failure_duration_steps=args.node_failure_duration_steps,
        node_failure_duration_random_min=args.node_failure_duration_random_min,
        node_failure_duration_random_max=args.node_failure_duration_random_max,
        device=args.device,
        out_dir=args.out_dir,
        save_interval=args.save_interval,
        resume=args.resume,
    )


def main() -> None:
    cfg = parse_args()
    log_path = train_ri_gmappo(cfg)
    print(f"training log: {log_path}")


if __name__ == "__main__":
    main()
